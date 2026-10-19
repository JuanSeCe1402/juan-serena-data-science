import io,re
from html.parser import HTMLParser
import pytest
from pypdf import PdfReader
from app import app
from core import EXAMPLES

@pytest.fixture
def client():
    app.config.update(TESTING=True,SECRET_KEY='test-key',SESSION_COOKIE_SECURE=False)
    return app.test_client()

def token(client):return re.search(r'name="csrf_token" value="([^"]+)"',client.get('/app').text)[1]
def calculate(client,**changes):
    values=dict(EXAMPLES['lote'],csrf_token=token(client));values.update(changes)
    return client.post('/app',data=values)

@pytest.mark.parametrize('path',['/','/features','/case-study','/architecture','/app','/health','/static/img/wunsce-logo-144.webp'])
def test_routes(client,path):assert client.get(path).status_code==200

def test_main_output_and_download(client):
    html=calculate(client).text
    assert '1,335.00' in html and '934.50' in html and '400.50' in html
    pdf=client.post('/quote',data={'csrf_token':token(client),'total':'1','price':'9999999','margin':'99'})
    assert pdf.status_code==200 and pdf.mimetype=='application/pdf'
    reader=PdfReader(io.BytesIO(pdf.data)); text='\n'.join(page.extract_text() for page in reader.pages)
    assert '934.50' in text and '1,335.00' in text and '400.50' in text
    assert '9,999,999' not in text
    assert len(reader.pages)>=1 and all(page.extract_text().strip() for page in reader.pages)
    assert pdf.headers['Cache-Control']=='no-store'

def test_quote_requires_own_session(client):
    calculate(client)
    stranger=app.test_client()
    assert stranger.post('/quote',data={'csrf_token':token(stranger)}).status_code==400

@pytest.mark.parametrize('path',['/app','/quote'])
def test_csrf(client,path):assert client.post(path,data=EXAMPLES['lote']).status_code==400

def test_bad_input_retained_and_no_quote(client):
    assert calculate(client).status_code==200
    response=calculate(client,margin='100')
    assert response.status_code==422 and 'role="alert"' in response.text and 'value="100"' in response.text
    assert client.post('/quote',data={'csrf_token':token(client)}).status_code==400

def test_html_escaped_in_view_and_pdf(client):
    assert '&lt;script&gt;' in calculate(client,name='<script>alert(1)</script>').text
    pdf=client.post('/quote',data={'csrf_token':token(client)})
    text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.data)).pages)
    assert '<script>alert(1)</script>' in text

def test_name_length(client):assert calculate(client,name='x'*81).status_code==422

def test_request_size(client):
    assert client.post('/app',data=b'x'*17000,content_type='application/octet-stream').status_code==413

def test_headers_health_and_no_real_claims(client):
    r=client.get('/health');assert r.get_json()=={'status':'ok','service':'frey-web'}
    assert r.headers['X-Content-Type-Options']=='nosniff'
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert 'Back to WUNSCE' in client.get('/').text
    assert 'Ejemplo reproducible' in client.get('/').text


def test_forms_labeled_and_assets_exist(client):
    class Tags(HTMLParser):
        def __init__(self):super().__init__();self.inputs=[];self.labels=[]
        def handle_starttag(self,tag,attrs):
            d=dict(attrs)
            if tag=='input' and d.get('type')!='hidden':self.inputs.append(d.get('id'))
            if tag=='label':self.labels.append(d.get('for'))
            if tag=='img':assert 'alt' in d
            if tag in ['img','script','link']:
                path=d.get('src',d.get('href',''))
                if path.startswith('/static/'):assert client.get(path).status_code==200
    for path in ['/','/app','/features','/case-study','/architecture']:
        html=client.get(path).text;t=Tags();t.feed(html)
        assert all(i in t.labels for i in t.inputs)
        assert html.count('<h1')==1 and 'id="main-content"' in html

def test_unknown_example(client):assert client.get('/app?example=missing').status_code==404
