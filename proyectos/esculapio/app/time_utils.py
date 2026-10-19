from datetime import datetime, date
from zoneinfo import ZoneInfo

from app.config import settings


def local_now() -> datetime:
    """Hora actual del consultorio, independiente de la zona horaria del servidor."""
    return datetime.now(ZoneInfo(settings.TIMEZONE))


def local_today() -> date:
    """Fecha actual del consultorio, independiente de la zona horaria del servidor."""
    return local_now().date()
