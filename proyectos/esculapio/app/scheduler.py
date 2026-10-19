"""Cálculo de disponibilidad y reserva de citas."""
from datetime import date, datetime, timedelta, time as time_cls
from threading import Lock

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Appointment, ScheduleSettings, DateOverride
from app.config import settings as app_settings
from app.time_utils import local_now, local_today

LAB_DURATION_MINUTES = 20
APPOINTMENT_TYPE_LABELS = {
    "consulta": "Consulta",
    "laboratorio": "Chequeo de exámenes de laboratorio",
}

# Serializa reservas dentro del proceso; SQLite además usa BEGIN IMMEDIATE.
_booking_lock = Lock()


def get_or_create_settings(db: Session) -> ScheduleSettings:
    row = db.query(ScheduleSettings).first()
    if row is None:
        row = ScheduleSettings(
            id=1,
            work_start=app_settings.WORK_START,
            work_end=app_settings.WORK_END,
            consult_minutes=app_settings.CONSULT_MINUTES,
            work_days=",".join(str(d) for d in app_settings.WORK_DAYS),
            human_auto_resume_minutes=0,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _hhmm_to_time(value: str) -> time_cls:
    h, m = value.split(":")
    return time_cls(hour=int(h), minute=int(m))


def get_duration_minutes(db: Session, appointment_type: str) -> int:
    if appointment_type == "laboratorio":
        return LAB_DURATION_MINUTES
    return get_or_create_settings(db).consult_minutes


def _day_bounds(db: Session, day: date) -> tuple[datetime, datetime] | None:
    cfg = get_or_create_settings(db)
    override = db.query(DateOverride).filter(DateOverride.date == day).first()

    if override and override.is_blocked:
        return None

    work_days = [int(d) for d in cfg.work_days.split(",") if d.strip()]
    if override is None and day.weekday() not in work_days:
        return None

    start_str = override.custom_start if (override and override.custom_start) else cfg.work_start
    end_str = override.custom_end if (override and override.custom_end) else cfg.work_end
    return datetime.combine(day, _hhmm_to_time(start_str)), datetime.combine(day, _hhmm_to_time(end_str))


def _confirmed_intervals(
    db: Session,
    day: date,
    exclude_appointment_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    query = db.query(Appointment).filter(
        Appointment.date == day,
        Appointment.status == "confirmada",
    )
    if exclude_appointment_id is not None:
        query = query.filter(Appointment.id != exclude_appointment_id)
    appointments = query.order_by(Appointment.start_time).all()
    return [
        (datetime.combine(day, a.start_time), datetime.combine(day, a.end_time))
        for a in appointments
    ]


def _overlaps(start: datetime, end: datetime, occupied: list[tuple[datetime, datetime]]) -> bool:
    return any(start < busy_end and end > busy_start for busy_start, busy_end in occupied)


def is_slot_available(
    db: Session,
    day: date,
    start_t: time_cls,
    appointment_type: str = "consulta",
    exclude_appointment_id: int | None = None,
) -> bool:
    if appointment_type not in APPOINTMENT_TYPE_LABELS or day>local_today()+timedelta(days=app_settings.MAX_BOOKING_DAYS_AHEAD):return False
    bounds = _day_bounds(db, day)
    if bounds is None or start_t not in get_slots_for_date(db,day,appointment_type,exclude_appointment_id):
        return False

    day_start, day_end = bounds
    duration = timedelta(minutes=get_duration_minutes(db, appointment_type))
    start_dt = datetime.combine(day, start_t)
    end_dt = start_dt + duration

    if start_dt < day_start or end_dt > day_end:
        return False

    if day < local_today():
        return False
    if day == local_today():
        # Dejamos un pequeño margen: el inicio debe ser posterior a la hora local actual.
        now = local_now().replace(tzinfo=None)
        if start_dt <= now:
            return False

    return not _overlaps(start_dt, end_dt, _confirmed_intervals(db, day, exclude_appointment_id))


def get_slots_for_date(
    db: Session,
    day: date,
    appointment_type: str = "consulta",
    exclude_appointment_id: int | None = None,
) -> list[time_cls]:
    """
    Calcula horarios disponibles sin solapar citas de distinta duración.

    Las consultas usan la duración configurable; el chequeo de laboratorio dura
    20 minutos. Tras una cita corta, el siguiente horario puede desplazarse para
    aprovechar el hueco real de la agenda.
    """
    bounds = _day_bounds(db, day)
    if bounds is None or day < local_today() or day>local_today()+timedelta(days=app_settings.MAX_BOOKING_DAYS_AHEAD):
        return []

    day_start, day_end = bounds
    duration = timedelta(minutes=get_duration_minutes(db, appointment_type))
    occupied = _confirmed_intervals(db, day, exclude_appointment_id)

    slots: list[time_cls] = []
    current = day_start
    now_naive = local_now().replace(tzinfo=None)

    while current + duration <= day_end:
        candidate_end = current + duration
        conflicts = [iv for iv in occupied if current < iv[1] and candidate_end > iv[0]]

        if conflicts:
            # Saltamos directamente al final del último bloqueo que choque.
            current = max(iv[1] for iv in conflicts)
            continue

        if day != local_today() or current > now_naive:
            slots.append(current.time())

        # Mantiene una agenda compacta: consulta=30 min, laboratorio=20 min.
        current += duration

    return slots


def get_available_days(
    db: Session,
    days_ahead: int | None = None,
    appointment_type: str = "consulta",
) -> dict[date, list[time_cls]]:
    days_ahead = days_ahead or app_settings.DAYS_AHEAD_TO_OFFER
    result: dict[date, list[time_cls]] = {}
    today = local_today()
    for i in range(days_ahead):
        day = today + timedelta(days=i)
        slots = get_slots_for_date(db, day, appointment_type)
        if slots:
            result[day] = slots
    return result


def _begin_serialized_booking(db: Session) -> None:
    """
    Abre una transacción que serializa las reservas.

    En SQLite, BEGIN IMMEDIATE obtiene el bloqueo de escritura antes de
    comprobar disponibilidad. En motores con bloqueo de filas, bloqueamos la
    fila de configuración para serializar las operaciones de agenda.
    """
    # Asegura que la fila exista antes de tomar el bloqueo; así un primer uso
    # en una instalación nueva no libera la transacción durante la validación.
    get_or_create_settings(db)
    db.commit()
    if db.bind and db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    else:
        db.query(ScheduleSettings).with_for_update().first()


def book_slot(
    db: Session,
    patient_id: int,
    day: date,
    start_t: time_cls,
    reason: str,
    appointment_type: str = "consulta",
) -> Appointment | None:
    """Reserva de forma atómica si el intervalo completo sigue libre."""
    if appointment_type not in APPOINTMENT_TYPE_LABELS:
        return None

    with _booking_lock:
        try:
            _begin_serialized_booking(db)

            if not is_slot_available(db, day, start_t, appointment_type):
                db.rollback()
                return None

            duration_minutes = get_duration_minutes(db, appointment_type)
            end_t = (datetime.combine(day, start_t) + timedelta(minutes=duration_minutes)).time()
            days_ahead = (day - local_today()).days

            appt = Appointment(
                patient_id=patient_id,
                date=day,
                start_time=start_t,
                end_time=end_t,
                appointment_type=appointment_type,
                duration_minutes=duration_minutes,
                reason=reason,
                status="confirmada",
                far_future=days_ahead > app_settings.FAR_FUTURE_DAYS,
            )
            db.add(appt)
            db.commit()
            db.refresh(appt)
            return appt
        except (OperationalError, IntegrityError):
            db.rollback()
            return None


def reschedule_slot(
    db: Session,
    appointment_id: int,
    new_day: date,
    new_start_t: time_cls,
    expected_version: int | None = None,
) -> Appointment | None:
    """Mueve una cita confirmada sin permitir solapamientos concurrentes."""
    with _booking_lock:
        try:
            _begin_serialized_booking(db)

            appt = (
                db.query(Appointment)
                .filter(Appointment.id == appointment_id)
                .first()
            )
            if appt is None or appt.status != "confirmada" or (expected_version is not None and appt.version != expected_version):
                db.rollback()
                return None

            appointment_type = appt.appointment_type or "consulta"
            if not is_slot_available(
                db,
                new_day,
                new_start_t,
                appointment_type,
                exclude_appointment_id=appt.id,
            ):
                db.rollback()
                return None

            duration_minutes = get_duration_minutes(db, appointment_type)
            new_end_t = (
                datetime.combine(new_day, new_start_t)
                + timedelta(minutes=duration_minutes)
            ).time()

            appt.date = new_day
            appt.start_time = new_start_t
            appt.end_time = new_end_t
            appt.duration_minutes = duration_minutes
            appt.far_future = (new_day - local_today()).days > app_settings.FAR_FUTURE_DAYS

            db.commit()
            db.refresh(appt)
            return appt
        except (OperationalError, IntegrityError):
            db.rollback()
            return None
