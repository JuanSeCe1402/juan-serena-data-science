import runpy
from pathlib import Path
import pytest
CONFIG=Path(__file__).resolve().parents[1]/'gunicorn.conf.py'
@pytest.mark.parametrize('port,bind',[('8080','0.0.0.0:8080'),('','0.0.0.0:8000')])
def test_port(monkeypatch,port,bind):
    monkeypatch.setenv('PORT',port)
    assert runpy.run_path(str(CONFIG))['bind']==bind
@pytest.mark.parametrize('port',['0','65536','bad'])
def test_invalid_port(monkeypatch,port):
    monkeypatch.setenv('PORT',port)
    with pytest.raises(ValueError):runpy.run_path(str(CONFIG))
