"""Session isolation, CSRF, bounded input and demo-only safeguards."""
import json,re,secrets,time
from datetime import date,datetime,timedelta
from urllib.parse import parse_qsl,urlsplit
from fastapi import Request,HTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse,RedirectResponse,Response
from sqlalchemy import text
from app.config import settings
from app.database import workspace,make_engine,Base

DEMO_REPLIES=("Demostración: confirmación administrativa de horario.","Demostración: recibimos tu solicitud; una persona dará seguimiento.","Demostración: puedes revisar los horarios disponibles.")
DEMO_NOTES=("","Demostración administrativa","Demostración: cambio de horario")


def safe_origin(value,default=""):
    try:
        p=urlsplit(value)
        if p.scheme in ("http","https") and p.hostname and not p.username and not p.password and not p.path.strip('/') and not p.query and not p.fragment and not any(c.isspace() for c in value):return value.rstrip('/')
    except ValueError:pass
    return default


def seed_demo(path):
    from app.models import Patient,Appointment,ConversationState,MessageLog
    from app.scheduler import get_or_create_settings,get_slots_for_date
    from app.human_mode import mark_human_request
    from app.time_utils import local_today
    from sqlalchemy.orm import Session
    engine=make_engine("sqlite:///"+str(path))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        cfg=get_or_create_settings(db);cfg.human_auto_resume_minutes=0
        for i in range(1,4):db.add(Patient(phone=f"000000{i:02d}",name=f"Paciente Demo {i:02d}"))
        db.commit()
        future=local_today()+timedelta(days=1)
        for _ in range(7):
            slots=get_slots_for_date(db,future)
            if slots:break
            future+=timedelta(days=1)
        if slots:
            start=slots[0]
            end=(datetime.combine(future,start)+timedelta(minutes=30)).time()
            db.add(Appointment(patient_id=1,date=future,start_time=start,end_time=end,appointment_type="consulta",duration_minutes=30,reason="Demostración administrativa",status="confirmada"))
        state=ConversationState(phone="00000002",step="START",data="{}")
        mark_human_request(db,state);db.add(state)
        db.add(MessageLog(phone="00000002",direction="incoming",text="Demostración: quiero hablar con una persona.",message_type="text",source="demo",is_read=False))
        db.commit()
    engine.dispose()


def cleanup_demo():
    root=settings.RUNTIME_DIR/'sessions';root.mkdir(mode=0o700,parents=True,exist_ok=True)
    for path in root.glob('*.sqlite3'):
        if re.fullmatch('[a-f0-9]{32}',path.stem):
            try:
                if time.time()-path.stat().st_mtime>settings.DEMO_TTL:path.unlink()
            except FileNotFoundError:pass
    return root


def validate_form(path,form):
    for key,value in form.items():
        if len(value)>1000 or any(ord(c)<32 and c not in '\n\r' for c in value):raise ValueError("Campo demasiado largo o inválido")
    for key in ('day','new_date'):
        if form.get(key):
            target=date.fromisoformat(form[key])
            if not date.today()-timedelta(days=1)<=target<=date.today()+timedelta(days=settings.MAX_BOOKING_DAYS_AHEAD):raise ValueError("Fecha fuera del intervalo permitido")
    for key in ('work_start','work_end','custom_start','custom_end','start_time','new_start_time'):
        if form.get(key) and not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',form[key]):raise ValueError("Hora inválida")
    for a,b in (('work_start','work_end'),('custom_start','custom_end')):
        if form.get(a) and form.get(b) and form[a]>=form[b]:raise ValueError("El fin debe ser posterior al inicio")
    if 'consult_minutes' in form and (not form['consult_minutes'].isdigit() or not 5<=int(form['consult_minutes'])<=120):raise ValueError("Duración: entre 5 y 120 minutos")
    if 'human_auto_resume_minutes' in form and (not form['human_auto_resume_minutes'].isdigit() or not 0<=int(form['human_auto_resume_minutes'])<=240):raise ValueError("Temporizador inválido")
    if 'work_days' in form and not re.fullmatch('[0-6](?:,[0-6])*',form['work_days']):raise ValueError("Días inválidos")
    if form.get('patient_age') and (not form['patient_age'].isdigit() or not 1<=int(form['patient_age'])<=119):raise ValueError("Edad inválida")
    if form.get('patient_name') is not None and not 1<=len(form['patient_name'].strip())<=120:raise ValueError("Nombre inválido")
    for key in ('patient_phone','phone','alert_contact_phone'):
        if form.get(key) and not re.fullmatch('[0-9]{8,15}',form[key]):raise ValueError("Identificador de contacto inválido")
    if settings.DEMO_MODE:
        if form.get('patient_name') and not re.fullmatch('Paciente Demo [0-9]{2}',form['patient_name']):raise ValueError("Usa únicamente un alias Paciente Demo 01–99")
        for key in ('patient_phone','phone'):
            if form.get(key) and not re.fullmatch('000000[0-9]{2}',form[key]):raise ValueError("Usa solo identificadores demo 00000001–00000099")
        if form.get('patient_age'):raise ValueError("La demo no admite edades")
        if form.get('body') and form['body'] not in DEMO_REPLIES:raise ValueError("Elige una respuesta demostrativa de la lista")
        for key in ('reason','note','alert_contact_name'):
            if form.get(key) and form[key] not in DEMO_NOTES:raise ValueError("Usa únicamente notas administrativas demo")
        if form.get('alert_contact_phone') or 'alert_whatsapp_enabled' in form or 'notify_patient' in form:raise ValueError("Las comunicaciones externas están desactivadas")
        if form.get('human_auto_resume_minutes','0')!='0':raise ValueError("La demo conserva el handoff hasta reanudación explícita")


class BodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        limit=32768 if scope.get('path')=='/webhook' else 16384
        length=dict(scope.get('headers',[])).get(b'content-length',b'0')
        if length.isdigit() and int(length)>limit:return await JSONResponse({'detail':'Solicitud demasiado grande'},status_code=413)(scope,receive,send)
        chunks=[];size=0
        while True:
            event=await receive()
            if event['type']=='http.disconnect':return
            part=event.get('body',b'');size+=len(part)
            if size>limit:return await JSONResponse({'detail':'Solicitud demasiado grande'},status_code=413)(scope,receive,send)
            chunks.append(part)
            if not event.get('more_body',False):break
        used=False
        async def replay():
            nonlocal used
            if not used:
                used=True;return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)


def install_security(app):
    @app.middleware('http')
    async def guards(request,call_next):
        token=None
        try:
            private=request.url.path.startswith('/panel')
            if len(request.url.query)>2048:return JSONResponse({'detail':'Consulta demasiado larga'},status_code=414)
            patient_id=request.query_params.get('patient_id')
            if patient_id is not None and (not patient_id.isdigit() or len(patient_id)>10 or not 1<=int(patient_id)<=2147483647):return JSONResponse({'detail':'Identificador inválido'},status_code=422)
            if request.url.path=='/webhook' and (settings.DEMO_MODE or not settings.INTEGRATIONS_ENABLED):return JSONResponse({'detail':'Integración desactivada'},status_code=404)
            if settings.DEMO_MODE and (request.url.path=='/panel/agenda/send' or request.url.path.startswith('/panel/media/')):return JSONResponse({'detail':'Función externa desactivada en demo'},status_code=404)
            if 'csrf' not in request.session and request.url.path!='/health' and not request.url.path.startswith('/static/'):request.session['csrf']=secrets.token_urlsafe(32)
            if private:
                if settings.DEMO_MODE:
                    root=cleanup_demo();sid=request.session.get('workspace','')
                    path=root/(sid+'.sqlite3') if re.fullmatch('[a-f0-9]{32}',sid) else None
                    if request.session.get('role') not in ('doctor','assistant') or not path or not path.is_file() or time.time()-request.session.get('started',0)>=settings.DEMO_TTL:
                        request.session.clear()
                        return RedirectResponse('/demo',status_code=303) if request.method=='GET' else JSONResponse({'detail':'Entorno vencido. Abre de nuevo la demo.'},status_code=401)
                    token=workspace.set(path)
                elif not request.headers.get('authorization','').startswith('Basic '):return JSONResponse({'detail':'Autenticación requerida'},status_code=401,headers={'WWW-Authenticate':'Basic'})
            if request.method in ('POST','PUT','PATCH','DELETE') and request.url.path!='/webhook':
                limit=16384
                if request.headers.get('content-length','0').isdigit() and int(request.headers.get('content-length','0'))>limit:return JSONResponse({'detail':'Solicitud demasiado grande'},status_code=413)
                body=await request.body()
                if len(body)>limit:return JSONResponse({'detail':'Solicitud demasiado grande'},status_code=413)
                if not body and not request.headers.get('x-csrf-token'):return JSONResponse({'detail':'Formulario no válido'},status_code=400)
                content_type=request.headers.get('content-type','').split(';')[0]
                form={}
                if content_type=='application/x-www-form-urlencoded':
                    pairs=parse_qsl(body.decode('utf8'),keep_blank_values=True,max_num_fields=50)
                    if any(sum(1 for a,b in pairs if a==key)>1 for key,value in pairs if key!='work_days_check'):return JSONResponse({'detail':'Campos repetidos no permitidos'},status_code=400)
                    form=dict(pairs)
                elif content_type=='application/json':
                    payload=json.loads(body)
                    if request.url.path!='/panel/layout' or not isinstance(payload,dict) or set(payload)!={'order'}:return JSONResponse({'detail':'Formato inválido'},status_code=400)
                else:return JSONResponse({'detail':'Formato de formulario no admitido'},status_code=415)
                supplied=form.get('csrf_token') or request.headers.get('x-csrf-token','')
                if not supplied or not secrets.compare_digest(supplied,request.session.get('csrf','')):return JSONResponse({'detail':'Formulario no válido. Recarga la página.'},status_code=400)
                validate_form(request.url.path,form)
                if private and settings.DEMO_MODE:
                    from app.database import SessionLocal
                    from app.models import Patient,Appointment,MessageLog,AuditLog
                    with SessionLocal() as db:
                        if any(db.query(model).count()>=settings.MAX_RECORDS for model in (Patient,Appointment,MessageLog,AuditLog)):return JSONResponse({'detail':'Límite de la demo. Reinicia tu entorno.'},status_code=429)
            response=await call_next(request)
        except (ValueError,UnicodeDecodeError):response=JSONResponse({'detail':'Revisa fechas, horarios y campos. Usa solo datos demo.'},status_code=422)
        except OSError:response=JSONResponse({'detail':'Almacenamiento temporal no disponible'},status_code=503)
        finally:
            if token is not None:workspace.reset(token)
        return response

    app.add_middleware(BodyLimit)
    app.add_middleware(SessionMiddleware,secret_key=settings.SECRET_KEY,session_cookie='esculapio_session',same_site='lax',https_only=bool(__import__('os').getenv('RAILWAY_ENVIRONMENT_ID')) or __import__('os').getenv('SITE_URL','').startswith('https://'),max_age=1800)

    # Outermost headers include middleware rejections and error responses.
    @app.middleware('http')
    async def secure_headers(request,call_next):
        response=await call_next(request)
        response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Permissions-Policy':'camera=(), microphone=(), geolocation=()','Content-Security-Policy':"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"})
        if request.url.path.startswith(('/panel','/demo','/health')) or response.status_code>=400:
            response.headers['Cache-Control']='no-store';response.headers['X-Robots-Tag']='noindex, nofollow'
        return response
