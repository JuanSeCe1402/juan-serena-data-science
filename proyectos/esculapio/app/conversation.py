"""Máquina de estados de la conversación con el paciente."""
import json
import re
import unicodedata
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from app.models import Patient, ConversationState, Appointment
from app.scheduler import (
    APPOINTMENT_TYPE_LABELS,
    get_available_days,
    get_slots_for_date,
    get_duration_minutes,
    book_slot,
)
from app.whatsapp_client import send_text, send_buttons
from app.config import settings
from app.time_utils import local_now, local_today

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

CANCEL_WORDS = {"cancelar"}
VIEW_QUALIFIER_WORDS = {"mis", "ver", "tengo", "veo"}
BOOKING_WORDS = {"cita", "citas", "agendar"}
GREETING_WORDS = {"hola", "buenas", "buenos"}
CHANGE_NAME_ACTION_WORDS = {"cambiar", "corregir", "editar", "actualizar"}




def _normalize_for_intent(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", (text or "").lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9ñ ]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def is_human_request(text: str) -> bool:
    """Detecta solicitudes claras para hablar con una persona/doctor/recepción."""
    t = _normalize_for_intent(text)
    if not t:
        return False

    exact_or_strong = {
        "humano", "persona", "asesor", "recepcionista",
        "atencion humana", "persona real", "operador",
    }
    if t in exact_or_strong:
        return True

    phrases = (
        "hablar con humano", "hablar con un humano", "hablar con una persona",
        "hablar con alguien", "hablar con el doctor", "hablar con la doctora",
        "quiero hablar con el doctor", "quiero hablar con la doctora",
        "quiero hablar con una persona", "comunicarme con el doctor",
        "comunicarme con la doctora", "pasame con el doctor",
        "pasame con la doctora", "atencion de una persona",
        "necesito un humano", "quiero un humano", "recepcion por favor",
    )
    return any(phrase in t for phrase in phrases)

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-záéíóúñü]+", (text or "").lower()))


def _get_or_create_patient(db: Session, phone: str) -> Patient:
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if patient is None:
        patient = Patient(phone=phone)
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient


def _get_state(db: Session, phone: str) -> ConversationState:
    state = db.query(ConversationState).filter(ConversationState.phone == phone).first()
    if state is None:
        state = ConversationState(phone=phone, step="START", data="{}")
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def _save_state(db: Session, state: ConversationState, step: str, data: dict) -> None:
    state.step = step
    state.data = json.dumps(data, default=str)
    db.commit()


def _fmt_day(d: date) -> str:
    return f"{DIAS_ES[d.weekday()]} {d.day}/{d.month}"


def _parse_custom_date(text: str) -> date | None:
    match = re.match(r"^\s*(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?\s*$", text or "")
    if not match:
        return None

    day_num, month_num, year_str = match.groups()
    try:
        day_num, month_num = int(day_num), int(month_num)
        if year_str:
            year_num = int(year_str)
            if year_num < 100:
                year_num += 2000
        else:
            year_num = local_today().year

        candidate = date(year_num, month_num, day_num)
        if not year_str and candidate < local_today():
            candidate = date(year_num + 1, month_num, day_num)
        return candidate
    except ValueError:
        return None


def _next_booking_step(patient: Patient) -> str:
    if not patient.name:
        return "ASK_NAME"
    if patient.age is None:
        return "ASK_AGE"
    return "ASK_APPOINTMENT_TYPE"


async def _send_main_menu(phone: str, patient: Patient | None = None) -> None:
    """Muestra las tres acciones principales como botones de WhatsApp."""
    saludo = f"Hola, {patient.name}" if patient and patient.name else "¡Hola!"
    await send_buttons(
        phone,
        f"{saludo} Soy el asistente del {settings.CLINIC_NAME} 🩺\n\n"
        "¿Qué deseas hacer?\n"
        "También puedes escribir *cancelar* o *cambiar nombre* cuando lo necesites.",
        buttons=[
            ("menu_book", "Agendar cita"),
            ("menu_appointments", "Mis citas"),
            ("menu_human", "Hablar con humano"),
        ],
    )


async def _ask_appointment_type(phone: str) -> None:
    await send_buttons(
        phone,
        "¿Qué tipo de cita necesitas?",
        buttons=[
            ("type_consulta", "Consulta"),
            ("type_laboratorio", "Revisar laboratorios"),
        ],
    )


async def _send_time_options(
    db: Session,
    phone: str,
    state: ConversationState,
    data: dict,
    chosen_day: date,
) -> None:
    appointment_type = data.get("appointment_type", "consulta")
    slots = get_slots_for_date(db, chosen_day, appointment_type)
    if not slots:
        await send_text(phone, "Ese día ya no tiene horarios disponibles para ese tipo de cita. Elige otra fecha.")
        _save_state(db, state, "ASK_CUSTOM_DATE", data)
        return

    data["chosen_day"] = chosen_day.isoformat()
    data["available_slots"] = [t.strftime("%H:%M") for t in slots]
    _save_state(db, state, "ASK_TIME", data)

    opciones = "\n".join(f"{i+1}. {t.strftime('%H:%M')}" for i, t in enumerate(slots))
    duration = get_duration_minutes(db, appointment_type)
    await send_text(
        phone,
        f"Horarios disponibles el {_fmt_day(chosen_day)} "
        f"({duration} min):\n{opciones}\n\n"
        "Responde con el número de la hora que prefieras.",
    )


async def handle_incoming(db: Session, phone: str, text: str, button_id: str | None) -> None:
    patient = _get_or_create_patient(db, phone)
    state = _get_state(db, phone)
    data = json.loads(state.data or "{}")
    text_lower = (text or "").strip().lower()
    tokens = _tokenize(text)

    # Comandos globales
    if CANCEL_WORDS & tokens:
        await _cancel_next(db, phone, patient)
        _save_state(db, state, "START", {})
        return

    if "citas" in tokens and (VIEW_QUALIFIER_WORDS & tokens):
        await _show_upcoming(db, phone, patient)
        return

    if "nombre" in tokens and (CHANGE_NAME_ACTION_WORDS & tokens):
        _save_state(db, state, "UPDATE_NAME", {})
        await send_text(phone, "Claro, ¿cuál es tu nombre completo correcto?")
        return

    # Menú principal: un saludo ya no inicia una cita automáticamente.
    # Así el paciente ve desde el inicio la opción visible "Hablar con humano".
    if GREETING_WORDS & tokens:
        _save_state(db, state, "START", {})
        await _send_main_menu(phone, patient)
        return

    if button_id == "menu_appointments":
        await _show_upcoming(db, phone, patient)
        return

    if button_id == "menu_book" or (BOOKING_WORDS & tokens):
        step = _next_booking_step(patient)
        data = {}
        _save_state(db, state, step, data)
        if step == "ASK_NAME":
            await send_text(
                phone,
                "Perfecto, voy a ayudarte a agendar tu cita. ¿Cuál es tu nombre completo?",
            )
        elif step == "ASK_AGE":
            await send_text(phone, f"Perfecto, {patient.name}. ¿Cuál es tu edad?")
        else:
            await _ask_appointment_type(phone)
        return

    step = state.step

    if step == "START":
        await _send_main_menu(phone, patient)
        return

    if step == "UPDATE_NAME":
        if len(text.strip()) < 3:
            await send_text(phone, "Por favor escribe tu nombre completo.")
            return
        patient.name = text.strip().title()
        db.commit()
        _save_state(db, state, "START", {})
        await send_text(phone, f"Listo, actualicé tu nombre a: {patient.name}. Escribe *cita* cuando quieras agendar.")
        return

    if step == "ASK_NAME":
        if len(text.strip()) < 3:
            await send_text(phone, "¿Podrías escribir tu nombre completo, por favor?")
            return
        patient.name = text.strip().title()
        db.commit()
        _save_state(db, state, "ASK_AGE", data)
        await send_text(phone, f"Gracias, {patient.name}. ¿Cuál es tu edad?")
        return

    if step == "ASK_AGE":
        if not text.strip().isdigit():
            await send_text(phone, "Por favor escribe tu edad solo con números (ej. 34).")
            return
        age = int(text.strip())
        if not (0 < age < 120):
            await send_text(phone, "Escribe una edad válida, por favor.")
            return
        patient.age = age
        db.commit()
        _save_state(db, state, "ASK_APPOINTMENT_TYPE", data)
        await _ask_appointment_type(phone)
        return

    if step == "ASK_APPOINTMENT_TYPE":
        appointment_type = None
        if button_id == "type_consulta" or "consulta" in tokens:
            appointment_type = "consulta"
        elif button_id == "type_laboratorio" or ({"laboratorio", "laboratorios", "examen", "exámenes", "estudio", "estudios"} & tokens):
            appointment_type = "laboratorio"

        if appointment_type is None:
            await send_text(phone, "Elige *Consulta* o *Revisar laboratorios*, por favor.")
            await _ask_appointment_type(phone)
            return

        data["appointment_type"] = appointment_type
        _save_state(db, state, "ASK_REASON", data)
        if appointment_type == "laboratorio":
            await send_text(phone, "¿Qué exámenes o estudios deseas revisar? Puedes escribir una nota breve.")
        else:
            await send_text(phone, "¿Cuál es el motivo de tu consulta?")
        return

    if step == "ASK_REASON":
        data["reason"] = text.strip()
        appointment_type = data.get("appointment_type", "consulta")
        available = get_available_days(db, appointment_type=appointment_type)
        if not available:
            await send_text(phone, "Lo siento, no hay horarios disponibles próximamente. Por favor intenta más tarde.")
            _save_state(db, state, "START", {})
            return

        data["available_days"] = [d.isoformat() for d in available.keys()]
        _save_state(db, state, "ASK_DAY", data)

        days_list = list(available.keys())[:8]
        opciones = "\n".join(f"{i+1}. {_fmt_day(d)}" for i, d in enumerate(days_list))
        await send_text(
            phone,
            f"Estos son los próximos días con horario disponible:\n{opciones}\n\n"
            "Responde con el número del día que prefieras, o escribe *otra fecha* para elegir una fecha más adelante.",
        )
        return

    if step == "ASK_DAY":
        day_tokens = _tokenize(text)
        if "otra" in day_tokens or "adelante" in day_tokens or "lejos" in day_tokens:
            _save_state(db, state, "ASK_CUSTOM_DATE", data)
            await send_text(phone, "Escribe la fecha en formato día/mes (ej. 15/12 o 15/12/2026). También puedes elegir hoy si todavía hay horario disponible.")
            return

        appointment_type = data.get("appointment_type", "consulta")
        available = get_available_days(db, appointment_type=appointment_type)
        days_list = list(available.keys())[:8]
        if not text.strip().isdigit() or not (1 <= int(text.strip()) <= len(days_list)):
            await send_text(phone, "Responde con el número de una opción o escribe *otra fecha*.")
            return

        chosen_day = days_list[int(text.strip()) - 1]
        await _send_time_options(db, phone, state, data, chosen_day)
        return

    if step == "ASK_CUSTOM_DATE":
        chosen_day = _parse_custom_date(text)
        if chosen_day is None:
            await send_text(phone, "No entendí esa fecha. Escríbela como 15/12 o 15/12/2026.")
            return

        today = local_today()
        if chosen_day < today:
            await send_text(phone, "Esa fecha ya pasó. Escribe una fecha de hoy en adelante, por favor.")
            return

        if (chosen_day - today).days > settings.MAX_BOOKING_DAYS_AHEAD:
            await send_text(phone, f"Esa fecha está demasiado lejos (máximo {settings.MAX_BOOKING_DAYS_AHEAD} días de anticipación).")
            return

        appointment_type = data.get("appointment_type", "consulta")
        slots = get_slots_for_date(db, chosen_day, appointment_type)
        if not slots:
            await send_text(phone, f"El {_fmt_day(chosen_day)} no tiene horario disponible para ese tipo de cita. Intenta con otra fecha.")
            return

        await _send_time_options(db, phone, state, data, chosen_day)
        return

    if step == "ASK_TIME":
        slots_str = data.get("available_slots", [])
        if not text.strip().isdigit() or not (1 <= int(text.strip()) <= len(slots_str)):
            await send_text(phone, "Por favor responde con el número de una de las horas disponibles.")
            return

        chosen_time_str = slots_str[int(text.strip()) - 1]
        data["chosen_time"] = chosen_time_str
        _save_state(db, state, "CONFIRM", data)

        chosen_day = date.fromisoformat(data["chosen_day"])
        appointment_type = data.get("appointment_type", "consulta")
        type_label = APPOINTMENT_TYPE_LABELS[appointment_type]
        duration = get_duration_minutes(db, appointment_type)
        await send_buttons(
            phone,
            f"Confirmo tu cita:\n\n"
            f"👤 {patient.name}\n"
            f"📋 {type_label} ({duration} min)\n"
            f"📅 {_fmt_day(chosen_day)}\n"
            f"🕐 {chosen_time_str}\n"
            f"📝 {data.get('reason') or 'Sin nota'}\n\n"
            f"Puedes cancelar por este medio hasta {settings.CANCELLATION_HOURS} horas antes.\n\n"
            "¿Confirmas?",
            buttons=[("confirm_yes", "Sí, confirmar"), ("confirm_no", "Cancelar")],
        )
        return

    if step == "CONFIRM":
        confirmed = button_id == "confirm_yes" or text_lower in ("sí", "si", "confirmar")
        if not confirmed:
            await send_text(phone, "De acuerdo, no se agendó la cita. Escribe *cita* cuando quieras intentarlo de nuevo.")
            _save_state(db, state, "START", {})
            return

        chosen_day = date.fromisoformat(data["chosen_day"])
        chosen_time = datetime.strptime(data["chosen_time"], "%H:%M").time()
        appointment_type = data.get("appointment_type", "consulta")
        appt = book_slot(
            db,
            patient.id,
            chosen_day,
            chosen_time,
            data.get("reason", ""),
            appointment_type,
        )

        if appt is None:
            await send_text(phone, "Justo se ocupó ese horario. Escribe *cita* para elegir otro, por favor.")
            _save_state(db, state, "START", {})
            return

        await send_text(
            phone,
            f"✅ Cita confirmada: {APPOINTMENT_TYPE_LABELS[appointment_type]} el "
            f"{_fmt_day(chosen_day)} a las {data['chosen_time']} con {settings.DOCTOR_NAME}.\n\n"
            "Si necesitas cancelar, escribe *cancelar*.",
        )
        _save_state(db, state, "START", {})
        return

    _save_state(db, state, "START", {})
    await _send_main_menu(phone, patient)


async def notify_doctor_cancellation(patient: Patient, appt_date: date, appt_time_str: str, reason: str = "") -> None:
    motivo = f"\n\nMotivo: {reason.strip()}" if reason and reason.strip() else ""
    await send_text(
        patient.phone,
        f"Hola {patient.name or ''} 👋\n\n"
        f"Te informamos que tu cita del {_fmt_day(appt_date)} a las {appt_time_str} "
        f"con {settings.DOCTOR_NAME} fue cancelada por el consultorio.{motivo}\n\n"
        "Escribe *cita* cuando quieras agendar una nueva fecha.",
    )


async def _show_upcoming(db: Session, phone: str, patient: Patient) -> None:
    upcoming = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.status == "confirmada",
            Appointment.date >= local_today(),
        )
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )
    if not upcoming:
        await send_text(phone, "No tienes citas próximas. Escribe *cita* para agendar una.")
        return

    lines = [
        f"- {_fmt_day(a.date)} a las {a.start_time.strftime('%H:%M')} · "
        f"{APPOINTMENT_TYPE_LABELS.get(a.appointment_type or 'consulta', 'Consulta')}"
        for a in upcoming
    ]
    await send_text(phone, "Tus próximas citas:\n" + "\n".join(lines))


async def _cancel_next(db: Session, phone: str, patient: Patient) -> None:
    next_appt = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.status == "confirmada",
            Appointment.date >= local_today(),
        )
        .order_by(Appointment.date, Appointment.start_time)
        .first()
    )
    if not next_appt:
        await send_text(phone, "No encontré ninguna cita próxima para cancelar.")
        return

    appt_datetime = datetime.combine(next_appt.date, next_appt.start_time)
    now_naive = local_now().replace(tzinfo=None)
    time_left = appt_datetime - now_naive

    if time_left < timedelta(hours=settings.CANCELLATION_HOURS):
        contacto = f" al {settings.CLINIC_PHONE}" if settings.CLINIC_PHONE else ""
        await send_text(
            phone,
            f"Tu cita es en menos de {settings.CANCELLATION_HOURS} horas, así que ya no "
            f"se puede cancelar por este medio. Por favor comunícate directamente{contacto} para avisar.",
        )
        return

    next_appt.status = "cancelada"
    db.commit()
    await send_text(phone, f"Tu cita del {_fmt_day(next_appt.date)} a las {next_appt.start_time.strftime('%H:%M')} fue cancelada.")
