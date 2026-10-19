from datetime import datetime,timezone

from sqlalchemy import (
    Column, Integer, String, Date, Time, DateTime, Boolean, ForeignKey, Text, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.time_utils import local_now


class Patient(Base):
    """Un paciente identificado por su número de WhatsApp."""
    __tablename__ = "patients"
    __table_args__=(CheckConstraint("age IS NULL OR age BETWEEN 1 AND 119"),CheckConstraint("length(phone) BETWEEN 8 AND 20"),)

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    """Una cita agendada."""
    __tablename__ = "appointments"
    __table_args__=(CheckConstraint("status IN ('confirmada','cancelada','pendiente_revision','atendida','no_asistio')"),CheckConstraint("duration_minutes BETWEEN 5 AND 120"),CheckConstraint("end_time > start_time"),)

    id = Column(Integer, primary_key=True)
    version = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version}
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    appointment_type = Column(String(30), default="consulta")
    duration_minutes = Column(Integer, default=30)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="confirmada")
    far_future = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    patient = relationship("Patient", back_populates="appointments")


class ScheduleSettings(Base):
    """Configuración global del horario del consultorio."""
    __tablename__ = "schedule_settings"
    __table_args__=(CheckConstraint("consult_minutes BETWEEN 5 AND 120"),CheckConstraint("human_auto_resume_minutes BETWEEN 0 AND 240"),)

    id = Column(Integer, primary_key=True, default=1)
    work_start = Column(String(5), default="11:00")
    work_end = Column(String(5), default="13:30")
    consult_minutes = Column(Integer, default=30)
    work_days = Column(String(20), default="0,1,2,3,4")
    # Minutos de inactividad humana antes de devolver la conversación al bot.
    # 0 = nunca reactivar automáticamente.
    human_auto_resume_minutes = Column(Integer, default=0)

    # Contacto configurable que recibe alertas operativas por WhatsApp.
    alert_contact_name = Column(String(100), default="")
    alert_contact_phone = Column(String(25), default="")
    alert_whatsapp_enabled = Column(Boolean, default=False)
    alert_human_requests = Column(Boolean, default=True)
    alert_new_appointments = Column(Boolean, default=False)
    alert_cancellations = Column(Boolean, default=True)
    alert_reschedules = Column(Boolean, default=False)

    # Orden personalizado de los módulos del dashboard (JSON).
    panel_order = Column(Text, default="[]")


class DateOverride(Base):
    """Excepción de horario para una fecha concreta."""
    __tablename__ = "date_overrides"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    is_blocked = Column(Boolean, default=False)
    custom_start = Column(String(5), nullable=True)
    custom_end = Column(String(5), nullable=True)
    note = Column(String(200), nullable=True)


class ConversationState(Base):
    """Estado de la conversación de cada paciente."""
    __tablename__ = "conversation_states"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    step = Column(String(30), default="START")
    data = Column(Text, default="{}")
    # Si el doctor toma la conversación manualmente, el webhook sigue
    # guardando los mensajes pero no ejecuta respuestas automáticas.
    bot_paused = Column(Boolean, default=False)
    # Se activa cuando el propio paciente pide hablar con una persona.
    human_requested = Column(Boolean, default=False)
    human_requested_at = Column(DateTime, nullable=True)
    # Motivo de la pausa: "human_request" se puede reactivar por inactividad;
    # "manual" permanece pausado hasta que el doctor lo reactive.
    pause_reason = Column(String(30), nullable=True)
    # Se establece cuando el consultorio responde por primera vez y se renueva
    # con cada mensaje humano. Antes de esto nunca corre el auto-reinicio.
    last_human_activity_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class MessageLog(Base):
    """Historial básico para mostrar conversaciones en el panel móvil."""
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # incoming / outgoing
    text = Column(Text, default="")
    message_type = Column(String(30), default="text")
    external_id = Column(String(180), nullable=True, unique=True, index=True)
    source = Column(String(30), default="api")  # patient / api / business_app
    # Si el mensaje trae una imagen, documento o audio, se guarda una copia
    # local permanente (los enlaces de WhatsApp caducan y el paciente podría
    # borrar el mensaje de su lado).
    media_path = Column(String(300), nullable=True)
    media_mime_type = Column(String(100), nullable=True)
    # Estado reportado por Meta para mensajes salientes.
    delivery_status = Column(String(30), nullable=True, index=True)  # sent/delivered/read/failed
    status_updated_at = Column(DateTime, nullable=True)
    error_detail = Column(Text, nullable=True)
    # Solo los mensajes entrantes pendientes de revisar se marcan como no leídos.
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: local_now().replace(tzinfo=None), index=True)



class AuditLog(Base):
    """Bitácora de acciones realizadas desde el panel."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False)
    action = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: local_now().replace(tzinfo=None),
        index=True,
    )
