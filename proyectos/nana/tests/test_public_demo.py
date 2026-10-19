import io
import re
import sqlite3
import time
from html.parser import HTMLParser
import pytest
from app import app, RUNTIME_DIR
import app as module

@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setattr(module,'RUNTIME_DIR',tmp_path)
    app.config.update(TESTING=True,SECRET_KEY='test-key',SESSION_COOKIE_SECURE=False,UPLOADS_ENABLED=False,MAX_CONTENT_LENGTH=1024*1024,MAX_ROWS=2000,MAX_COLUMNS=50,JOB_TTL=1800,MAX_JOBS=100)
    return app.test_client()

def run_demo(client):
    html=client.get('/app').text
    token=re.search(r'name="csrf_token" value="([^"]+)"',html)[1]
    return client.post('/app',data={'csrf_token':token,'source':'sample'})

@pytest.mark.parametrize('path',['/','/features','/case-study','/architecture','/app','/health','/sample.csv'])
def test_routes(client,path): assert client.get(path).status_code==200

def test_complete_demo_and_session_isolation(client):
    response=run_demo(client)
    assert response.status_code==200
    assert 'DEMO-001' in response.text and 'Back to WUNSCE' in response.text
    assert 'no-store' in response.headers['Cache-Control']
    csv_url=re.search(r'href="(/download/[^"]+/csv)"',response.text)[1]
    db_url=csv_url.rsplit('/',1)[0]+'/sqlite'
    assert client.get(csv_url).status_code==200
    database=client.get(db_url)
    assert database.status_code==200 and database.data.startswith(b'SQLite format 3')
    assert app.test_client().get(csv_url).status_code==404
    assert client.get('/download/../csv').status_code==404

def test_expiration(client):
    response=run_demo(client)
    url=re.search(r'href="(/download/[^"]+/csv)"',response.text)[1]
    app.config['JOB_TTL']=-1
    assert client.get(url).status_code==404

def test_csrf_required(client):
    assert client.post('/app',data={'source':'sample'}).status_code==400
    assert client.post('/app',data={'source':'sample','csrf_token':'bad'}).status_code==400

def test_upload_disabled(client):
    html=client.get('/app').text
    token=re.search(r'name="csrf_token" value="([^"]+)"',html)[1]
    assert 'type="file"' not in html
    assert client.post('/app',data={'csrf_token':token,'file':(io.BytesIO(b'a\n1'),'data.csv')}).status_code==400

def test_request_limit(client):
    assert client.post('/app',data=b'x'*(1024*1024+1),content_type='application/octet-stream').status_code==413

def test_demo_capacity(client):
    app.config['MAX_JOBS']=0
    assert run_demo(client).status_code==503

def test_session_cooldown(client):
    assert run_demo(client).status_code==200
    assert run_demo(client).status_code==429

def test_security_headers(client):
    response=client.get('/')
    assert response.headers['X-Frame-Options']=='DENY'
    assert "form-action 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['X-Content-Type-Options']=='nosniff'
    assert '92%' not in response.text

def test_assets_and_accessibility(client):
    class Assets(HTMLParser):
        def handle_starttag(self,tag,attrs):
            d=dict(attrs)
            if tag in ('img','script','link'):
                url=d.get('src',d.get('href',''))
                if url.startswith('/static/'): assert client.get(url).status_code==200,url
                if tag=='img': assert 'alt' in d
    for path in ['/','/app','/features','/case-study','/architecture']:
        html=client.get(path).text
        Assets().feed(html)
        assert 'id="main-content"' in html
        assert html.count('<h1')==1


def test_invalid_job_ids(client):
    for job in ['..','_','a'*31,'z'*32]:
        assert client.get('/download/'+job+'/csv').status_code==404
