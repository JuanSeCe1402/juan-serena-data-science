import json
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
import pytest
from app import app, PAGE_META, PROJECTS

class Head(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta, self.links = {}, {}
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta": self.meta[a.get("name", a.get("property"))] = a.get("content")
        if tag == "link": self.links[a.get("rel")] = a.get("href")

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://wunsce.example")
    app.config.update(TESTING=True)
    return app.test_client()

@pytest.mark.parametrize("path", ["/", "/services", "/projects", "/about", "/contact"] + ["/projects/" + p["slug"] for p in PROJECTS])
def test_metadata(client, path):
    html = client.get(path + "?utm_source=test").get_data(as_text=True)
    h = Head(html)
    assert h.links["canonical"] == "https://wunsce.example" + path
    assert h.meta["og:url"] == h.links["canonical"]
    assert h.meta["description"] == h.meta["og:description"]
    assert h.meta["og:title"] == h.meta["twitter:title"]
    assert h.meta["twitter:card"] == "summary_large_image"
    assert h.meta["og:image"] == "https://wunsce.example/static/img/og-wunsce.png"
    assert 'id="main-content"' in html
    assert html.count("<h1") == 1
    schema = html.split('<script type="application/ld+json">')[1].split('</script>')[0]
    assert json.loads(schema)["@graph"][0]["url"] == "https://wunsce.example/"


def test_unique_descriptions(client):
    pages = ["/", "/services", "/projects", "/about", "/contact"] + ["/projects/" + p["slug"] for p in PROJECTS]
    assert len({Head(client.get(p).get_data(as_text=True)).meta["description"] for p in pages}) == len(pages)


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.mimetype == "application/xml"
    root = ET.fromstring(response.data)
    urls = [el.text for el in root.findall("{*}url/{*}loc")]
    assert len(urls) == 11 and len(set(urls)) == 11
    assert all(url.startswith("https://wunsce.example/") for url in urls)
    for url in urls: assert client.get(url).status_code == 200
    assert not any("health" in url for url in urls)


def test_robots(client):
    r = client.get("/robots.txt")
    assert r.mimetype == "text/plain"
    assert "Sitemap: https://wunsce.example/sitemap.xml" in r.text
    assert "Disallow: /health" in r.text


@pytest.mark.parametrize("path", ["/missing", "/projects/missing"])
def test_error_seo(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert "noindex" in r.headers["X-Robots-Tag"]
    h = Head(r.text)
    assert "canonical" not in h.links
    assert "noindex" in h.meta["robots"]
    assert "Explorar proyectos" in r.text


@pytest.mark.parametrize("path", ["/favicon.ico", "/static/img/favicon-192.png", "/static/img/apple-touch-icon.png", "/static/img/og-wunsce.png"])
def test_brand_assets(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.mimetype.startswith("image/")


def test_railway_origin_fallback(client, monkeypatch):
    monkeypatch.delenv("SITE_URL")
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "wunsce.up.railway.app")
    assert Head(client.get("/").text).links["canonical"] == "https://wunsce.up.railway.app/"


def test_health_not_indexed(client):
    assert "noindex" in client.get("/health").headers["X-Robots-Tag"]


@pytest.mark.parametrize("origin", ["https://example.com/path", "https://user:pass@example.com", "javascript:alert(1)"])
def test_invalid_origin(client, monkeypatch, origin):
    monkeypatch.setenv("SITE_URL", origin)
    with pytest.raises(ValueError): client.get("/sitemap.xml")
