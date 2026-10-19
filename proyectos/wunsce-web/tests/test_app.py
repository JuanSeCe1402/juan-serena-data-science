from html.parser import HTMLParser
from urllib.parse import urlsplit
import pytest
from app import app, PROJECTS, web_url, whatsapp_number

@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()

@pytest.mark.parametrize("path", ["/", "/services", "/projects", "/about", "/contact"] + ["/projects/" + p["slug"] for p in PROJECTS])
def test_pages(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert b"WUNSCE" in response.data
    assert client.head(path).status_code == 200

@pytest.mark.parametrize("path", ["/missing", "/projects/missing", "/static/missing.css"])
def test_not_found(client, path):
    assert client.get(path).status_code == 404


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok", "service": "wunsce-main"}


def test_services_render_items(client):
    assert "Flujos de WhatsApp" in client.get("/services").get_data(as_text=True)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {"href", "src"} and value)


def test_internal_links_and_assets(client):
    for path in ["/", "/services", "/projects", "/about", "/contact"] + ["/projects/" + p["slug"] for p in PROJECTS]:
        parser = Links()
        parser.feed(client.get(path).get_data(as_text=True))
        for url in parser.urls:
            if url.startswith("/") and not url.startswith("//"):
                assert client.get(urlsplit(url).path).status_code == 200, (path, url)


@pytest.mark.parametrize("value, expected", [(" https://example.com/demo ", "https://example.com/demo"), ("javascript:alert(1)", ""), ("//example.com", ""), ("https://[", ""), ("", ""), ("https://example.com:bad", ""), ("https://example.com:65536", ""), ("https://example.com:0", ""), ("https://user:pass@example.com", ""), ("http://localhost:8080", "http://localhost:8080")])
def test_web_urls(monkeypatch, value, expected):
    monkeypatch.setenv("NANA_URL", value)
    assert web_url("NANA_URL") == expected


@pytest.mark.parametrize("value, expected", [("+52 (55) 1234-5678", "525512345678"), ("https://wa.me/123", ""), ("123", ""), ("", "")])
def test_whatsapp(monkeypatch, value, expected):
    monkeypatch.setenv("CONTACT_WHATSAPP", value)
    assert whatsapp_number() == expected


def test_contact_config(client, monkeypatch):
    monkeypatch.setenv("CONTACT_EMAIL", "hello@example.com")
    monkeypatch.setenv("CONTACT_WHATSAPP", "+52 55 1234 5678")
    monkeypatch.setenv("GITHUB_URL", "https://github.com/example")
    html = client.get("/contact").get_data(as_text=True)
    assert 'mailto:hello@example.com' in html
    assert 'https://wa.me/525512345678' in html
    assert 'https://github.com/example' in html


def test_unsupported_method(client):
    assert client.post("/contact").status_code == 405
