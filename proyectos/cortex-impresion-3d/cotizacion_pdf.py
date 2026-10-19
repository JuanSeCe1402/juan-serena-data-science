from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generar_pdf(cliente, datos):
    carpeta = "cotizaciones"
    os.makedirs(carpeta, exist_ok=True)
    archivo = os.path.join(carpeta, f"Cotizacion_{cliente.replace(' ', '_')}.pdf")

    c = canvas.Canvas(archivo, pagesize=A4)
    width, height = A4

    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, height - 100, width=80, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 18)
    c.drawString(140, height - 60, "Cortex Studio 3D")
    c.setFont("Helvetica", 12)
    c.drawString(140, height - 80, "Cotización Profesional de Impresión 3D")

    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 60, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    c.line(40, height - 110, width - 40, height - 110)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 140, f"Cliente: {cliente}")

    c.setFont("Helvetica", 11)
    y = height - 180
    for k, v in datos.items():
        c.drawString(60, y, f"{k.capitalize().replace('_', ' ')}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")
        y -= 18

    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0.8, 0.2)
    c.drawString(60, y - 10, f"💰 Precio final sugerido: ${datos['precio_final']:.2f}")

    c.save()
