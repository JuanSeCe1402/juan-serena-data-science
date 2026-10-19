from app import app


def test_configured_phone_whatsapp_and_github(monkeypatch):
    monkeypatch.setenv('CONTACT_PHONE', '522282363264')
    monkeypatch.setenv('CONTACT_WHATSAPP', '522282363264')
    monkeypatch.setenv('GITHUB_URL', 'https://github.com/JuanSeCe1402')
    monkeypatch.delenv('CONTACT_EMAIL', raising=False)
    html = app.test_client().get('/contact').text
    assert 'href="tel:+522282363264"' in html
    assert '+52 228 236 3264' in html
    assert 'href="https://wa.me/522282363264"' in html
    assert 'href="https://github.com/JuanSeCe1402"' in html
    assert 'mailto:' not in html
    assert 'próximamente' not in html
    assert 'tel:+522282363264' in app.test_client().get('/').text


def test_unsafe_phone_is_not_rendered(monkeypatch):
    monkeypatch.setenv('CONTACT_PHONE', 'javascript:alert(1)')
    html = app.test_client().get('/contact').text
    assert 'tel:+' not in html
    assert 'javascript:' not in html
