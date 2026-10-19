"""
Tareas que corren solas, sin que nadie las tenga que ejecutar a mano:

  1. send_reminders()        -> manda un WhatsApp un día antes de cada cita.
  2. flag_past_appointments() -> las citas de días ya pasados que se quedaron
                                  como "confirmada" pasan a "pendiente_revision"
                                  para que el doctor diga, con un clic en el
                                  panel, si el paciente sí llegó o no.
  3. backup_database()        -> copia el archivo de la base de datos a una
                                  carpeta de respaldos y borra los respaldos
                                  más viejos que BACKUP_KEEP_DAYS.

Las tres se programan con APScheduler cuando arranca la aplicación
(ver app/main.py), así que mientras el servidor esté corriendo, se
ejecutan solas todos los días a la hora configurada en el .env.
"""
import shutil
import sqlite3
from datetime import date, timedelta, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import SessionLocal
from app.models import Appointment
from app.whatsapp_client import send_text, send_document, upload_media
from app.agenda_pdf import build_agenda_pdf
from app.time_utils import local_today
from app.human_mode import auto_resume_due_conversations

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fmt_day(d: date) -> str:
    return f"{DIAS_ES[d.weekday()]} {d.day}/{d.month}"


async def send_reminders() -> None:
    """Manda un recordatorio a quienes tienen cita mañana."""
    db = SessionLocal()
    try:
        tomorrow = local_today() + timedelta(days=1)
        appts = (
            db.query(Appointment)
            .filter(Appointment.date == tomorrow, Appointment.status == "confirmada")
            .all()
        )
        for a in appts:
            patient = a.patient
            await send_text(
                patient.phone,
                f"Hola {patient.name or ''} 👋 Te recordamos tu cita mañana "
                f"{_fmt_day(a.date)} a las {a.start_time.strftime('%H:%M')} "
                f"con {settings.DOCTOR_NAME}.\n\n"
                f"Si ya no puedes asistir, escribe *cancelar* (hasta "
                f"{settings.CANCELLATION_HOURS} horas antes).",
            )
    finally:
        db.close()


async def send_daily_agenda() -> None:
    """
    Genera el PDF de la agenda de hoy y se lo manda por WhatsApp a la
    doctor, si configuró su número en DOCTOR_PHONE.
    """
    if not settings.DOCTOR_PHONE:
        return  # no hay a quién mandarle la agenda

    db = SessionLocal()
    try:
        today = local_today()
        pdf_path = build_agenda_pdf(db, today)

        total = (
            db.query(Appointment)
            .filter(Appointment.date == today, Appointment.status.in_(["confirmada", "pendiente_revision"]))
            .count()
        )

        media_id = await upload_media(str(pdf_path))
        if media_id is None:
            await send_text(
                settings.DOCTOR_PHONE,
                "No se pudo generar el envío automático de la agenda de hoy por un error técnico. "
                "Puedes descargarla desde el panel.",
            )
            return

        await send_document(
            settings.DOCTOR_PHONE,
            media_id,
            filename=pdf_path.name,
            caption=f"Agenda de hoy ({total} cita{'s' if total != 1 else ''}) — {_fmt_day(today)}",
        )
    finally:
        db.close()


def flag_past_appointments() -> None:
    """
    Las citas de fechas ya pasadas que nadie marcó como cancelada quedan
    como 'pendiente_revision' para que el doctor confirme desde el panel
    si el paciente asistió o no. Así queda un registro de inasistencias.
    """
    db = SessionLocal()
    try:
        today = local_today()
        pendientes = (
            db.query(Appointment)
            .filter(Appointment.date < today, Appointment.status == "confirmada")
            .all()
        )
        for a in pendientes:
            a.status = "pendiente_revision"
        db.commit()
    finally:
        db.close()


def backup_database() -> None:
    """
    Respalda SQLite y una copia comprimida de los adjuntos.
    En SQLite se usa la API de backup para obtener una copia consistente
    incluso si la aplicación está atendiendo solicitudes.
    """
    if "sqlite" not in settings.DATABASE_URL:
        return

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    src = Path(db_path)
    if not src.exists():
        return

    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    db_dest = backup_dir / f"consultorio_{stamp}.db"

    source_conn = sqlite3.connect(str(src))
    dest_conn = sqlite3.connect(str(db_dest))
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    media_dir = Path(settings.MEDIA_DIR)
    if media_dir.exists() and any(media_dir.iterdir()):
        archive_base = backup_dir / f"media_{stamp}"
        shutil.make_archive(str(archive_base), "zip", root_dir=str(media_dir))

    limit = datetime.now() - timedelta(days=settings.BACKUP_KEEP_DAYS)

    for f in backup_dir.glob("consultorio_*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < limit:
            f.unlink(missing_ok=True)

    for f in backup_dir.glob("media_*.zip"):
        if datetime.fromtimestamp(f.stat().st_mtime) < limit:
            f.unlink(missing_ok=True)



def auto_resume_human_chats() -> None:
    """Reactiva chats atendidos por humano después del tiempo configurado."""
    db = SessionLocal()
    try:
        auto_resume_due_conversations(db)
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    """Registra y arranca las tareas programadas. Se llama una vez al iniciar la app."""
    tz = ZoneInfo(settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        send_reminders, "cron", hour=settings.REMINDER_HOUR, minute=0, id="reminders"
    )
    scheduler.add_job(
        send_daily_agenda, "cron", hour=settings.AGENDA_SEND_HOUR, minute=0, id="daily_agenda"
    )
    scheduler.add_job(
        flag_past_appointments, "cron", hour=settings.BACKUP_HOUR, minute=0, id="flag_past"
    )
    scheduler.add_job(
        backup_database, "cron", hour=settings.BACKUP_HOUR, minute=5, id="backup"
    )
    # Revisión frecuente y liviana; solo toca conversaciones en modo humano.
    scheduler.add_job(
        auto_resume_human_chats, "interval", minutes=1, id="auto_resume_human_chats", max_instances=1
    )
    scheduler.start()
    return scheduler
