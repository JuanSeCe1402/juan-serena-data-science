"""Decimal arithmetic: all cost inputs refer to the whole batch, before tax."""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING

CENT=Decimal('0.01')
MAX_COST=Decimal('1000000')

def number(value,label,maximum=MAX_COST):
    text=str(value).strip()
    if not re.fullmatch(r'\d+(?:[.,]\d{1,2})?',text):
        raise ValueError(f'{label}: usa un número no negativo con hasta dos decimales, sin separadores de miles.')
    try: result=Decimal(text.replace(',','.'))
    except InvalidOperation: raise ValueError(f'{label}: número no válido.')
    if not result.is_finite() or result>maximum:
        raise ValueError(f'{label}: el valor supera el límite de la demo ({maximum}).')
    return result

def quantity_value(value):
    if not re.fullmatch(r'[0-9]{1,6}',str(value)) or not 1<=int(value)<=100000:
        raise ValueError('Cantidad: usa un entero entre 1 y 100000.')
    return int(value)

def money(value): return value.quantize(CENT,rounding=ROUND_HALF_UP)

def price_for_margin(total,margin):
    # Round up to a cent so the suggested batch price does not undershoot the target.
    return (total/(1-margin/100)).quantize(CENT,rounding=ROUND_CEILING)

def calculate_cost(material,labor,machine,energy,overhead,waste_percent,margin_percent,quantity=1):
    costs=[number(v,label) for v,label in zip([material,labor,machine,energy,overhead],['Materiales','Mano de obra','Máquina','Energía','Indirectos'])]
    quantity=quantity_value(quantity)
    waste=number(waste_percent,'Merma',Decimal('100'))
    margin=number(margin_percent,'Margen',Decimal('95'))
    base=sum(costs,Decimal('0')); waste_cost=money(base*waste/100); total=base+waste_cost
    if total<=0: raise ValueError('Introduce al menos un costo mayor que cero.')
    price=price_for_margin(total,margin)
    return dict(direct_cost=base,base_cost=base,waste_cost=waste_cost,total_cost=total,
                unit_cost=money(total/quantity),suggested_price=price,unit_price=money(price/quantity),
                profit=price-total,quantity=quantity,margin=margin,waste_percent=waste,
                effective_margin=money((price-total)/price*100))

def scenarios(total,margins=(15,20,25,30,35,40,50),quantity=1):
    total=number(total,'Costo total',Decimal('10000000'))
    if total<=0: raise ValueError('El costo total debe ser mayor que cero.')
    quantity=quantity_value(quantity)
    rows=[]
    for value in margins:
        margin=number(value,'Margen',Decimal('95')); price=price_for_margin(total,margin)
        rows.append(dict(margin=margin,price=price,unit_price=money(price/quantity),profit=price-total))
    return rows

EXAMPLES={
    'lote': dict(name='Lote demostrativo de 10 piezas',quantity='10',material='250',labor='300',machine='180',energy='40',overhead='120',waste='5',margin='30'),
    'servicio': dict(name='Servicio técnico ficticio',quantity='1',material='0',labor='600',machine='0',energy='0',overhead='100',waste='0',margin='25'),
}

def evaluate(values):
    return calculate_cost(*(values[k] for k in ['material','labor','machine','energy','overhead','waste','margin']),quantity=values['quantity'])
