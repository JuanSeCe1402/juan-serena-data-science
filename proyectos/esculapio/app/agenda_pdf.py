"""
Genera un PDF con la agenda de citas de un día, para que el doctor
lo pueda descargar desde el panel o recibirlo por WhatsApp cada mañana.
"""
from datetime import date
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Appointment
from app.scheduler import APPOINTMENT_TYPE_LABELS

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

TEAL = colors.HexColor("#2F6F62")
TEAL_PALE = colors.HexColor("#E1EDE9")
INK = colors.HexColor("#1E2A28")
MUTED = colors.HexColor("#64756F")

AGENDA_DIR = Path(settings.AGENDA_DIR)


def _fmt_day_largo(d: date) -> str:
    return f"{DIAS_ES[d.weekday()]} {d.day} de {MESES_ES[d.month]} de {d.year}"


def build_agenda_pdf(db: Session, day: date) -> Path:
    """
    Crea (o sobreescribe) el PDF de la agenda del día indicado y regresa
    la ruta del archivo.
    """
    AGENDA_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=AGENDA_DIR,suffix='.pdf',prefix='demo_' if settings.DEMO_MODE else 'agenda_',delete=False) as temporary:
        path=Path(temporary.name)

    appointments = (
        db.query(Appointment)
        .filter(Appointment.date == day, Appointment.status.in_(["confirmada", "pendiente_revision"]))
        .order_by(Appointment.start_time)
        .all()
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleTeal", parent=styles["Title"], textColor=TEAL, fontSize=18, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleMuted", parent=styles["Normal"], textColor=MUTED, fontSize=11, spaceAfter=14,
    )
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=10, textColor=INK)

    doc = SimpleDocTemplate(
        str(path), pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = [
        Paragraph(escape(settings.CLINIC_NAME), title_style),
        Paragraph(f"Agenda del {_fmt_day_largo(day)} — {escape(settings.DOCTOR_NAME)}", subtitle_style),
    ]

    if settings.DEMO_MODE:
        story.append(Paragraph("DEMO - SOLO DATOS FICTICIOS - SIN INFORMACION CLINICA", cell_style))
        story.append(Spacer(1,10))
    if not appointments:
        story.append(Paragraph("No hay citas agendadas para este día.", cell_style))
    else:
        header = ["Hora", "Tipo", "Paciente", "Edad", "ID demo" if settings.DEMO_MODE else "Teléfono", "Nota administrativa" if settings.DEMO_MODE else "Motivo"]
        rows = [header]
        for a in appointments:
            rows.append([
                f"{a.start_time.strftime('%H:%M')}-{a.end_time.strftime('%H:%M')}",
                Paragraph(APPOINTMENT_TYPE_LABELS.get(a.appointment_type or "consulta", "Consulta"), cell_style),
                Paragraph(escape(a.patient.name or "-"), cell_style),
                str(a.patient.age) if a.patient.age else "—",
                a.patient.phone,
                Paragraph(escape(a.reason or "-"), cell_style),
            ])

        table = Table(rows, colWidths=[2.6 * cm, 3.4 * cm, 3.5 * cm, 1.2 * cm, 2.8 * cm, 3.8 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TEAL_PALE]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE4E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))
        story.append(Paragraph(f"Total de citas: {len(appointments)}", subtitle_style))

    doc.build(story)
    return path
