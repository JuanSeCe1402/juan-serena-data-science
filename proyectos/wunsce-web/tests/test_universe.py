from app import app
from lore import CHARACTERS


def test_universe_connects_every_character():
    response = app.test_client().get("/universo")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for character in CHARACTERS:
        assert f'id="{character["slug"]}"' in html
        assert character["title"] in html
    assert "Nanahuatzin" in html
    assert "espejo" in html
    assert 'href="/projects/psique"' not in html


def test_projects_have_documented_story_and_business_role():
    for slug in ["nana", "frey", "tikal", "darwin", "esculapio"]:
        response = app.test_client().get("/projects/" + slug)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "EN LA TRAVESÍA" in html
        assert "EN WUNSCE" in html
        assert f'href="/universo#{slug}"' in html


def test_universe_is_discoverable():
    client = app.test_client()
    assert 'href="/universo"' in client.get("/").get_data(as_text=True)
    assert "/universo</loc>" in client.get("/sitemap.xml").get_data(as_text=True)


def test_public_scope_excludes_future_projects():
    client = app.test_client()
    for path in ["/", "/universo", "/about", "/projects", "/services", "/contact"] + ["/projects/" + slug for slug in ["nana", "frey", "tikal", "darwin", "esculapio"]]:
        html = client.get(path).get_data(as_text=True).lower()
        for future in ["xian", "psique", "shiva"]:
            assert future not in html, (path, future)
    html = client.get("/universo").get_data(as_text=True)
    assert 'id="principios"' in html
    assert "Principio de la empresa" in html
    assert "LOS PROYECTOS Y SU PROPIO LORE" in html
