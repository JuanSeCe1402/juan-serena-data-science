from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def generar_nota_pdf(cliente, datos):
    archivo = f"Nota_{cliente.replace(' ', '_')}.pdf"
    c = canvas.Canvas(archivo, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 750, "🧠 Cortex Studio 3D - Nota de Cobro")

    c.setFont("Helvetica", 12)
    c.drawString(40, 720, f"Cliente: {cliente}")

    c.drawString(40, 680, f"Material: {datos['material']}")
    c.drawString(40, 660, f"Peso total: {datos['peso']} g")
    c.drawString(40, 640, f"Tiempo: {datos['horas']} h")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 600, f"Total a pagar: ${datos['precio_final']:.2f} MXN")

    c.line(40, 590, 550, 590)

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(40, 560, "Gracias por su preferencia 🙌")

    c.save()
