import os,re,sqlite3
from html.parser import HTMLParser
from pathlib import Path
import pytest
import app as module
from app import app
from database import connect,STATUSES

@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setattr(module,'RUNTIME_DIR',tmp_path)
    app.config.update(TESTING=True,SECRET_KEY='test-key',SESSION_COOKIE_SECURE=False,DEMO_TTL=1800,MAX_SPACES=100,MAX_RECORDS=50)
    return app.test_client()

def token(client,path='/app'):
    html=client.get(path).text
    return re.search(r'name="csrf_token" value="([^"]+)"',html)[1]

def post(client,path,data=None,source='/app'):
    return client.post(path,data=dict(data or {},csrf_token=token(client,source)))

def database_path(client):
    with client.session_transaction() as s:identifier=s['space_id']
    return module.RUNTIME_DIR/(identifier+'.sqlite3')

def scalar(client,sql,parameters=()):
    con=connect(database_path(client))
    try:return con.execute(sql,parameters).fetchone()[0]
    finally:con.close()

@pytest.mark.parametrize('path',['/','/features','/case-study','/architecture','/app','/clients','/orders','/orders?stage=Quote','/inventory','/tasks','/health'])
def test_routes(client,path):assert client.get(path).status_code==200

def test_seed_is_synthetic_and_paid_is_not_delivered(client):
    html=client.get('/app').text
    assert 'ENTORNO DEMO AISLADO' in html and 'Demo Alfa' in html
    assert 'MXN 1,100.00' in html
    assert scalar(client,"SELECT SUM(amount_cents) FROM orders WHERE status='Paid'")==110000
    assert scalar(client,"SELECT SUM(amount_cents) FROM orders WHERE status='Delivered'")==65000
    assert scalar(client,'SELECT COUNT(*) FROM inventory WHERE stock<=min_stock')==2
    assert 'norte.mx' not in html and '$184K' not in html

def test_full_order_pipeline_and_stale_updates(client):
    client.get('/app')
    for before,after in zip(STATUSES,STATUSES[1:]):
        response=post(client,'/orders/1/advance',{'expected_status':before})
        assert response.status_code==302
        assert scalar(client,'SELECT status FROM orders WHERE id=1')==after
        assert post(client,'/orders/1/advance',{'expected_status':before}).status_code==409
    assert post(client,'/orders/1/advance',{'expected_status':'Paid'}).status_code==409

def test_no_pipeline_skip_on_create(client):
    response=post(client,'/orders',dict(client_id='1',description='Pedido ficticio',amount='120.50',status='Paid'))
    assert response.status_code==422
    assert scalar(client,'SELECT COUNT(*) FROM orders')==6

def test_client_order_task_stock_workflow(client):
    assert post(client,'/clients',dict(name='Demo Nuevo',email='nuevo@example.test')).status_code==302
    assert post(client,'/orders',dict(client_id='4',description='Nuevo trabajo ficticio',amount='123,45')).status_code==302
    assert scalar(client,'SELECT amount_cents FROM orders WHERE id=7')==12345
    assert scalar(client,'SELECT status FROM orders WHERE id=7')=='Lead'
    assert post(client,'/tasks',dict(title='Tarea ficticia vinculada',owner='Equipo demo A',due_date='2026-10-22',order_id='7')).status_code==302
    assert scalar(client,'SELECT order_id FROM tasks WHERE id=4')==7
    assert post(client,'/tasks/4/advance',dict(expected_status='Pending')).status_code==302
    assert post(client,'/tasks/4/advance',dict(expected_status='In Progress')).status_code==302
    assert scalar(client,'SELECT status FROM tasks WHERE id=4')=='Done'
    assert post(client,'/inventory',dict(sku='DEMO-X',name='Material ficticio',stock='5',min_stock='6')).status_code==302
    assert post(client,'/inventory/4/stock',dict(stock='10',expected_stock='5')).status_code==302
    assert scalar(client,'SELECT stock FROM inventory WHERE id=4')==10
    assert post(client,'/inventory/4/stock',dict(stock='0',expected_stock='5')).status_code==409

def test_foreign_keys_and_db_constraints(client):
    client.get('/app');con=connect(database_path(client))
    try:
        assert con.execute('PRAGMA foreign_keys').fetchone()[0]==1
        with pytest.raises(sqlite3.IntegrityError):con.execute("INSERT INTO orders(client_id,description,amount_cents,status) VALUES(999,'demo',100,'Lead')")
        con.rollback()
        with pytest.raises(sqlite3.IntegrityError):con.execute("UPDATE orders SET status='Invalid' WHERE id=1")
        con.rollback()
        with pytest.raises(sqlite3.IntegrityError):con.execute('UPDATE inventory SET stock=-1 WHERE id=1')
    finally:con.close()

@pytest.mark.parametrize('path,data',[
 ('/clients',dict(name='Real Person',email='real@example.com')),
 ('/clients',dict(name='Demo Uno',email='real@example.com')),
 ('/orders',dict(client_id='999',description='demo',amount='10')),
 ('/orders',dict(client_id='1 OR 1=1',description='demo',amount='10')),
 ('/orders',dict(client_id='1',description='',amount='10')),
 ('/orders',dict(client_id='1',description='demo',amount='-1')),
 ('/orders',dict(client_id='1',description='demo',amount='NaN')),
 ('/orders',dict(client_id='1',description='demo',amount='Infinity')),
 ('/orders',dict(client_id='1',description='demo',amount='1000000.01')),
 ('/inventory',dict(sku='not-demo',name='demo',stock='1',min_stock='0')),
 ('/inventory',dict(sku='DEMO-N',name='demo',stock='-1',min_stock='0')),
 ('/inventory',dict(sku='DEMO-N',name='demo',stock='1.5',min_stock='0')),
 ('/inventory',dict(sku='DEMO-N',name='demo',stock='1',min_stock='100001')),
 ('/tasks',dict(title='demo',owner='Real Name',due_date='',order_id='')),
 ('/tasks',dict(title='demo',owner='Equipo demo A',due_date='2026-02-30',order_id='')),
 ('/tasks',dict(title='demo',owner='Equipo demo A',due_date='',order_id='999')),
 ('/tasks',dict(title='demo',owner='Equipo demo A',due_date='',order_id='',status='Done')),
])
def test_invalid_inputs_rejected(client,path,data):
    response=post(client,path,data)
    assert response.status_code==422 and 'role="alert"' in response.text

@pytest.mark.parametrize('path',['/clients','/orders','/inventory','/tasks','/orders/1/advance','/tasks/1/advance','/inventory/1/stock','/reset-demo'])
def test_csrf_required(client,path):assert client.post(path,data={}).status_code==400

def test_session_isolation(client):
    assert post(client,'/clients',dict(name='Demo Privado',email='')).status_code==302
    assert post(client,'/orders',dict(client_id='4',description='Trabajo privado demo',amount='10')).status_code==302
    other=app.test_client();other.get('/app')
    assert 'Demo Privado' not in other.get('/clients').text
    assert database_path(client)!=database_path(other)
    assert post(other,'/orders/7/advance',dict(expected_status='Lead')).status_code==404
    assert post(other,'/orders',dict(client_id='4',description='demo',amount='10')).status_code==422
    assert scalar(client,'SELECT status FROM orders WHERE id=7')=='Lead'

def test_reset_only_own_session_and_invalidates_old_forms(client):
    other=app.test_client();other.get('/app')
    csrf=token(client)
    assert post(client,'/clients',dict(name='Demo Extra',email='')).status_code==302
    assert client.post('/reset-demo',data={'csrf_token':csrf}).status_code==302
    assert 'Demo Extra' not in client.get('/clients').text
    assert scalar(other,'SELECT COUNT(*) FROM clients')==3
    assert client.post('/orders/1/advance',data=dict(csrf_token=csrf,expected_status='Lead')).status_code==400

def test_expiration_blocks_old_post(client):
    csrf=token(client)
    with client.session_transaction() as s:s['space_started']=0
    assert client.post('/orders/1/advance',data=dict(csrf_token=csrf,expected_status='Lead')).status_code==409
    assert client.get('/app').status_code==200
    assert scalar(client,'SELECT status FROM orders WHERE id=1')=='Lead'

def test_duplicates_and_capacity(client):
    assert post(client,'/clients',dict(name='Demo Alfa',email='')).status_code==422
    assert post(client,'/inventory',dict(sku='DEMO-MAT-A',name='demo',stock='1',min_stock='0')).status_code==422
    app.config['MAX_RECORDS']=3
    assert post(client,'/clients',dict(name='Demo Extra',email='')).status_code==422

def test_global_capacity(client):
    app.config['MAX_SPACES']=0
    assert client.get('/app').status_code==503
    assert client.get('/health').status_code==200

def test_request_limit(client):assert client.post('/clients',data=b'x'*17000,content_type='application/octet-stream').status_code==413

def test_xss_and_sql_payload_stay_text(client):
    value="Demo <script>alert(1)</script> ' OR 1=1 --"
    assert post(client,'/clients',dict(name=value,email='')).status_code==302
    html=client.get('/clients').text
    assert '<script>alert(1)</script>' not in html and '&lt;script&gt;' in html
    assert scalar(client,'SELECT COUNT(*) FROM clients')==4

def test_health_headers_and_filter(client):
    response=client.get('/health')
    assert response.get_json()=={'status':'ok','service':'tikal-web'}
    assert response.headers['Cache-Control']=='no-store'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert client.get('/orders?stage=Invalid').status_code==404
    assert 'Ejemplo 2' in client.get('/orders?stage=Quote').text
    assert 'Ejemplo 1 · Lead</th>' not in client.get('/orders?stage=Quote').text

def test_labels_and_assets(client):
    class Tags(HTMLParser):
        def __init__(self):super().__init__();self.inputs=[];self.labels=[]
        def handle_starttag(self,tag,attrs):
            d=dict(attrs)
            if tag in ('input','select') and d.get('type')!='hidden':self.inputs.append(d.get('id'))
            if tag=='label':self.labels.append(d.get('for'))
            if tag=='img':assert 'alt' in d
            if tag in ('img','script','link'):
                path=d.get('src',d.get('href',''))
                if path.startswith('/static/'):assert client.get(path).status_code==200
    for path in ['/','/app','/clients','/orders','/inventory','/tasks','/features','/case-study','/architecture']:
        html=client.get(path).text;t=Tags();t.feed(html)
        assert all(i and i in t.labels for i in t.inputs),(path,t.inputs,t.labels)
        assert html.count('<h1')==1 and 'id="main-content"' in html
        assert 'Back to WUNSCE' in html
