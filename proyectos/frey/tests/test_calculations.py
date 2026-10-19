from decimal import Decimal
import pytest
from core import calculate_cost,scenarios,evaluate,EXAMPLES

def test_exact_example():
    r=evaluate(EXAMPLES['lote'])
    assert r['total_cost']==Decimal('934.50')
    assert r['unit_cost']==Decimal('93.45')
    assert r['suggested_price']==Decimal('1335.00')
    assert r['profit']==Decimal('400.50')
    assert r['unit_price']==Decimal('133.50')

def test_margin_is_not_markup():
    r=calculate_cost(100,0,0,0,0,0,20,1)
    assert r['suggested_price']==Decimal('125.00')
    assert r['profit']==Decimal('25.00')

def test_quantity_distributes_not_multiplies():
    one=calculate_cost(100,0,0,0,0,0,20,1)
    ten=calculate_cost(100,0,0,0,0,0,20,10)
    assert one['total_cost']==ten['total_cost']
    assert ten['unit_cost']==Decimal('10.00')

@pytest.mark.parametrize('field,value',[(0,-1),(0,'NaN'),(0,'Infinity'),(0,'1e20'),(0,'1,234.56'),(0,'1.234'),(0,'1000000.01'),(5,-1),(5,101),(6,-1),(6,100),(6,96),(7,0),(7,-1),(7,1.5),(7,100001)])
def test_invalid_inputs_rejected(field,value):
    args=[100,0,0,0,0,0,30,1];args[field]=value
    with pytest.raises(ValueError):calculate_cost(*args)

def test_zero_cost_rejected():
    with pytest.raises(ValueError):calculate_cost(0,0,0,0,0,0,30)

def test_decimal_comma_and_rounding():
    r=calculate_cost('0,10','0,20',0,0,0,5,0,1)
    assert r['waste_cost']==Decimal('0.02')
    assert r['total_cost']==Decimal('0.32')

@pytest.mark.parametrize('margin',['0','15','30','95'])
def test_price_covers_target_after_rounding(margin):
    r=calculate_cost('0.01',0,0,0,0,0,margin,3)
    actual=r['profit']/r['suggested_price']*100
    assert actual>=Decimal(margin)


def test_scenario_totals_match_core():
    base=evaluate(EXAMPLES['lote'])
    for row in scenarios(base['total_cost'],quantity=10):
        result=calculate_cost(base['total_cost'],0,0,0,0,0,row['margin'],10)
        assert row['price']==result['suggested_price']
        assert row['profit']==result['profit']

@pytest.mark.parametrize('margin',[-1,100,'NaN'])
def test_scenario_margins_validated(margin):
    with pytest.raises(ValueError):scenarios(100,[margin])
