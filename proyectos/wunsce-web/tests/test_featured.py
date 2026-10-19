import pytest
from app import app

FIELDS = {
    'NAME': 'Demo de prueba', 'FUNCTION': 'Organización de pedidos',
    'STATUS': 'Demo', 'SCREENSHOT': 'img/featured/demo.webp',
    'SCREENSHOT_ALT': 'Pantalla de pedidos de la demo',
    'PROBLEM': 'Información dispersa.', 'SOLUTION': 'Un espacio para organizarla.',
    'CTA_LABEL': 'Abrir demo', 'CTA_URL': 'https://example.com/demo',
}

@pytest.fixture
def configured(monkeypatch, tmp_path):
    for name, value in FIELDS.items():
        monkeypatch.setenv('FEATURED_PROJECT_' + name, value)
    static = tmp_path / 'static'
    image = static / 'img' / 'featured' / 'demo.webp'
    image.parent.mkdir(parents=True)
    image.write_bytes(b'test fixture')
    monkeypatch.setattr(app, 'static_folder', str(static))
    return app.test_client()


def test_empty_featured_is_hidden(monkeypatch):
    for name in FIELDS:
        monkeypatch.delenv('FEATURED_PROJECT_' + name, raising=False)
    assert 'featured-project-title' not in app.test_client().get('/').text


def test_complete_featured_has_demo_and_no_results(configured):
    html = configured.get('/').text
    assert 'id="featured-project-title"' in html
    assert 'href="https://example.com/demo"' in html
    assert 'src="/static/img/featured/demo.webp"' in html
    assert 'Pantalla de pedidos de la demo' in html
    assert 'El problema' in html and 'La solución' in html
    assert 'featured-results' not in html

@pytest.mark.parametrize('field,value', [
    ('PROBLEM', ''), ('CTA_URL', 'javascript:alert(1)'),
    ('SCREENSHOT', '../private.webp'), ('SCREENSHOT', 'img/missing.webp'),
])
def test_incomplete_or_unsafe_featured_is_hidden(configured, monkeypatch, field, value):
    monkeypatch.setenv('FEATURED_PROJECT_' + field, value)
    assert 'featured-project-title' not in configured.get('/').text


def test_featured_text_is_escaped(configured, monkeypatch):
    monkeypatch.setenv('FEATURED_PROJECT_NAME', '<script>alert(1)</script>')
    html = configured.get('/').text
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
