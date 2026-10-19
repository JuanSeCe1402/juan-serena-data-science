"""Reglas del modo humano y reactivación automática del bot."""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import ConversationState, MessageLog, ScheduleSettings
from app.time_utils import local_now


def _now_naive():
    return local_now().replace(tzinfo=None)


def get_auto_resume_minutes(db: Session) -> int:
    cfg = db.query(ScheduleSettings).first()
    value = getattr(cfg, "human_auto_resume_minutes", 30) if cfg else 30
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 30


def mark_human_request(db: Session, state: ConversationState) -> None:
    """Pausa por petición del paciente. No empieza el temporizador aún."""
    state.bot_paused = True
    state.human_requested = True
    state.human_requested_at = _now_naive()
    state.pause_reason = "human_request"
    state.last_human_activity_at = None


def mark_human_activity(db: Session, state: ConversationState) -> None:
    """Registra actividad del consultorio y reinicia el temporizador."""
    if state.bot_paused and state.pause_reason == "human_request":
        state.human_requested = False
        state.last_human_activity_at = _now_naive()


def pause_manually(state: ConversationState) -> None:
    """La pausa manual es indefinida y no usa auto-reactivación."""
    state.bot_paused = True
    state.human_requested = False
    state.pause_reason = "manual"
    state.last_human_activity_at = None


def resume_bot(state: ConversationState) -> None:
    state.bot_paused = False
    state.human_requested = False
    state.pause_reason = None
    state.last_human_activity_at = None
    state.step = "START"
    state.data = "{}"


def auto_resume_if_due(db: Session, state: ConversationState, *, add_log: bool = True) -> bool:
    """Reactiva solo pausas originadas por solicitud humana y ya atendidas."""
    if not state or not state.bot_paused or state.pause_reason != "human_request":
        return False
    # Mientras el paciente siga esperando la primera respuesta humana, no se reactiva.
    if state.human_requested or state.last_human_activity_at is None:
        return False

    minutes = get_auto_resume_minutes(db)
    if minutes <= 0:
        return False

    due_at = state.last_human_activity_at + timedelta(minutes=minutes)
    if _now_naive() < due_at:
        return False

    phone = state.phone
    resume_bot(state)
    if add_log:
        db.add(MessageLog(
            phone=phone,
            direction="system",
            text=f"🤖 Bot reactivado automáticamente tras {minutes} minutos sin actividad del consultorio.",
            message_type="system",
            source="system",
            is_read=True,
        ))
    return True


def auto_resume_due_conversations(db: Session) -> int:
    """Revisa todas las conversaciones pausadas; devuelve cuántas reactivó."""
    states = (
        db.query(ConversationState)
        .filter(ConversationState.bot_paused == True, ConversationState.pause_reason == "human_request")  # noqa: E712
        .all()
    )
    resumed = 0
    for state in states:
        if auto_resume_if_due(db, state):
            resumed += 1
    if resumed:
        db.commit()
    return resumed
