"""Explicit configuration; demo mode cannot consume live credentials or databases."""
import os
import re
import secrets
import tempfile
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT/".env")
def flag(name,default=False):
    value=os.getenv(name,"true" if default else "false").lower()
    if value not in ("true","false"):raise RuntimeError(name+" must be true or false")
    return value=="true"

def number(name,default,low,high):
    value=int(os.getenv(name,str(default)))
    if not low<=value<=high:raise RuntimeError("Invalid "+name)
    return value

DEMO_MODE=flag("DEMO_MODE",True)
RUNTIME=Path(os.getenv("ESCULAPIO_RUNTIME_DIR",str(Path(tempfile.gettempdir())/"wunsce_esculapio"))).resolve()
if RUNTIME.is_relative_to(ROOT/"app/static"):raise RuntimeError("Runtime cannot be public")
RUNTIME.mkdir(mode=0o700,parents=True,exist_ok=True)
secret=os.getenv("SECRET_KEY","")
if (secret and len(secret)<32) or ((os.getenv("RAILWAY_ENVIRONMENT_ID") or not DEMO_MODE) and len(secret)<32):raise RuntimeError("Set a stable random SECRET_KEY of at least 32 characters")
secret=secret or secrets.token_hex(32)
live=flag("INTEGRATIONS_ENABLED")
if DEMO_MODE and live:raise RuntimeError("External integrations are forbidden in demo mode")
version=os.getenv("WHATSAPP_API_VERSION","") if live else ""
phone_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID","") if live else ""
token=os.getenv("WHATSAPP_TOKEN","") if live else ""
if live and (not re.fullmatch(r"v[0-9]{1,2}\.0",version) or not re.fullmatch(r"[0-9]{5,30}",phone_id) or not token):raise RuntimeError("Configure approved WhatsApp API version, phone ID and token")
settings=SimpleNamespace(
 DEMO_MODE=DEMO_MODE,SECRET_KEY=secret,RUNTIME_DIR=RUNTIME,INTEGRATIONS_ENABLED=live,ENABLE_JOBS=flag("ENABLE_JOBS"),ALLOW_MEDIA_DOWNLOAD=flag("ALLOW_MEDIA_DOWNLOAD"),
 DATABASE_URL=("sqlite:///"+str(RUNTIME/"demo_bootstrap.sqlite3")) if DEMO_MODE else os.getenv("DATABASE_URL","sqlite:///"+str(RUNTIME/"private.sqlite3")),
 ADMIN_USER=os.getenv("ADMIN_USER","") if not DEMO_MODE else "",ADMIN_PASSWORD_HASH=os.getenv("ADMIN_PASSWORD_HASH","") if not DEMO_MODE else "",
 ASSISTANT_USER=os.getenv("ASSISTANT_USER","") if not DEMO_MODE else "",ASSISTANT_PASSWORD_HASH=os.getenv("ASSISTANT_PASSWORD_HASH","") if not DEMO_MODE else "",
 CLINIC_NAME="Consultorio Demo · ESCULAPIO" if DEMO_MODE else os.getenv("CLINIC_NAME","Consultorio"),DOCTOR_NAME="Equipo Demo" if DEMO_MODE else os.getenv("DOCTOR_NAME","Equipo del consultorio"),
 CLINIC_PHONE="" if DEMO_MODE else os.getenv("CLINIC_PHONE",""),CLINIC_EMAIL="" if DEMO_MODE else os.getenv("CLINIC_EMAIL",""),DOCTOR_PHONE="" if DEMO_MODE else os.getenv("DOCTOR_PHONE",""),
 WHATSAPP_TOKEN=token,WHATSAPP_PHONE_NUMBER_ID=phone_id,WHATSAPP_API_VERSION=version,WHATSAPP_API_URL=f"https://graph.facebook.com/{version}/{phone_id}/messages" if live else "",
 WHATSAPP_VERIFY_TOKEN=os.getenv("WHATSAPP_VERIFY_TOKEN","") if live else "",META_APP_SECRET=os.getenv("META_APP_SECRET","") if live else "",WEBHOOK_SIGNATURE_REQUIRED=True,
 TIMEZONE=os.getenv("TIMEZONE","America/Mexico_City"),WORK_START="09:00",WORK_END="14:00",WORK_DAYS=[0,1,2,3,4],CONSULT_MINUTES=30,
 DAYS_AHEAD_TO_OFFER=14,MAX_BOOKING_DAYS_AHEAD=90,FAR_FUTURE_DAYS=30,CANCELLATION_HOURS=2,
 MEDIA_DIR=str(RUNTIME/"media"),BACKUP_DIR=str(RUNTIME/"backups"),AGENDA_DIR=str(RUNTIME/"agendas"),BACKUP_KEEP_DAYS=7,
 MAX_MEDIA_MB=5,MEDIA_ALLOWED_TYPES={"image/jpeg","image/png","application/pdf","audio/ogg"},REMINDER_HOUR=9,AGENDA_SEND_HOUR=8,BACKUP_HOUR=3,
 DEMO_TTL=1800,MAX_SPACES=50,MAX_RECORDS=100,
)
ZoneInfo(settings.TIMEZONE)
if DEMO_MODE and settings.ENABLE_JOBS:raise RuntimeError("Scheduled jobs are forbidden in public demo mode")
