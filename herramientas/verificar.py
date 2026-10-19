"""Comprobaciones de sintaxis, vínculos locales, demos y errores de datos comunes."""
from pathlib import Path
import ast
import importlib.util
import re

ROOT = Path(__file__).resolve().parents[1]


def cargar(slug, filename):
    path = ROOT / 'proyectos' / slug / filename
    spec = importlib.util.spec_from_file_location(slug.replace('-', '_'), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    excluded = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache'}
    pyfiles = [p for p in ROOT.rglob('*.py') if not excluded.intersection(p.relative_to(ROOT).parts)]
    for p in pyfiles:
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p.relative_to(ROOT)))
    for p in ROOT.rglob('*.md'):
        if excluded.intersection(p.relative_to(ROOT).parts):
            continue
        for link in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
            if not re.match(r'\w+://', link) and not link.startswith('#'):
                assert (p.parent / link.split('#')[0]).exists(), (p, link)
    bike = cargar('movilidad-urbana', 'analizar.py')
    assert bike.demo()['viajes_validos'] == 3
    assert bike.demo()['duracion_media_segundos'] == 700
    bad = bike.resumir([{'Start Time': 'bad', 'Trip Duration': '3'},
                        {'Start Time': '2025-01-01', 'Trip Duration': '-1'},
                        {'Start Time': '2025-01-01', 'Trip Duration': 'nan'}])
    assert bad['filas_descartadas'] == 3 and bad['duracion_media_segundos'] is None
    optical = cargar('espectros-opticos', 'analizar.py')
    assert optical.demo()['maximo_global'] == {'x': 1550., 'y': 3.}
    assert optical.resumir(['header,metadata', 'NaN,1'])['puntos'] == 0
    qe = cargar('convergencia-manganeso', 'extraer.py')
    assert qe.demo()['energia_final_Ry'] == -451.26
    assert qe.extraer('JOB DONE.')['convergencia_electronica_reportada'] is False
    result = qe.extraer('! total energy = -3 Ry\n! total energy = -4 Ry\nconvergence NOT achieved\nJOB DONE.')
    assert result['energia_final_Ry'] == -4 and result['fallo_convergencia_reportado'] is True
    assert not result['convergencia_electronica_reportada']
    stix = cargar('indicadores-stix', 'analizar.py')
    assert stix.demo()['repeticiones_de_patron'] == 1
    assert stix.resumir([{'objects': [{'type': 'indicator'}]}])['indicadores_sin_patron'] == 1
    print(f'OK: sintaxis de {len(pyfiles)} archivos, enlaces Markdown, 4 demos y casos de datos inválidos.')
    print('Los prototipos históricos de GUI, audio y ML no están cubiertos por estas comprobaciones.')


if __name__ == '__main__':
    main()
