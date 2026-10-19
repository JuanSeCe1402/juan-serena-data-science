import re
from datetime import date
from decimal import Decimal,InvalidOperation

class ValidationError(ValueError): pass

def text(value,label,maximum=100):
    value=str(value).strip()
    if not value or len(value)>maximum or any(ord(c)<32 for c in value):
        raise ValidationError(f'{label}: escribe entre 1 y {maximum} caracteres, sin saltos de línea.')
    return value

def integer(value,label,minimum=0,maximum=100000):
    if not re.fullmatch(r'[0-9]{1,6}',str(value)) or not minimum<=int(value)<=maximum:
        raise ValidationError(f'{label}: usa un entero entre {minimum} y {maximum}.')
    return int(value)

def cents(value):
    value=str(value).strip()
    if not re.fullmatch(r'\d+(?:[.,]\d{1,2})?',value):
        raise ValidationError('Importe: usa hasta dos decimales, sin signos ni separadores de miles.')
    amount=Decimal(value.replace(',','.'))
    if amount>Decimal('1000000'):
        raise ValidationError('Importe: máximo MXN 1,000,000 por pedido demo.')
    return int(amount*100)

def demo_client(value):
    value=text(value,'Nombre demo',60)
    if not value.lower().startswith('demo '):
        raise ValidationError('El nombre ficticio del cliente debe comenzar con «Demo ».')
    return value

def demo_email(value):
    value=str(value).strip().lower()
    if value and (len(value)>100 or not re.fullmatch(r'[a-z0-9._+-]+@[a-z0-9.-]+\.test',value)):
        raise ValidationError('Usa únicamente un correo ficticio terminado en .test, o deja el campo vacío.')
    return value

def sku(value):
    value=str(value).strip().upper()
    if not re.fullmatch(r'DEMO-[A-Z0-9-]{1,24}',value):
        raise ValidationError('El SKU debe comenzar con DEMO- y usar letras, números o guiones (máximo 29 caracteres).')
    return value

def due_date(value):
    value=str(value).strip()
    if not value:return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValidationError('Fecha: usa AAAA-MM-DD.')
    try: result=date.fromisoformat(value)
    except ValueError:raise ValidationError('La fecha no es válida.')
    if not 2000<=result.year<=2100:raise ValidationError('Fecha: usa un año entre 2000 y 2100.')
    return result.isoformat()
