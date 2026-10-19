import base64,json,re
from contextlib import contextmanager
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from sqlalchemy.orm import Session
from app import app
from app.config import settings
from app.database import make_engine
import app.agenda_pdf as pdf

@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setattr(settings,'DEMO_MODE',True)
    monkeypatch.setattr(settings,'INTEGRATIONS_ENABLED',False)
    monkeypatch.setattr(settings,'ENABLE_JOBS',False)
    monkeypatch.setattr(settings,'RUNTIME_DIR',tmp_path)
    monkeypatch.setattr(settings,'MAX_SPACES',50)
    monkeypatch.setattr(settings,'MAX_RECORDS',100)
    monkeypatch.setattr(settings,'DEMO_TTL',1800)
    monkeypatch.setattr(pdf,'AGENDA_DIR',tmp_path/'agendas')
    with TestClient(app) as c:yield c

def csrf(client,path='/demo'):
    r=client.get(path)
    match=re.search(r'name="csrf_token" value="([^"]+)"',r.text)
    if not match:match=re.search(r'name="csrf-token" content="([^"]+)"',r.text)
    return match[1]

def start(client,role='doctor'):
    r=client.post('/demo/start',data=dict(role=role,csrf_token=csrf(client)),follow_redirects=False)
    assert r.status_code==303,r.text
    return client

def post(client,path,data=None):
    return client.post(path,data=dict(data or {},csrf_token=csrf(client,'/panel')),follow_redirects=False)

def cookie_data(client):return json.loads(base64.b64decode(TimestampSigner(settings.SECRET_KEY).unsign(client.cookies['esculapio_session'])))
def db_path(client):return settings.RUNTIME_DIR/'sessions'/(cookie_data(client)['workspace']+'.sqlite3')
@contextmanager
def database(client):
    engine=make_engine('sqlite:///'+str(db_path(client)))
    try:
        with Session(engine) as db:yield db
    finally:engine.dispose()
