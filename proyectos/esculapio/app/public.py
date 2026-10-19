from xml.etree import ElementTree as ET
import os,re,secrets,time,tempfile,sqlite3
from pathlib import Path
from fastapi import Request,Form,Depends,HTTPException
from fastapi.responses import RedirectResponse,JSONResponse,Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError,OperationalError
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.security import cleanup_demo,seed_demo,safe_origin


PUBLIC_DESCRIPTIONS = {'/': 'Conoce ESCULAPIO: operación administrativa de consultorio con agenda, mensajes y atención humana. Demo independiente con datos ficticios.', '/features': 'Explora las funciones administrativas de ESCULAPIO: agenda, pacientes demo, mensajes, permisos por rol y transferencia a atención humana.', '/case-study': 'Conoce la web publicada del Dr. Jonathan y la demo administrativa independiente de ESCULAPIO: contexto, solución, arquitectura y alcance verificado.', '/architecture': 'Conoce la arquitectura y los límites de ESCULAPIO: FastAPI, SQLAlchemy, bases temporales por sesión e integraciones externas desactivadas.'}

def install_public(app,templates):
    @app.get('/sitemap.xml')
    def sitemap(request:Request):
        origin=safe_origin(os.getenv('SITE_URL','')) or str(request.base_url).rstrip('/')
        root=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for path in PUBLIC_DESCRIPTIONS:
            ET.SubElement(ET.SubElement(root,'url'),'loc').text=origin+path
        return Response(ET.tostring(root,encoding='utf-8',xml_declaration=True),media_type='application/xml')

    @app.get('/robots.txt')
    def robots(request:Request):
        origin=safe_origin(os.getenv('SITE_URL','')) or str(request.base_url).rstrip('/')
        return Response('User-agent: *\nAllow: /\nDisallow: /health\nSitemap: '+origin+'/sitemap.xml\n',media_type='text/plain')

    @app.get('/case-study')
    def case_study(request:Request):return templates.TemplateResponse('case_study.html',{'request':request})

    @app.get('/features')
    def features(request:Request):return templates.TemplateResponse('features.html',{'request':request})

    @app.get('/architecture')
    def architecture(request:Request):return templates.TemplateResponse('architecture.html',{'request':request})

    @app.get('/demo')
    def demo(request:Request):
        if not settings.DEMO_MODE:raise HTTPException(404)
        return templates.TemplateResponse('demo.html',{'request':request})

    @app.post('/demo/start')
    def demo_start(request:Request,role:str=Form(...)):
        if not settings.DEMO_MODE:raise HTTPException(404)
        if role not in ('doctor','assistant'):raise HTTPException(422,'Rol demo inválido')
        root=cleanup_demo()
        if len(list(root.glob('*.sqlite3')))>=settings.MAX_SPACES:raise HTTPException(503,'Demo ocupada')
        sid=secrets.token_hex(16);path=root/(sid+'.sqlite3')
        try:seed_demo(path)
        except Exception:
            path.unlink(missing_ok=True);raise
        old=request.session.get('workspace','')
        if re.fullmatch('[a-f0-9]{32}',old):(root/(old+'.sqlite3')).unlink(missing_ok=True)
        request.session.clear();request.session.update(workspace=sid,started=time.time(),role=role,csrf=secrets.token_urlsafe(32))
        return RedirectResponse('/panel',status_code=303)

    @app.post('/demo/reset')
    def demo_reset(request:Request):
        if not settings.DEMO_MODE:raise HTTPException(404)
        sid=request.session.get('workspace','')
        if re.fullmatch('[a-f0-9]{32}',sid):(settings.RUNTIME_DIR/'sessions'/(sid+'.sqlite3')).unlink(missing_ok=True)
        request.session.clear()
        return RedirectResponse('/demo',status_code=303)

    @app.post('/panel/demo-incoming')
    async def demo_incoming(request:Request,phone:str=Form(...),event:str=Form(...),db:Session=Depends(get_db)):
        if not settings.DEMO_MODE:raise HTTPException(404)
        from app.main import check_admin
        check_admin(request,None)
        from app.models import Patient,ConversationState,MessageLog
        from app.human_mode import mark_human_request
        from app.whatsapp_client import send_text
        if not db.query(Patient).filter(Patient.phone==phone).first():raise HTTPException(404,'Paciente demo no encontrado')
        if event not in ('menu','human','message'):raise HTTPException(422,'Evento demo inválido')
        state=db.query(ConversationState).filter(ConversationState.phone==phone).first()
        if not state:state=ConversationState(phone=phone,step='START',data='{}');db.add(state)
        body={'menu':'Demostración: consultar horarios.','human':'Demostración: quiero hablar con una persona.','message':'Demostración: seguimiento administrativo.'}[event]
        db.add(MessageLog(phone=phone,direction='incoming',text=body,message_type='text',source='demo',is_read=False))
        if event=='human':mark_human_request(db,state)
        paused=bool(state.bot_paused)
        db.commit()
        if not paused:await send_text(phone,'Demostración: puedes revisar los horarios disponibles.')
        return RedirectResponse('/panel/messages?phone='+phone,status_code=303)

    @app.get('/favicon.ico')
    def favicon():return RedirectResponse('/static/img/wunsce-logo-144.webp',status_code=307)

    @app.get('/health')
    def health():
        try:
            with tempfile.TemporaryFile(dir=settings.RUNTIME_DIR) as f:f.write(b'ok')
            if settings.DEMO_MODE:
                con=sqlite3.connect(':memory:');con.execute('SELECT 1');con.close()
            else:
                from app.database import engine
                from sqlalchemy import text
                with engine.connect() as con:con.execute(text('SELECT 1'))
        except (OSError,OperationalError,sqlite3.Error):return JSONResponse({'status':'unavailable','service':'esculapio-web'},status_code=503)
        return {'status':'ok','service':'esculapio-web'}

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):return templates.TemplateResponse('public_error.html',{'request':request,'code':422,'message':'Revisa los campos del formulario. No se muestran los datos enviados.'},status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request,exc):
        messages={400:'Formulario no válido. Recarga la página.',401:'Se requiere acceso autorizado.',403:'Tu rol no permite esta acción.',404:'Esta página o registro no existe.',409:'El registro cambió o el horario ya no está disponible.',422:'Revisa los campos y usa únicamente ejemplos demo.',429:'Límite temporal alcanzado. Inténtalo más tarde.',503:'La demo no está disponible temporalmente.'}
        return templates.TemplateResponse('public_error.html',{'request':request,'code':exc.status_code,'message':messages.get(exc.status_code,'No se pudo completar la solicitud.')},status_code=exc.status_code,headers=exc.headers)

    @app.exception_handler(StaleDataError)
    async def stale_error(request,exc):return JSONResponse({"detail":"El registro cambió. Recarga la página."},status_code=409)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request,exc):return JSONResponse({'detail':'El registro ya existe o su relación no es válida.'},status_code=409)
    @app.exception_handler(OperationalError)
    async def storage_error(request,exc):return JSONResponse({'detail':'Almacenamiento no disponible temporalmente.'},status_code=503)

    original=templates.TemplateResponse
    def with_metadata(name,context,**kwargs):
        request=context['request']
        origin=safe_origin(os.getenv('SITE_URL','')) or str(request.base_url).rstrip('/')
        context.update(seo_description=PUBLIC_DESCRIPTIONS.get(request.url.path, 'Demostración administrativa de ESCULAPIO con datos ficticios.'), social_image=origin+'/static/img/og-wunsce.png', canonical_url=origin+request.url.path if request.url.path in ('/','/features','/case-study','/architecture') else None)
        return original(name,context,**kwargs)
    templates.TemplateResponse=with_metadata
