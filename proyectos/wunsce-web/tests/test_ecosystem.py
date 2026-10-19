from html.parser import HTMLParser
import pytest
from app import app, PROJECTS


class Catalog(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.cards, self.links = [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and 'hub-project' in attrs.get('class', '').split():
            self.cards.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs)


@pytest.mark.parametrize('path', ['/', '/projects'])
def test_hub_uses_environment_links_and_one_card_per_project(monkeypatch, path):
    for project in PROJECTS:
        monkeypatch.setenv(project['slug'].upper() + '_URL', 'https://demo.example/' + project['slug'])
    html = app.test_client().get(path).text
    catalog = Catalog(html)
    assert catalog.cards == ['project-' + p['slug'] for p in PROJECTS]
    for project in PROJECTS:
        links = [a for a in catalog.links if a.get('href') == 'https://demo.example/' + project['slug']]
        assert len(links) == 1
        assert {'noopener', 'noreferrer'} <= set(links[0]['rel'].split())
        assert html.index('id="title-' + project['slug'] + '"') < html.index('<p class="project-brand">' + project['name'])


@pytest.mark.parametrize('value', ['', 'javascript:alert(1)', 'https://user:password@example.com'])
def test_unconfigured_or_unsafe_demo_has_no_external_cta(monkeypatch, value):
    monkeypatch.setenv('NANA_URL', value)
    html = app.test_client().get('/projects/nana').text
    assert 'Enlace público no configurado' in html
    assert 'Explorar transformación de datos ↗' not in html
    assert 'ENLACE PÚBLICO NO CONFIGURADO' in app.test_client().get('/').text


def test_links_can_change_without_stale_catalog(monkeypatch):
    client = app.test_client()
    monkeypatch.setenv('DARWIN_URL', 'https://demo.example/first')
    assert 'href="https://demo.example/first"' in client.get('/projects/darwin').text
    monkeypatch.setenv('DARWIN_URL', 'https://demo.example/second')
    assert 'href="https://demo.example/second"' in client.get('/projects/darwin').text
    assert 'href="https://demo.example/first"' not in client.get('/projects/darwin').text


def test_ecosystem_map_preserves_scope_and_brand():
    html = app.test_client().get('/').text
    assert 'id="ecosistema"' in html and 'WUNSCE Ecosystem' in html
    assert 'no comparten datos ni se conectan automáticamente' in html
    assert 'Understand.' in html and 'Choose.' in html and 'Transform.' in html
    assert html.index('id="ecosistema"') < html.index('id="origen"')
    for project in PROJECTS:
        assert project['ecosystem_action'] in html
        assert f'img/emblems/{project["slug"]}.webp' in html


def test_published_website_is_separate_optional_link(monkeypatch):
    monkeypatch.setenv('ESCULAPIO_URL', 'https://demo.example/case-study')
    monkeypatch.setenv('ESCULAPIO_IMPLEMENTATION_URL', 'https://clinic.example/')
    html = app.test_client().get('/projects/esculapio').text
    assert 'href="https://demo.example/case-study"' in html
    assert 'href="https://clinic.example/"' in html
    assert 'demo administrativa independiente' in html
    monkeypatch.setenv('ESCULAPIO_IMPLEMENTATION_URL', 'javascript:alert(1)')
    assert 'Ver web del Dr. Jonathan' not in app.test_client().get('/projects/esculapio').text
