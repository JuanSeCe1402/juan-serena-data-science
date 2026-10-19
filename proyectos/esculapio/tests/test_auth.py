import base64,json,hashlib,hmac
import pytest
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash
import app.main as main
import app.database as storage
from app import app
from app.config import settings
from app.database import make_engine
from app.security import seed_demo
from conftest import csrf,start

@pytest.fixture
def private_client(monkeypatch,tmp_path):
    monkeypatch.setattr(settings,'DEMO_MODE',False)
    monkeypatch.setattr(settings,'ENABLE_JOBS',False)
    monkeypatch.setattr(settings,'INTEGRATIONS_ENABLED',False)
    monkeypatch.setattr(settings,'ADMIN_USER','doctor-unit')
    monkeypatch.setattr(settings,'ADMIN_PASSWORD_HASH',generate_password_hash('demo-test-doctor-credential'))
    monkeypatch.setattr(settings,'ASSISTANT_USER','assistant-unit')
    monkeypatch.setattr(settings,'ASSISTANT_PASSWORD_HASH',generate_password_hash('demo-test-assistant-credential'))
    monkeypatch.setattr(settings,'RUNTIME_DIR',tmp_path)
    monkeypatch.setattr(main,'_auth_failures',{})
    path=tmp_path/'private-test.sqlite3';seed_demo(path)
    engine=make_engine('sqlite:///'+str(path))
    monkeypatch.setattr(main,'engine',engine);monkeypatch.setattr(storage,'engine',engine)
    with TestClient(app) as c:yield c
    engine.dispose()


def authorization(user,password):return {'Authorization':'Basic '+base64.b64encode((user+':'+password).encode()).decode()}

def test_private_authentication_and_role_enforcement(private_client):
    c=private_client
    assert c.get('/panel').status_code==401
    assert 'Basic' in c.get('/panel').headers['www-authenticate']
    assert c.get('/panel',headers=authorization('doctor-unit','wrong')).status_code==401
    doctor=authorization('doctor-unit','demo-test-doctor-credential')
    assistant=authorization('assistant-unit','demo-test-assistant-credential')
    assert c.get('/panel',headers=doctor).status_code==200
    assert c.get('/panel/settings',headers=doctor).status_code==200
    assert c.get('/panel/settings',headers=assistant).status_code==403
    c.headers.update(assistant)
    token=csrf(c,'/panel')
    assert c.post('/panel/patients/1/delete',data={'csrf_token':token,'confirm_delete':'ELIMINAR','role':'doctor'}).status_code==403
    assert c.get('/demo').status_code==404
    assert c.post('/panel/messages/send',data={'phone':'00000001','body':'demo'}).status_code==400


def test_login_throttle(private_client):
    for i in range(10):assert private_client.get('/panel',headers=authorization('wrong','wrong')).status_code==401
    assert private_client.get('/panel',headers=authorization('wrong','wrong')).status_code==429


def test_demo_cookie_cannot_authenticate_private_mode(client,monkeypatch):
    start(client)
    monkeypatch.setattr(settings,'DEMO_MODE',False)
    assert client.get('/panel').status_code==401


def test_private_config_weak_hash_rejected(private_client,monkeypatch):
    monkeypatch.setattr(settings,'ADMIN_PASSWORD_HASH',generate_password_hash('admin'))
    with pytest.raises(RuntimeError):main._validate_security_configuration()


def test_private_webhook_signature_batch_and_replay_without_network(private_client,monkeypatch):
    monkeypatch.setattr(settings,'INTEGRATIONS_ENABLED',True)
    monkeypatch.setattr(settings,'META_APP_SECRET','unit-test-app-secret-not-real-provider-value')
    monkeypatch.setattr(settings,'WHATSAPP_PHONE_NUMBER_ID','00000099')
    responses=[]
    async def no_network(to,body):responses.append(to);return True
    monkeypatch.setattr(main,'send_text',no_network)
    messages=[{'id':'event-demo-1','from':'00000001','type':'text','text':{'body':'hablar con humano'}},{'id':'event-demo-2','from':'00000002','type':'text','text':{'body':'hablar con humano'}}]
    payload={'entry':[{'changes':[{'field':'messages','value':{'messages':messages,'metadata':{'phone_number_id':'00000099'}}}]}]}
    raw=json.dumps(payload).encode();signature='sha256='+hmac.new(settings.META_APP_SECRET.encode(),raw,hashlib.sha256).hexdigest()
    assert private_client.post('/webhook',content=raw,headers={'Content-Type':'application/json'}).status_code==403
    headers={'Content-Type':'application/json','X-Hub-Signature-256':signature}
    first=private_client.post('/webhook',content=raw,headers=headers)
    assert first.status_code==200 and first.json()['processed']==2
    second=private_client.post('/webhook',content=raw,headers=headers)
    assert second.status_code==200 and len(responses)==2
    payload['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']='00000098'
    raw=json.dumps(payload).encode();signature='sha256='+hmac.new(settings.META_APP_SECRET.encode(),raw,hashlib.sha256).hexdigest()
    assert private_client.post('/webhook',content=raw,headers={'Content-Type':'application/json','X-Hub-Signature-256':signature}).status_code==400


def test_private_transport_success_rejection_and_timeout_are_mocked(private_client,monkeypatch):
    import asyncio,httpx
    import app.whatsapp_client as transport
    monkeypatch.setattr(settings,'INTEGRATIONS_ENABLED',True)
    monkeypatch.setattr(settings,'WHATSAPP_API_URL','https://graph.facebook.com/v99.0/demo/messages')
    monkeypatch.setattr(settings,'WHATSAPP_TOKEN','unit-test-token-not-real')
    original=httpx.AsyncClient
    requests=[]
    def provider(request):
        requests.append(request)
        assert request.headers['Authorization']=='Bearer unit-test-token-not-real'
        return httpx.Response(200,json={'messages':[{'id':'demo-outgoing-id'}]})
    monkeypatch.setattr(transport.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(provider),**kwargs))
    assert asyncio.run(transport.send_text('00000001','Demostración administrativa'))
    assert len(requests)==1
    def rejected(request):return httpx.Response(403,json={'error':'sensitive-provider-detail-must-not-be-stored'})
    monkeypatch.setattr(transport.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(rejected),**kwargs))
    assert not asyncio.run(transport.send_text('00000001','Demostración administrativa'))
    with storage.SessionLocal() as db:
        from app.models import MessageLog
        assert all('sensitive-provider-detail' not in (m.error_detail or '') for m in db.query(MessageLog))
    def timeout(request):raise httpx.ConnectError('mock failure',request=request)
    monkeypatch.setattr(transport.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(timeout),**kwargs))
    assert not asyncio.run(transport.send_text('00000001','Demostración administrativa'))


def test_low_cost_password_hash_rejected(private_client,monkeypatch):
    monkeypatch.setattr(settings,'ADMIN_PASSWORD_HASH',generate_password_hash('unit-test-only-password',method='pbkdf2:sha256:1000'))
    with pytest.raises(RuntimeError):main._validate_security_configuration()
