from pathlib import Path
import runpy
import pytest

CONFIG = Path(__file__).resolve().parents[1] / "gunicorn.conf.py"

@pytest.mark.parametrize("port, expected", [("18765", "0.0.0.0:18765"), ("", "0.0.0.0:8000"), (None, "0.0.0.0:8000")])
def test_production_bind(monkeypatch, port, expected):
    if port is None:
        monkeypatch.delenv("PORT", raising=False)
    else:
        monkeypatch.setenv("PORT", port)
    assert runpy.run_path(str(CONFIG))["bind"] == expected

@pytest.mark.parametrize("port", ["0", "65536", "bad"])
def test_invalid_production_port(monkeypatch, port):
    monkeypatch.setenv("PORT", port)
    with pytest.raises(ValueError): runpy.run_path(str(CONFIG))
