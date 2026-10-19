import csv
import io
import json
import re
import threading
import time
from html.parser import HTMLParser
import pytest
import app as module
from app import app


@pytest.fixture
def client(monkeypatch,tmp_path):
    monkeypatch.setattr(module,"RUNTIME_DIR",tmp_path)
    monkeypatch.setattr(module,"TRAIN_LOCK",threading.Lock())
    monkeypatch.setattr(module,"LAST_TRAIN",0.0)
    app.config.update(TESTING=True,SECRET_KEY="test-key",SESSION_COOKIE_SECURE=False,RESULT_TTL=1800,MAX_RESULTS=100,TRAIN_COOLDOWN=0,MIN_TRAIN_INTERVAL=0)
    return app.test_client()


def token(client):
    return re.search(r'name="csrf_token" value="([^"]+)"',client.get('/app').text)[1]


def post(client,path='/app',data=None):
    return client.post(path,data=dict(data or {},csrf_token=token(client)))


def run(client,**kwargs):
    data=dict(n='500',seed='42',model='logistic');data.update(kwargs)
    return post(client,data=data)


def report_path(client):
    with client.session_transaction() as s:identifier=s['result_id']
    return module.RUNTIME_DIR/(identifier+'.json')


@pytest.mark.parametrize('path',['/','/features','/case-study','/architecture','/app','/health'])
def test_public_routes(client,path):assert client.get(path).status_code==200


def test_no_static_metrics_and_no_training_on_get(client):
    assert '84%' not in client.get('/').text
    assert 'métricas aparecerán' in client.get('/app').text
    assert not list(module.RUNTIME_DIR.glob('*.json'))


@pytest.mark.parametrize('path',['/app','/download','/download-input','/reset-demo'])
def test_all_mutations_require_csrf(client,path):assert client.post(path).status_code==400


@pytest.mark.parametrize('data',[dict(n='-1'),dict(n='499'),dict(n='3001'),dict(n='NaN'),dict(n='1.5'),dict(n='999999999'),dict(seed='-1'),dict(seed='1000000'),dict(seed='NaN'),dict(model='<script>alert(1)</script>')])
def test_invalid_options_preserve_form_and_show_error(client,data):
    assert run(client,**data).status_code==422
    assert not list(module.RUNTIME_DIR.glob('*.json'))


def test_full_web_experiment_and_trusted_downloads(client):
    assert run(client).status_code==302
    html=client.get('/app').text
    assert 'Regresión logística' in html and 'ROC-AUC' in html and '125' in html
    assert 'Accuracy de referencia' in html and 'SOLO DATOS SINTÉTICOS' in html
    result=json.loads(report_path(client).read_text(encoding='utf8'))
    response=post(client,'/download',{'csv':'=HYPERLINK("evil")'})
    assert response.status_code==200 and 'attachment' in response.headers['Content-Disposition']
    rows=list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig'))))
    assert len(rows)==result['test_count']==125
    assert all(r['customer_id'].startswith('DEMO-') and r['data_source']=='synthetic_demo' for r in rows)
    assert b'HYPERLINK' not in response.data
    assert set(r['customer_id'] for r in rows).isdisjoint(result['train_ids'])
    source=post(client,'/download-input')
    inputs=list(csv.DictReader(io.StringIO(source.data.decode('utf-8-sig'))))
    assert len(inputs)==505 and all(r['data_source']=='synthetic_demo' for r in inputs)
    assert client.get('/app?segment=High').status_code==200
    assert client.get('/app?segment=Invalid').status_code==404
    assert client.get('/download').status_code==405


def test_isolation_reset_and_old_csrf_invalidated(client):
    run(client)
    other=app.test_client()
    assert post(other,'/download').status_code==410
    run(other,seed='7')
    own=report_path(client);other_path=report_path(other)
    assert own!=other_path
    csrf=token(client)
    assert client.post('/reset-demo',data={'csrf_token':csrf}).status_code==302
    assert not own.exists() and other_path.exists()
    assert post(other,'/download').status_code==200
    assert client.post('/app',data=dict(csrf_token=csrf,n='500',seed='42',model='logistic')).status_code==400


def test_expiration_returns_gone_and_no_result(client,monkeypatch):
    run(client)
    path=report_path(client)
    import os
    os.utime(path,(time.time()-1900,time.time()-1900))
    assert post(client,'/download').status_code==410
    assert not path.exists()
    assert 'métricas aparecerán' in client.get('/app').text


def test_repeat_reuses_result_without_training(client,monkeypatch):
    run(client)
    path=report_path(client)
    def fail(_):raise AssertionError('Unexpected training')
    monkeypatch.setattr(module,'run_experiment',fail)
    assert run(client).status_code==302 and report_path(client)==path


def test_per_session_and_global_cooldown(client):
    run(client)
    app.config['TRAIN_COOLDOWN']=10
    assert run(client,seed='7').status_code==429
    app.config['TRAIN_COOLDOWN']=0
    app.config['MIN_TRAIN_INTERVAL']=10
    assert run(client,seed='7').status_code==429
    assert not module.TRAIN_LOCK.locked()


def test_training_lock_and_storage_capacity(client):
    module.TRAIN_LOCK.acquire()
    try:assert run(client).status_code==503
    finally:module.TRAIN_LOCK.release()
    app.config['MAX_RESULTS']=0
    assert run(client).status_code==503
    assert not module.TRAIN_LOCK.locked()
    assert client.get('/health').status_code==200


def test_training_error_releases_lock(client,monkeypatch):
    def fail(_):raise RuntimeError('test failure')
    monkeypatch.setattr(module,'run_experiment',fail)
    with pytest.raises(RuntimeError):run(client)
    assert not module.TRAIN_LOCK.locked()


def test_request_size_headers_and_escaping(client):
    assert client.post('/app',data=b'x'*5000,content_type='application/octet-stream').status_code==413
    response=run(client,model='<script>alert(1)</script>')
    assert '<script>alert(1)</script>' not in response.text
    assert response.headers['Cache-Control']=='no-store'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert client.get('/app').headers['X-Robots-Tag']=='noindex, nofollow'
    assert 'no-store' in client.get('/health').headers['Cache-Control']


def test_health_checks_writable_runtime(client,monkeypatch,tmp_path):
    path=tmp_path/'missing'/'nested'
    monkeypatch.setattr(module,'RUNTIME_DIR',path)
    response=client.get('/health')
    assert response.status_code==503 and response.json['status']=='unavailable'


class Tags(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))


def test_template_forms_assets_and_accessibility_contract(client):
    run(client)
    for path in ('/','/app','/features','/case-study','/architecture','/missing'):
        html=client.get(path).text;p=Tags();p.feed(html)
        assert 'Back to WUNSCE' in html and 'lang="es"' in html
        assert 'TIKAL' not in html
        assert len([1 for tag,a in p.tags if tag=='h1'])==1
        ids=[a.get('id') for _,a in p.tags if 'id' in a]
        assert len(ids)==len(set(ids))
        labels={a.get('for') for tag,a in p.tags if tag=='label'}
        for tag,a in p.tags:
            if tag in ('input','select') and a.get('type')!='hidden':assert a.get('id') in labels
            if tag=='th':assert a.get('scope') in ('col','row')
            if tag in ('script','img'):
                url=a.get('src')
                if url and url.startswith('/static/'):assert client.get(url).status_code==200
                if tag=='img':assert 'alt' in a and 'width' in a and 'height' in a
