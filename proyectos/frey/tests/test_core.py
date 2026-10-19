from core import calculate_cost

def test_price():
 r=calculate_cost(100,100,0,0,0,0,20,1)
 assert r['suggested_price']>r['total_cost']
