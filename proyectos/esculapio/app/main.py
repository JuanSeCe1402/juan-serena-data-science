import secrets
import hmac
import hashlib
import json
import re
import mimetypes
from pathlib import Path
from datetime import date, timedelta, datetime
from urllib.parse import quote

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi import Path as APIPath
from typing import Annotated
from fastapi.responses import PlainTextResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from werkzeug.security import check_password_hash
from contextlib import asynccontextmanager
import threading,time,tempfile
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.database import Base, engine, get_db
from app.models import Appointment, DateOverride, Patient, MessageLog, ConversationState, AuditLog
from app.scheduler import (
    APPOINTMENT_TYPE_LABELS,
    get_or_create_settings,
    get_slots_for_date,
    book_slot,
    reschedule_slot,
)
from app.whatsapp_client import (
    extract_incoming_message,
    extract_business_app_echo,
    send_text,
    download_media,
    extract_message_statuses,
)
from app.conversation import handle_incoming, notify_doctor_cancellation, is_human_request
from app.jobs import start_scheduler, send_daily_agenda
from app.agenda_pdf import build_agenda_pdf
from app.time_utils import local_today, local_now
from app.human_mode import (
    auto_resume_if_due,
    mark_human_activity,
    mark_human_request,
    pause_manually,
    resume_bot,
)






@asynccontextmanager
async def lifespan(application):
    _validate_security_configuration()
    if not settings.DEMO_MODE:
        from sqlalchemy import inspect
        inspector=inspect(engine)
        names=set(inspector.get_table_names())
        if not names.intersection(Base.metadata.tables):
            Base.metadata.create_all(bind=engine)
        else:
            for table in Base.metadata.sorted_tables:
                if table.name not in names:raise RuntimeError("Database migration required before startup")
                existing={c['name'] for c in inspector.get_columns(table.name)}
                if not set(table.columns.keys())<=existing:raise RuntimeError("Database migration required before startup")
    if settings.ENABLE_JOBS:application.state.scheduler=start_scheduler()
    try:yield
    finally:
        scheduler=getattr(application.state,'scheduler',None)
        if scheduler:scheduler.shutdown(wait=False)

app = FastAPI(title="ESCULAPIO · Operación administrativa",lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)


def _validate_security_configuration():
    if settings.DEMO_MODE:return
    if not re.fullmatch('[a-zA-Z0-9_.-]{3,40}',settings.ADMIN_USER) or not settings.ADMIN_PASSWORD_HASH.startswith(('scrypt:','pbkdf2:sha256:')):
        raise RuntimeError("Configure ADMIN_USER and a strong ADMIN_PASSWORD_HASH")
    if bool(settings.ASSISTANT_USER)!=bool(settings.ASSISTANT_PASSWORD_HASH) or settings.ASSISTANT_USER==settings.ADMIN_USER:
        raise RuntimeError("Configure a separate assistant account or leave both assistant fields empty")
    if settings.ASSISTANT_USER and (not re.fullmatch('[a-zA-Z0-9_.-]{3,40}',settings.ASSISTANT_USER) or not settings.ASSISTANT_PASSWORD_HASH.startswith(('scrypt:','pbkdf2:sha256:'))):
        raise RuntimeError("Configure a valid separate assistant account")
    for value in (settings.ADMIN_PASSWORD_HASH,settings.ASSISTANT_PASSWORD_HASH):
        if value:
            method=value.split('$',1)[0].split(':')
            if method[0]=='pbkdf2' and (len(method)!=3 or int(method[2])<600000):raise RuntimeError("Password hash work factor too low")
            if method[0]=='scrypt' and (len(method)!=4 or int(method[1])<32768 or int(method[2])<8 or int(method[3])<1):raise RuntimeError("Password hash work factor too low")
        if value and any(check_password_hash(value,weak) for weak in ('admin','password','123456','cambia-esta-clave')):
            raise RuntimeError("Weak password hash rejected")
    if settings.INTEGRATIONS_ENABLED and (len(settings.WHATSAPP_VERIFY_TOKEN)<32 or len(settings.META_APP_SECRET)<32):
        raise RuntimeError("Live webhook requires strong signature and verification secrets")






app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent/"static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent/"templates"))
_original_render=templates.TemplateResponse
def _render(name,context,**kwargs):
    request=context['request']
    context.update(demo_mode=settings.DEMO_MODE,csrf_token=request.session.get('csrf',''),demo_replies=__import__('app.security',fromlist=['DEMO_REPLIES']).DEMO_REPLIES)
    context['wunsce_url']=__import__('app.security',fromlist=['safe_origin']).safe_origin(__import__('os').getenv('WUNSCE_URL',''),'https://wunsce-main-production.up.railway.app')
    return _original_render(request=request,name=name,context=context,**kwargs)
templates.TemplateResponse=_render
security = HTTPBasic(auto_error=False)
_auth_lock=threading.Lock()
_auth_failures={}


def check_admin(request: Request,credentials: HTTPBasicCredentials | None=Depends(security)):
    if settings.DEMO_MODE:
        role=request.session.get('role')
        if role not in ('doctor','assistant'):raise HTTPException(401,"Abre la demo para elegir un rol simulado")
        user={'username':'demo-'+role,'role':role}
    else:
        key=request.client.host if request.client else 'unknown'
        now=time.monotonic()
        with _auth_lock:
            for ip,value in list(_auth_failures.items()):
                if now-value[1]>60:_auth_failures.pop(ip,None)
            if _auth_failures.get(key,(0,now))[0]>=10 or len(_auth_failures)>500:raise HTTPException(429,"Demasiados intentos de acceso")
        role=None
        if credentials:
            for candidate,username,password_hash in (('doctor',settings.ADMIN_USER,settings.ADMIN_PASSWORD_HASH),('assistant',settings.ASSISTANT_USER,settings.ASSISTANT_PASSWORD_HASH)):
                if username and password_hash and secrets.compare_digest(credentials.username.encode(),username.encode()) and check_password_hash(password_hash,credentials.password):role=candidate
        if role is None:
            with _auth_lock:
                old=_auth_failures.get(key,(0,now));_auth_failures[key]=(old[0]+1,now)
            raise HTTPException(401,"Autenticación requerida",headers={'WWW-Authenticate':'Basic'})
        with _auth_lock:_auth_failures.pop(key,None)
        user={'username':credentials.username,'role':role}
    request.state.user_role=user['role'];request.state.username=user['username']
    return user


def require_doctor(user: dict = Depends(check_admin)):
    if user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere acceso de doctor.",
        )
    return user


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _audit(
    db: Session,
    user: dict | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    details: str = "",
) -> None:
    actor = (user or {}).get("username", "system")
    role = (user or {}).get("role", "system")
    db.add(
        AuditLog(
            actor=actor,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=None,
        )
    )


def _allowed_media_roots() -> list[Path]:
    roots = [Path(settings.MEDIA_DIR).resolve(), Path("./media").resolve()]
    unique = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def _safe_media_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    try:
        candidate = Path(path_value).resolve()
    except (OSError, RuntimeError):
        return None
    if not candidate.name.startswith("msg_"):
        return None
    for root in _allowed_media_roots():
        try:
            candidate.relative_to(root)
            return candidate
        except ValueError:
            continue
    return None


def _delete_media_paths(paths: list[str | None]) -> int:
    deleted = 0
    for value in paths:
        file_path = _safe_media_path(value)
        if file_path and file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                deleted += 1
            except OSError as exc:
                pass
    return deleted


def _media_type_allowed(mime_type: str) -> bool:
    return (mime_type or "").lower() in settings.MEDIA_ALLOWED_TYPES


def _verify_webhook_signature(raw_body: bytes, signature: str | None) -> bool:
    if not settings.META_APP_SECRET or not signature:
        return False
    expected = "sha256=" + hmac.new(
        settings.META_APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return secrets.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# WEBHOOK DE WHATSAPP
# ---------------------------------------------------------------------------

@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and secrets.compare_digest(params.get("hub.verify_token","").encode(),settings.WHATSAPP_VERIFY_TOKEN.encode())
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


async def _send_staff_alert(db: Session, event: str, body: str) -> None:
    """Envía una alerta al contacto operativo configurado, sin romper el flujo si falla."""
    cfg = get_or_create_settings(db)
    enabled_for_event = {
        "human": bool(cfg.alert_human_requests),
        "new_appointment": bool(cfg.alert_new_appointments),
        "cancellation": bool(cfg.alert_cancellations),
        "reschedule": bool(cfg.alert_reschedules),
    }.get(event, False)
    phone = _normalize_phone(cfg.alert_contact_phone or "")
    if not cfg.alert_whatsapp_enabled or not enabled_for_event or len(phone) < 8:
        return
    try:
        await send_text(phone, body)
    except Exception as exc:
        pass


@app.post("/webhook")
async def receive_message(request: Request,db: Session=Depends(get_db)):
    from app.integrations import split_events
    raw_body=await request.body()
    if len(raw_body)>32768:raise HTTPException(413,"Webhook demasiado grande")
    if not _verify_webhook_signature(raw_body,request.headers.get('X-Hub-Signature-256')):raise HTTPException(403,"Firma inválida")
    try:
        payload=json.loads(raw_body)
        if not settings.WHATSAPP_PHONE_NUMBER_ID:raise HTTPException(503,"Canal externo no configurado")
        events=split_events(payload,expected_phone_id=settings.WHATSAPP_PHONE_NUMBER_ID)
    except (ValueError,UnicodeDecodeError,TypeError):raise HTTPException(400,"Payload inválido")
    processed=0
    for payload in events:
        await _process_webhook_event(payload,db)
        processed+=1
    return {'status':'accepted','processed':processed}


async def _process_webhook_event(payload,db):
    # Estados de entrega de mensajes salientes reportados por Meta.
    statuses = extract_message_statuses(payload)
    if statuses:
        rank = {"sent": 1, "delivered": 2, "read": 3}
        updated = 0
        for item in statuses:
            msg = (
                db.query(MessageLog)
                .filter(MessageLog.external_id == item["external_id"])
                .first()
            )
            if not msg:
                continue

            new_status = item.get("status")
            current_status = msg.delivery_status
            should_update = (
                new_status == "failed"
                or current_status == "failed"
                or rank.get(new_status, 0) >= rank.get(current_status, 0)
            )
            if should_update:
                msg.delivery_status = new_status
                msg.status_updated_at = local_now().replace(tzinfo=None)
                msg.error_detail = "Proveedor reportó fallo" if item.get("error_detail") else None
                updated += 1

        if updated:
            db.commit()
        return {"status": "message_status", "updated": updated}

    # En Coexistence, los mensajes que el consultorio manda desde el celular
    # llegan como smb_message_echoes. Se guardan en el buzón pero NO se pasan
    # al bot como si los hubiera escrito el paciente.
    echo = extract_business_app_echo(payload)
    if echo and echo.get("to"):
        external_id = echo.get("external_id")
        if external_id and db.query(MessageLog).filter(MessageLog.external_id == external_id).first():
            return {"status": "duplicate_echo"}
        db.add(
            MessageLog(
                phone=echo["to"],
                direction="outgoing",
                text=echo.get("text", ""),
                message_type=echo.get("message_type", "text"),
                external_id=external_id,
                source="business_app",
            )
        )
        # Si el doctor responde desde WhatsApp Business (Coexistence),
        # también cuenta como actividad humana y reinicia el temporizador.
        echo_state = db.query(ConversationState).filter(ConversationState.phone == echo["to"]).first()
        if echo_state:
            mark_human_activity(db, echo_state)
        db.commit()
        return {"status": "echo_logged"}

    parsed = extract_incoming_message(payload)
    if parsed is None:
        return {"status": "ignored"}

    external_id = parsed.get("external_id")
    if external_id and db.query(MessageLog).filter(MessageLog.external_id == external_id).first():
        return {"status": "duplicate"}

    log = MessageLog(
        phone=parsed["from"],
        direction="incoming",
        text=parsed.get("text", ""),
        message_type=parsed.get("message_type", "text"),
        external_id=external_id,
        source="patient",
        is_read=False,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Si el mensaje trae una foto, documento o audio, se guarda una copia
    # local permanente (los enlaces de WhatsApp caducan y el paciente
    # podría borrar el mensaje de su lado más adelante).
    media_id = parsed.get("media_id")
    if media_id:
        max_bytes = max(1, settings.MAX_MEDIA_MB) * 1024 * 1024
        result = await download_media(media_id, max_bytes=max_bytes)
        if result is not None:
            content, mime_type = result
            if _media_type_allowed(mime_type):
                media_dir = Path(settings.MEDIA_DIR)
                media_dir.mkdir(parents=True, exist_ok=True)
                extension = mimetypes.guess_extension(mime_type) or ""
                filename = f"msg_{log.id}{extension}"
                file_path = media_dir / filename
                file_path.write_bytes(content)
                log.media_path = str(file_path)
                log.media_mime_type = mime_type
                db.commit()
            else:
                log.text = (
                    (log.text or "").strip()
                    + f"\n[Adjunto no guardado: tipo {mime_type} no permitido]"
                ).strip()
                db.commit()
        else:
            log.text = (
                (log.text or "").strip()
                + f"\n[Adjunto no guardado: descarga fallida o supera {settings.MAX_MEDIA_MB} MB]"
            ).strip()
            db.commit()

    state = db.query(ConversationState).filter(ConversationState.phone == parsed["from"]).first()

    # El paciente puede pedir hablar con una persona en cualquier momento.
    # Esto pausa el bot para esa conversación y genera una alerta en el panel.
    if parsed.get("button_id") == "menu_human" or is_human_request(parsed.get("text", "")):
        if state is None:
            state = ConversationState(phone=parsed["from"], step="START", data="{}")
            db.add(state)
        already_requested = bool(state.human_requested)
        mark_human_request(db, state)
        db.commit()
        if not already_requested:
            patient = db.query(Patient).filter(Patient.phone == parsed["from"]).first()
            patient_name = (patient.name if patient and patient.name else "Paciente")
            await _send_staff_alert(
                db,
                "human",
                f"🔔 Atención humana solicitada\n"
                f"Paciente: {patient_name}\n"
                f"WhatsApp: {parsed['from']}\n"
                f"Hora: {local_now().strftime('%H:%M')}\n\n"
                f"Revisa el panel de Mensajes para atender la conversación.",
            )
        await send_text(
            parsed["from"],
            "Claro. Ya avisé al consultorio que deseas hablar con una persona. "
            "En cuanto sea posible te responderán por este mismo chat. 👤",
        )
        return {"status": "human_requested"}

    if state and state.bot_paused:
        # Protección adicional: si justo venció el temporizador entre revisiones
        # del scheduler, reactivamos antes de procesar este nuevo mensaje.
        if auto_resume_if_due(db, state):
            db.commit()
            state = db.query(ConversationState).filter(ConversationState.phone == parsed["from"]).first()

    if state and state.bot_paused:
        # Modo humano: registramos el mensaje para que el doctor lo vea,
        # pero no hacemos que el bot responda automáticamente.
        return {"status": "logged_human_mode"}

    try:
        await handle_incoming(db, parsed["from"], parsed["text"], parsed["button_id"])
    except Exception:
        # Si el procesamiento falla, permitimos que Meta reintente el webhook.
        db.delete(log)
        db.commit()
        raise

    return {"status": "ok"}



# ---------------------------------------------------------------------------
# PANEL WEB
# ---------------------------------------------------------------------------

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse('public_home.html',{'request':request})


@app.get("/privacy")
def privacy_policy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "clinic_phone": settings.CLINIC_PHONE,
            "clinic_email": settings.CLINIC_EMAIL,
            "updated": local_today().strftime("%d/%m/%Y"),
        },
    )


@app.get("/panel")
def panel(request: Request, db: Session = Depends(get_db), user: str = Depends(check_admin)):
    today = local_today()
    horizon = today + timedelta(days=30)

    appointments = (
        db.query(Appointment)
        .filter(Appointment.date >= today, Appointment.date <= horizon, Appointment.status == "confirmada")
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )
    pending_review = (
        db.query(Appointment)
        .filter(Appointment.status == "pendiente_revision")
        .order_by(Appointment.date.desc(), Appointment.start_time)
        .all()
    )
    overrides = db.query(DateOverride).filter(DateOverride.date >= today).order_by(DateOverride.date).all()
    cfg = get_or_create_settings(db)

    prefill_patient = None
    patient_id_param = request.query_params.get("patient_id", "")
    if patient_id_param.isdigit():
        prefill_patient = db.query(Patient).filter(Patient.id == int(patient_id_param)).first()

    far_future_appointments = (
        db.query(Appointment)
        .filter(Appointment.far_future == True, Appointment.status == "confirmada")  # noqa: E712
        .order_by(Appointment.date)
        .all()
    )

    no_show_counts = dict(
        db.query(Appointment.patient_id, func.count(Appointment.id))
        .filter(Appointment.status == "no_asistio")
        .group_by(Appointment.patient_id)
        .all()
    )

    return templates.TemplateResponse(
        "panel.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "appointments": appointments,
            "pending_review": pending_review,
            "far_future_appointments": far_future_appointments,
            "far_future_days": settings.FAR_FUTURE_DAYS,
            "overrides": overrides,
            "cfg": cfg,
            "today": today,
            "no_show_counts": no_show_counts,
            "cancellation_hours": settings.CANCELLATION_HOURS,
            "appointment_type_labels": APPOINTMENT_TYPE_LABELS,
            "panel_order_json": cfg.panel_order or "[]",
            "new_date": request.query_params.get("new_date", ""),
            "prefill_patient": prefill_patient,
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.get("/panel/calendar")
def calendar_page(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "today": local_today(),
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.get("/panel/calendar/events")
def calendar_events(
    start: str,
    end: str,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    """Citas para la vista mensual del calendario."""
    try:
        start_day = date.fromisoformat(start)
        end_day = date.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rango de fechas inválido")
    if end_day < start_day or (end_day - start_day).days > 93:
        raise HTTPException(status_code=400, detail="Rango de calendario demasiado amplio")

    rows = (
        db.query(Appointment)
        .filter(
            Appointment.date >= start_day,
            Appointment.date <= end_day,
            Appointment.status != "cancelada",
        )
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )
    return {
        "events": [
            {
                "id": a.id,
                "date": a.date.isoformat(),
                "start": a.start_time.strftime("%H:%M"),
                "end": a.end_time.strftime("%H:%M"),
                "name": (a.patient.name or a.patient.phone),
                "phone": a.patient.phone,
                "type": a.appointment_type or "consulta",
                "type_label": APPOINTMENT_TYPE_LABELS.get(a.appointment_type or "consulta", "Consulta"),
                "reason": a.reason or "Sin motivo",
                "status": a.status,
                "patient_url": f"/panel/patients/{a.patient_id}",
                "reschedule_url": f"/panel/appointment/{a.id}/reschedule?return_to=calendar",
            }
            for a in rows
        ]
    }


@app.post("/panel/layout")
async def save_panel_layout(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    """Guarda el orden del dashboard para conservarlo entre dispositivos."""
    payload = await request.json()
    order = payload.get("order", [])
    if not isinstance(order, list):
        raise HTTPException(status_code=400, detail="Orden inválido")
    clean = []
    for item in order[:30]:
        if isinstance(item, str) and re.fullmatch(r"[a-z0-9_-]{1,50}", item):
            clean.append(item)
    cfg = get_or_create_settings(db)
    cfg.panel_order = json.dumps(clean)
    db.commit()
    return {"status": "ok", "order": clean}


@app.get("/panel/slots")
def panel_slots(
    day: str,
    appointment_type: str = "consulta",
    exclude_appointment_id: int | None = None,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    if appointment_type not in APPOINTMENT_TYPE_LABELS:
        raise HTTPException(status_code=400, detail="Tipo de cita inválido")
    try:
        target = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fecha inválida")
    return {
        "slots": [
            t.strftime("%H:%M")
            for t in get_slots_for_date(
                db,
                target,
                appointment_type,
                exclude_appointment_id=exclude_appointment_id,
            )
        ]
    }


@app.get("/panel/appointment/{appt_id}/reschedule")
def reschedule_appointment_page(
    appt_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if appt is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if appt.status != "confirmada":
        return RedirectResponse(
            f"/panel/patients/{appt.patient_id}?error=" + quote("Solo se pueden reagendar citas confirmadas"),
            status_code=303,
        )

    return templates.TemplateResponse(
        "reschedule.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "appt": appt,
            "appointment_type_label": APPOINTMENT_TYPE_LABELS.get(
                appt.appointment_type or "consulta", "Consulta"
            ),
            "today": local_today(),
            "return_to": request.query_params.get("return_to", "calendar"),
            "error": request.query_params.get("error", ""),
        },
    )


@app.post("/panel/appointment/{appt_id}/reschedule")
async def reschedule_appointment(
    appt_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    day: str = Form(...),
    start_time: str = Form(...),
    expected_version: int = Form(...),
    notify_patient: str | None = Form(None),
    return_to: str = Form("calendar"),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if appt is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if appt.version!=expected_version:raise HTTPException(409,"La cita cambió. Recarga el formulario.")
    patient_id = appt.patient_id
    patient = appt.patient
    old_day = appt.date
    old_start = appt.start_time

    try:
        target_day = date.fromisoformat(day)
        target_time = datetime.strptime(start_time, "%H:%M").time()
    except ValueError:
        return RedirectResponse(
            f"/panel/appointment/{appt_id}/reschedule?return_to={quote(return_to)}&error="
            + quote("Fecha u hora inválida"),
            status_code=303,
        )

    moved = reschedule_slot(db, appt_id, target_day, target_time,expected_version=expected_version)
    if moved is None:
        return RedirectResponse(
            f"/panel/appointment/{appt_id}/reschedule?return_to={quote(return_to)}&error="
            + quote("Ese horario ya no está disponible. Elige otro."),
            status_code=303,
        )

    _audit(
        db, user, "appointment_rescheduled", "appointment", moved.id,
        f"{patient.name or patient.phone}: {old_day} {old_start.strftime('%H:%M')} -> "
        f"{target_day} {target_time.strftime('%H:%M')}"
    )
    db.commit()

    if notify_patient:
        await send_text(
            patient.phone,
            f"🔄 Tu cita fue reagendada. Nueva fecha: {target_day.strftime('%d/%m/%Y')} "
            f"a las {target_time.strftime('%H:%M')} con {settings.DOCTOR_NAME}.",
        )

    await _send_staff_alert(
        db,
        "reschedule",
        f"🔄 Cita reagendada\n"
        f"Paciente: {patient.name or patient.phone}\n"
        f"Antes: {old_day.strftime('%d/%m/%Y')} {old_start.strftime('%H:%M')}\n"
        f"Ahora: {target_day.strftime('%d/%m/%Y')} {target_time.strftime('%H:%M')}",
    )

    notice = quote("Cita reagendada correctamente")
    if return_to == "patient":
        return RedirectResponse(f"/panel/patients/{patient_id}?notice={notice}", status_code=303)
    if return_to == "agenda":
        return RedirectResponse(f"/panel?notice={notice}", status_code=303)
    return RedirectResponse(f"/panel/calendar?notice={notice}", status_code=303)


@app.post("/panel/appointment/create")
async def create_appointment_from_panel(
    patient_name: str = Form(...),
    patient_phone: str = Form(...),
    patient_age: str = Form(""),
    appointment_type: str = Form("consulta"),
    day: str = Form(...),
    start_time: str = Form(...),
    reason: str = Form(""),
    notify_patient: str | None = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    if appointment_type not in APPOINTMENT_TYPE_LABELS:
        return RedirectResponse("/panel?error=" + quote("Tipo de cita inválido"), status_code=303)

    phone = _normalize_phone(patient_phone)
    if len(phone) < 8:
        return RedirectResponse("/panel?error=" + quote("El teléfono no parece válido"), status_code=303)

    try:
        target_day = date.fromisoformat(day)
        target_time = datetime.strptime(start_time, "%H:%M").time()
    except ValueError:
        return RedirectResponse("/panel?error=" + quote("Fecha u hora inválida"), status_code=303)

    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if patient is None:
        patient = Patient(phone=phone)
        db.add(patient)
        db.flush()

    patient.name = patient_name.strip()
    if patient_age.strip().isdigit():
        patient.age = int(patient_age.strip())
    db.commit()
    db.refresh(patient)

    appt = book_slot(db, patient.id, target_day, target_time, reason.strip(), appointment_type)
    if appt is None:
        return RedirectResponse(
            "/panel?error=" + quote("Ese horario ya no está disponible o queda fuera del horario del consultorio"),
            status_code=303,
        )

    _audit(
        db, user, "appointment_created", "appointment", appt.id,
        f"{patient.name or phone} · {target_day} {target_time.strftime('%H:%M')} · {appointment_type}"
    )
    db.commit()

    if notify_patient:
        await send_text(
            phone,
            f"✅ El consultorio agendó tu cita: {APPOINTMENT_TYPE_LABELS[appointment_type]} "
            f"el {target_day.strftime('%d/%m/%Y')} a las {target_time.strftime('%H:%M')} "
            f"con {settings.DOCTOR_NAME}.",
        )

    return RedirectResponse("/panel?notice=" + quote("Cita agregada correctamente"), status_code=303)


@app.get("/panel/patients")
def patients_page(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    query = db.query(Patient)
    term = q.strip()
    if term:
        like = f"%{term}%"
        query = query.filter(
            (Patient.name.ilike(like)) | (Patient.phone.ilike(like))
        )

    patients = query.order_by(Patient.name, Patient.phone).limit(200).all()
    ids = [p.id for p in patients]
    stats_by_patient = {pid: {} for pid in ids}
    next_by_patient = {}

    if ids:
        grouped = (
            db.query(Appointment.patient_id, Appointment.status, func.count(Appointment.id))
            .filter(Appointment.patient_id.in_(ids))
            .group_by(Appointment.patient_id, Appointment.status)
            .all()
        )
        for pid, status_value, count in grouped:
            stats_by_patient.setdefault(pid, {})[status_value] = int(count)

        upcoming = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id.in_(ids),
                Appointment.status == "confirmada",
                Appointment.date >= local_today(),
            )
            .order_by(Appointment.date, Appointment.start_time)
            .all()
        )
        for appt in upcoming:
            next_by_patient.setdefault(appt.patient_id, appt)

    return templates.TemplateResponse(
        "patients.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "patients": patients,
            "stats_by_patient": stats_by_patient,
            "next_by_patient": next_by_patient,
            "q": term,
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.get("/panel/patients/{patient_id}/edit")
def edit_patient_page(
    patient_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    return templates.TemplateResponse(
        "edit_patient.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "patient": patient,
            "error": request.query_params.get("error", ""),
        },
    )


@app.post("/panel/patients/{patient_id}/edit")
def update_patient(
    patient_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    patient_name: str = Form(...),
    patient_phone: str = Form(...),
    patient_age: str = Form(""),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    name = patient_name.strip()
    new_phone = _normalize_phone(patient_phone)
    old_phone = patient.phone

    if not name:
        return RedirectResponse(
            f"/panel/patients/{patient_id}/edit?error="
            + quote("El nombre no puede estar vacío"),
            status_code=303,
        )
    if len(new_phone) < 8:
        return RedirectResponse(
            f"/panel/patients/{patient_id}/edit?error="
            + quote("El teléfono no parece válido"),
            status_code=303,
        )

    age_value = None
    if patient_age.strip():
        try:
            age_value = int(patient_age)
        except ValueError:
            return RedirectResponse(
                f"/panel/patients/{patient_id}/edit?error="
                + quote("La edad debe ser un número"),
                status_code=303,
            )
        if age_value < 1 or age_value > 119:
            return RedirectResponse(
                f"/panel/patients/{patient_id}/edit?error="
                + quote("La edad debe estar entre 1 y 119"),
                status_code=303,
            )

    if new_phone != old_phone:
        duplicate_patient = (
            db.query(Patient)
            .filter(Patient.phone == new_phone, Patient.id != patient_id)
            .first()
        )
        existing_state = (
            db.query(ConversationState)
            .filter(ConversationState.phone == new_phone)
            .first()
        )
        existing_messages = (
            db.query(MessageLog)
            .filter(MessageLog.phone == new_phone)
            .first()
        )
        if duplicate_patient or existing_state or existing_messages:
            return RedirectResponse(
                f"/panel/patients/{patient_id}/edit?error="
                + quote(
                    "Ese WhatsApp ya tiene información registrada. "
                    "No se cambió el número para evitar mezclar pacientes."
                ),
                status_code=303,
            )

        # La agenda usa patient_id, por lo que las citas no necesitan cambios.
        # La conversación y su bitácora sí se identifican por teléfono.
        db.query(ConversationState).filter(
            ConversationState.phone == old_phone
        ).update(
            {ConversationState.phone: new_phone},
            synchronize_session=False,
        )
        db.query(MessageLog).filter(
            MessageLog.phone == old_phone
        ).update(
            {MessageLog.phone: new_phone},
            synchronize_session=False,
        )
        patient.phone = new_phone

    patient.name = name
    patient.age = age_value
    _audit(
        db, user, "patient_updated", "patient", patient.id,
        f"Nombre={name}; WhatsApp={patient.phone}; Edad={age_value or ''}"
    )
    db.commit()

    return RedirectResponse(
        f"/panel/patients/{patient_id}?notice="
        + quote("Datos del paciente actualizados"),
        status_code=303,
    )


@app.post("/panel/patients/{patient_id}/delete")
def delete_patient(
    patient_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    confirm_delete: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    """Elimina definitivamente al paciente y todos sus datos locales asociados."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if confirm_delete != "ELIMINAR":
        return RedirectResponse(
            f"/panel/patients/{patient_id}?error="
            + quote("Escribe ELIMINAR para confirmar la eliminación permanente"),
            status_code=303,
        )

    phone = patient.phone
    patient_label = patient.name or patient.phone
    patient_messages = db.query(MessageLog).filter(MessageLog.phone == phone).all()
    media_paths = [m.media_path for m in patient_messages if m.media_path]

    try:
        # Las citas dependen del paciente por patient_id.
        db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).delete(synchronize_session=False)

        # El buzón y el estado conversacional se vinculan por número.
        db.query(MessageLog).filter(
            MessageLog.phone == phone
        ).delete(synchronize_session=False)

        db.query(ConversationState).filter(
            ConversationState.phone == phone
        ).delete(synchronize_session=False)

        _audit(
            db, user, "patient_deleted", "patient", patient_id,
            f"{patient_label} · {phone}"
        )
        db.delete(patient)
        db.commit()
        _delete_media_paths(media_paths)
    except Exception:
        db.rollback()
        return RedirectResponse(
            f"/panel/patients/{patient_id}?error="
            + quote("No se pudo eliminar el paciente. No se realizaron cambios."),
            status_code=303,
        )

    return RedirectResponse(
        "/panel/patients?notice="
        + quote("Registro de paciente eliminado permanentemente"),
        status_code=303,
    )


@app.get("/panel/patients/{patient_id}")
def patient_detail_page(
    patient_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    all_appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
        .limit(300)
        .all()
    )
    upcoming = sorted(
        [
            a for a in all_appointments
            if a.status == "confirmada" and a.date >= local_today()
        ],
        key=lambda a: (a.date, a.start_time),
    )
    history = [
        a for a in all_appointments
        if not (a.status == "confirmada" and a.date >= local_today())
    ]

    stats = {
        "total": len(all_appointments),
        "atendida": sum(1 for a in all_appointments if a.status == "atendida"),
        "no_asistio": sum(1 for a in all_appointments if a.status == "no_asistio"),
        "cancelada": sum(1 for a in all_appointments if a.status == "cancelada"),
        "proximas": len(upcoming),
    }

    return templates.TemplateResponse(
        "patient_detail.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "patient": patient,
            "upcoming": upcoming,
            "history": history,
            "stats": stats,
            "appointment_type_labels": APPOINTMENT_TYPE_LABELS,
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.get("/panel/messages")
def messages_panel(
    request: Request,
    phone: str | None = None,
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    recent = db.query(MessageLog).order_by(MessageLog.created_at.desc(), MessageLog.id.desc()).limit(500).all()

    unread_rows = (
        db.query(MessageLog.phone, func.count(MessageLog.id))
        .filter(MessageLog.direction == "incoming", MessageLog.is_read == False)
        .group_by(MessageLog.phone)
        .all()
    )
    unread_by_phone = {phone_value: count for phone_value, count in unread_rows}
    states = {st.phone: st for st in db.query(ConversationState).all()}

    contacts = []
    seen = set()
    for msg in recent:
        if msg.phone in seen:
            continue
        seen.add(msg.phone)
        patient = db.query(Patient).filter(Patient.phone == msg.phone).first()
        st = states.get(msg.phone)
        contacts.append(
            {
                "phone": msg.phone,
                "name": patient.name if patient and patient.name else msg.phone,
                "last_text": msg.text,
                "last_at": msg.created_at,
                "unread_count": int(unread_by_phone.get(msg.phone, 0)),
                "human_requested": bool(st and st.human_requested),
                "bot_paused": bool(st and st.bot_paused),
            }
        )

    # Solicitudes humanas primero; luego no leídos y actividad reciente.
    contacts.sort(
        key=lambda c: (c["human_requested"], c["unread_count"] > 0, c["last_at"]),
        reverse=True,
    )

    selected_phone = phone or (contacts[0]["phone"] if contacts else None)
    conversation = []
    selected_patient = None
    bot_paused = False
    human_requested = False
    pause_reason = None
    last_human_activity_at = None
    if selected_phone:
        conversation = (
            db.query(MessageLog)
            .filter(MessageLog.phone == selected_phone)
            .order_by(MessageLog.created_at.desc(), MessageLog.id.desc())
            .limit(300)
            .all()
        )
        conversation.reverse()
        selected_patient = db.query(Patient).filter(Patient.phone == selected_phone).first()
        state = db.query(ConversationState).filter(ConversationState.phone == selected_phone).first()
        bot_paused = bool(state and state.bot_paused)
        human_requested = bool(state and state.human_requested)
        pause_reason = state.pause_reason if state else None
        last_human_activity_at = state.last_human_activity_at if state else None

        # Abrir el chat cuenta como revisarlo. No modifica el modo humano.
        db.query(MessageLog).filter(
            MessageLog.phone == selected_phone,
            MessageLog.direction == "incoming",
            MessageLog.is_read == False,
        ).update({MessageLog.is_read: True}, synchronize_session=False)
        db.commit()
        for c in contacts:
            if c["phone"] == selected_phone:
                c["unread_count"] = 0
                break

    total_unread = sum(c["unread_count"] for c in contacts)
    total_human_requests = sum(1 for c in contacts if c["human_requested"])

    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "contacts": contacts,
            "selected_phone": selected_phone,
            "selected_patient": selected_patient,
            "conversation": conversation,
            "bot_paused": bot_paused,
            "human_requested": human_requested,
            "pause_reason": pause_reason,
            "last_human_activity_at": last_human_activity_at,
            "human_auto_resume_minutes": get_or_create_settings(db).human_auto_resume_minutes,
            "total_unread": total_unread,
            "total_human_requests": total_human_requests,
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.get("/panel/messages/notifications")
def messages_notifications(
    db: Session = Depends(get_db),
    user: str = Depends(check_admin),
):
    unread_count = db.query(MessageLog).filter(
        MessageLog.direction == "incoming", MessageLog.is_read == False
    ).count()
    human_requests = db.query(ConversationState).filter(
        ConversationState.human_requested == True
    ).count()
    latest = (
        db.query(MessageLog)
        .filter(MessageLog.direction == "incoming", MessageLog.is_read == False)
        .order_by(MessageLog.id.desc())
        .first()
    )
    latest_payload = None
    if latest:
        patient = db.query(Patient).filter(Patient.phone == latest.phone).first()
        st = db.query(ConversationState).filter(ConversationState.phone == latest.phone).first()
        latest_payload = {
            "id": latest.id,
            "phone": latest.phone,
            "name": patient.name if patient and patient.name else latest.phone,
            "text": latest.text or "Nuevo mensaje",
            "human_requested": bool(st and st.human_requested),
        }
    return {
        "unread_count": unread_count,
        "human_requests": human_requests,
        "latest": latest_payload,
    }


@app.post("/panel/messages/send")
async def send_message_from_panel(
    phone: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    phone = _normalize_phone(phone)
    if body.strip():
        sent = await send_text(phone, body.strip())
        if not sent:
            return RedirectResponse(
                f"/panel/messages?phone={quote(phone)}&error="
                + quote("WhatsApp rechazó el envío. Revisa el estado del mensaje y la configuración de Meta."),
                status_code=303,
            )
        state = db.query(ConversationState).filter(ConversationState.phone == phone).first()
        if state:
            # La primera respuesta humana quita la alerta y comienza el temporizador;
            # cada respuesta posterior vuelve a contar desde cero.
            mark_human_activity(db, state)
        _audit(db, user, "message_sent", "conversation", phone, "Respuesta manual desde panel")
        db.commit()
    return RedirectResponse(f"/panel/messages?phone={quote(phone)}", status_code=303)


@app.post("/panel/messages/{message_id}/delete")
def delete_message_from_panel(
    message_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    msg = db.query(MessageLog).filter(MessageLog.id == message_id).first()
    if not msg:
        return RedirectResponse(
            "/panel/messages?error=" + quote("El mensaje ya no existe"),
            status_code=303,
        )

    phone = msg.phone
    media_path = msg.media_path
    _audit(db, user, "message_deleted", "message", msg.id, f"Conversación {phone}")
    db.delete(msg)
    db.commit()
    _delete_media_paths([media_path])
    return RedirectResponse(
        f"/panel/messages?phone={quote(phone)}&notice=" + quote("Mensaje eliminado del buzón"),
        status_code=303,
    )


@app.post("/panel/messages/delete-conversation")
def delete_conversation_from_panel(
    phone: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    phone = _normalize_phone(phone)
    messages = db.query(MessageLog).filter(MessageLog.phone == phone).all()
    media_paths = [m.media_path for m in messages if m.media_path]
    deleted = db.query(MessageLog).filter(MessageLog.phone == phone).delete(synchronize_session=False)
    state = db.query(ConversationState).filter(ConversationState.phone == phone).first()
    if state:
        # Clearing messages must never reactivate automation implicitly.
        pause_manually(state)
    _audit(db, user, "conversation_cleared", "conversation", phone, f"{deleted} mensajes")
    db.commit()
    _delete_media_paths(media_paths)
    notice = f"Se eliminaron {deleted} mensajes del buzón ; el bot permanece pausado"
    return RedirectResponse("/panel/messages?notice=" + quote(notice), status_code=303)


@app.post("/panel/messages/bot-mode")
def update_conversation_bot_mode(
    phone: str = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    phone = _normalize_phone(phone)
    if action not in ("pause", "resume"):
        raise HTTPException(status_code=400, detail="Acción inválida")

    state = db.query(ConversationState).filter(ConversationState.phone == phone).first()
    if state is None:
        state = ConversationState(phone=phone, step="START", data="{}")
        db.add(state)

    if action == "pause":
        pause_manually(state)
    else:
        # Después de una atención manual reiniciamos el flujo para evitar
        # continuar una reserva a medias con datos viejos.
        resume_bot(state)
    _audit(db, user, f"bot_{action}", "conversation", phone, "")
    db.commit()

    message = "Bot pausado para esta conversación" if action == "pause" else "Bot reanudado para esta conversación"
    return RedirectResponse(
        f"/panel/messages?phone={quote(phone)}&notice=" + quote(message),
        status_code=303,
    )


@app.get("/panel/settings")
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    cfg = get_or_create_settings(db)
    today = local_today()
    overrides = (
        db.query(DateOverride)
        .filter(DateOverride.date >= today)
        .order_by(DateOverride.date)
        .all()
    )
    activity = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(100)
        .all()
    )
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "clinic_name": settings.CLINIC_NAME,
            "doctor_name": settings.DOCTOR_NAME,
            "cfg": cfg,
            "today": today,
            "overrides": overrides,
            "activity": activity,
            "notice": request.query_params.get("notice", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@app.post("/panel/settings")
def update_settings(
    work_start: str = Form(...),
    work_end: str = Form(...),
    consult_minutes: int = Form(...),
    work_days: str = Form(...),
    human_auto_resume_minutes: int = Form(0),
    alert_contact_name: str = Form(""),
    alert_contact_phone: str = Form(""),
    alert_whatsapp_enabled: str | None = Form(None),
    alert_human_requests: str | None = Form(None),
    alert_new_appointments: str | None = Form(None),
    alert_cancellations: str | None = Form(None),
    alert_reschedules: str | None = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    cfg = get_or_create_settings(db)
    cfg.work_start = work_start
    cfg.work_end = work_end
    cfg.consult_minutes = consult_minutes
    cfg.work_days = work_days
    cfg.human_auto_resume_minutes = max(0, human_auto_resume_minutes)
    cfg.alert_contact_name = alert_contact_name.strip()
    cfg.alert_contact_phone = _normalize_phone(alert_contact_phone)
    cfg.alert_whatsapp_enabled = alert_whatsapp_enabled is not None
    cfg.alert_human_requests = alert_human_requests is not None
    cfg.alert_new_appointments = alert_new_appointments is not None
    cfg.alert_cancellations = alert_cancellations is not None
    cfg.alert_reschedules = alert_reschedules is not None
    _audit(db, user, "settings_updated", "settings", cfg.id, "Configuración general/alertas")
    db.commit()
    return RedirectResponse("/panel/settings?notice=" + quote("Configuración guardada"), status_code=303)


@app.post("/panel/block-day")
def block_day(
    day: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    the_date = date.fromisoformat(day)
    override = db.query(DateOverride).filter(DateOverride.date == the_date).first()
    if override is None:
        override = DateOverride(date=the_date)
        db.add(override)
    override.is_blocked = True
    override.custom_start = None
    override.custom_end = None
    override.note = note or "Bloqueado"
    db.flush()
    _audit(db, user, "day_blocked", "date_override", override.id, f"{the_date} · {override.note}")
    db.commit()
    return RedirectResponse("/panel/settings", status_code=303)


@app.post("/panel/custom-day")
def custom_day(
    day: str = Form(...),
    custom_start: str = Form(...),
    custom_end: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db),
    user: dict = Depends(require_doctor),
):
    the_date = date.fromisoformat(day)
    override = db.query(DateOverride).filter(DateOverride.date == the_date).first()
    if override is None:
        override = DateOverride(date=the_date)
        db.add(override)
    override.is_blocked = False
    override.custom_start = custom_start
    override.custom_end = custom_end
    override.note = note or "Horario especial"
    db.flush()
    _audit(
        db, user, "custom_schedule_set", "date_override", override.id,
        f"{the_date} · {custom_start}-{custom_end} · {override.note}"
    )
    db.commit()
    return RedirectResponse("/panel/settings", status_code=303)


@app.post("/panel/override/{override_id}/delete")
def delete_override(override_id: Annotated[int,APIPath(ge=1,le=2147483647)], db: Session = Depends(get_db), user: dict = Depends(require_doctor)):
    override = db.get(DateOverride,override_id)
    if override:
        details = f"{override.date} · {override.note or ''}"
        _audit(db, user, "date_override_deleted", "date_override", override.id, details)
        db.delete(override)
        db.commit()
    return RedirectResponse("/panel/settings", status_code=303)


@app.post("/panel/appointment/{appt_id}/cancel")
async def cancel_appointment(
    appt_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    reason: str = Form(""),
    expected_version: int = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    appt = db.get(Appointment,appt_id)
    if appt is None:raise HTTPException(404,"Cita no encontrada")
    if appt.version!=expected_version:raise HTTPException(409,"La cita cambió. Recarga el formulario.")
    if appt.status != "confirmada":raise HTTPException(409,"La cita ya cambió de estado")
    if appt:
        appt.status = "cancelada"
        _audit(
            db, user, "appointment_cancelled", "appointment", appt.id,
            f"{appt.patient.name or appt.patient.phone} · {appt.date} {appt.start_time.strftime('%H:%M')} · {reason or 'Sin motivo'}"
        )
        db.commit()
        await notify_doctor_cancellation(appt.patient, appt.date, appt.start_time.strftime("%H:%M"), reason)
    return RedirectResponse("/panel", status_code=303)


@app.post("/panel/appointment/{appt_id}/mark")
def mark_appointment(
    appt_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    result: str = Form(...),
    expected_version: int = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    if result not in ("atendida", "no_asistio"):
        raise HTTPException(status_code=400, detail="Valor inválido")
    appt = db.get(Appointment,appt_id)
    if appt is None:raise HTTPException(404,"Cita no encontrada")
    if appt.version!=expected_version:raise HTTPException(409,"La cita cambió. Recarga el formulario.")
    if appt.status not in ('confirmada','pendiente_revision'):raise HTTPException(409,"La cita ya cambió de estado")
    if appt.date>local_today():raise HTTPException(409,"No se registra asistencia de una cita futura")
    if appt:
        appt.status = result
        _audit(
            db, user, "appointment_marked", "appointment", appt.id,
            f"{appt.patient.name or appt.patient.phone} · {result}"
        )
        db.commit()
    return RedirectResponse("/panel", status_code=303)


@app.get("/panel/agenda/pdf")
def download_agenda_pdf(
    day: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    try:target_day = date.fromisoformat(day) if day else local_today()
    except ValueError:raise HTTPException(400,"Fecha inválida")
    pdf_path = build_agenda_pdf(db, target_day)
    from starlette.background import BackgroundTask
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"agenda_demo_{target_day.isoformat()}.pdf" if settings.DEMO_MODE else f"agenda_{target_day.isoformat()}.pdf",background=BackgroundTask(Path(pdf_path).unlink,missing_ok=True))


@app.get("/panel/media/{message_id}")
def view_message_media(
    message_id: Annotated[int,APIPath(ge=1,le=2147483647)],
    db: Session = Depends(get_db),
    user: dict = Depends(check_admin),
):
    """Muestra la foto/documento/audio guardado de un mensaje del buzón."""
    msg = db.query(MessageLog).filter(MessageLog.id == message_id).first()
    if msg is None or not msg.media_path:
        raise HTTPException(status_code=404, detail="Este mensaje no tiene un archivo adjunto")

    file_path = _safe_media_path(msg.media_path)
    if file_path is None or not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no está disponible en el servidor")

    return FileResponse(
        file_path,
        media_type=msg.media_mime_type or "application/octet-stream",
        filename=file_path.name if not (msg.media_mime_type or "").startswith("image/") else None,
    )


@app.post("/panel/agenda/send")
async def send_agenda_now(user: str = Depends(check_admin)):
    if not settings.DOCTOR_PHONE:
        raise HTTPException(status_code=400, detail="Configura DOCTOR_PHONE para enviar la agenda por WhatsApp.")
    await send_daily_agenda()
    return RedirectResponse("/panel", status_code=303)


from app.public import install_public
from app.security import install_security
install_public(app,templates)
install_security(app)
