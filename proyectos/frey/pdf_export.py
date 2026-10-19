import io
from decimal import Decimal
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from core import evaluate,scenarios


def amount(value): return f'MXN {value:,.2f}'

def build_quote(values):
    """Recompute from validated inputs; no browser-supplied totals or price."""
    result=evaluate(values)
    out=io.BytesIO()
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='FreyTitle',parent=styles['Heading1'],textColor=colors.HexColor('#3e4228'),fontSize=22,leading=27))
    styles['BodyText'].leading=15
    styles['BodyText'].spaceAfter=9
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42,title='FREY - Escenario demostrativo',author='WUNSCE Analytics & Environments')
    story=[Paragraph('WUNSCE / FREY',styles['FreyTitle']),Paragraph('Escenario de costos y precio · Ejemplo hipotético',styles['Heading2']),
           Paragraph(escape(values['name']),styles['Heading2']),
           Paragraph('No es una oferta comercial ni un resultado de cliente. Moneda de referencia: MXN. Importes del lote, sin impuestos ni descuentos.',styles['BodyText'])]
    def table(rows,widths):
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#3e4228')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#B8BAAA')),('VALIGN',(0,0),(-1,-1),'TOP')]))
        return t
    rows=[['Concepto','Valor'],['Cantidad de unidades',str(result['quantity'])]]
    for label,key in [('Materiales','material'),('Mano de obra','labor'),('Máquina','machine'),('Energía','energy'),('Indirectos','overhead')]:
        rows.append([label,amount(Decimal(values[key]))])
    rows += [['Costo base',amount(result['base_cost'])],['Merma ('+str(result['waste_percent'])+'%)',amount(result['waste_cost'])],['Costo total del lote',amount(result['total_cost'])],['Costo unitario aproximado',amount(result['unit_cost'])],['Margen objetivo sobre venta',str(result['margin'])+'%'],['Precio sugerido del lote',amount(result['suggested_price'])],['Precio unitario de referencia',amount(result['unit_price'])],['Utilidad bruta estimada del lote',amount(result['profit'])]]
    story+=[table(rows,[290,220]),PageBreak(),Paragraph('Comparar márgenes',styles['Heading2'])]
    comparison=[['Objetivo','Precio del lote','Utilidad del lote']]
    comparison += [[str(r['margin'])+'%',amount(r['price']),amount(r['profit'])] for r in scenarios(result['total_cost'],quantity=result['quantity'])]
    story += [table(comparison,[100,205,205]),Spacer(1,14),Paragraph('Fórmulas: costo total = costo base + merma; costo unitario = costo total / cantidad; precio del lote = costo total / (1 - margen / 100); utilidad = precio del lote - costo total.',styles['BodyText']),Paragraph('El margen es proporción del precio de venta, no un recargo sobre costo. Precio del lote redondeado hacia arriba al centavo para cubrir el margen objetivo. Importes unitarios redondeados por separado: multiplicarlos puede producir diferencias de centavos. Este modelo no comprueba que se hayan incluido todos los costos.',styles['BodyText'])]
    def footer(c,d):
        c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#3e4228'));c.drawString(42,24,'FREY · WUNSCE · Demo con valores hipotéticos');c.drawRightString(A4[0]-42,24,f'Página {d.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    out.seek(0)
    return out
