DEMO_PATH = "/demo"

from html.parser import HTMLParser
from xml.etree import ElementTree as ET


class Head(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.meta = {}; self.canonical = None; self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')


PUBLIC_PATHS = ('/', '/features', '/case-study', '/architecture')


def test_public_metadata_is_unique_and_social_cards_match(client):
    descriptions = set()
    for path in PUBLIC_PATHS:
        response = client.get(path + '?utm_source=audit')
        assert response.status_code == 200
        head = Head(response.text)
        assert head.canonical.endswith(path)
        assert '?' not in head.canonical
        assert head.meta['og:url'] == head.canonical
        assert head.meta['description'] == head.meta['og:description'] == head.meta['twitter:description']
        assert head.meta['og:title'] == head.meta['twitter:title']
        assert head.meta['twitter:card'] == 'summary_large_image'
        assert head.meta['og:image'].startswith(('http://', 'https://'))
        assert head.meta['og:image'] == head.meta['twitter:image']
        assert head.meta['og:image:alt']
        descriptions.add(head.meta['description'])
    assert len(descriptions) == 4


def test_sitemap_contains_only_public_pages(client):
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert 'application/xml' in response.headers['content-type']
    tree = ET.fromstring(response.content if hasattr(response, 'content') else response.data)
    urls = [element.text for element in tree.findall('{*}url/{*}loc')]
    assert len(urls) == 4
    from urllib.parse import urlsplit
    assert {urlsplit(url).path for url in urls} == set(PUBLIC_PATHS)
    for url in urls:
        assert client.get(urlsplit(url).path).status_code == 200


def test_robots_announces_sitemap(client):
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert 'text/plain' in response.headers['content-type']
    assert 'Disallow: /health' in response.text
    assert 'Sitemap: ' in response.text and '/sitemap.xml' in response.text


def test_social_image_is_served_and_demo_errors_stay_noindex(client):
    response = client.get('/static/img/og-wunsce.png')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('image/png')
    demo = client.get(DEMO_PATH)
    assert 'noindex' in Head(demo.text).meta['robots']
    missing = client.get('/not-a-public-page')
    assert missing.status_code == 404
    head = Head(missing.text)
    assert 'noindex' in head.meta['robots']
    assert head.canonical is None and 'og:url' not in head.meta
