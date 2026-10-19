"""Extraer pares numéricos de CSV instrumentales; demo sintética por defecto."""
import argparse
import csv
import io
import json
import math
from pathlib import Path


def resumir(lines):
    pares, otras = [], 0
    for row in csv.reader(lines):
        try:
            x, y = float(row[0]), float(row[1])
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError('valor no finito')
        except (ValueError, IndexError):
            otras += 1
            continue
        pares.append((x, y))
    if not pares:
        return {'puntos': 0, 'otras_filas': otras, 'maximo_global': None}
    peak = max(pares, key=lambda xy: xy[1])
    return {'puntos': len(pares), 'otras_filas': otras,
            'x_min': min(x for x, _ in pares), 'x_max': max(x for x, _ in pares),
            'maximo_global': {'x': peak[0], 'y': peak[1]},
            'nota': 'Unidades dependen del archivo; el máximo global no es identificación física.'}


def demo():
    return resumir(io.StringIO('File,Demo\nWavelength,Signal\n1549,1\n1550,3\n1551,2\n'))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archivos', nargs='*', type=Path)
    args = ap.parse_args()
    if not args.archivos:
        print(json.dumps({'origen': 'SINTÉTICO', 'resumen': demo()}, ensure_ascii=False, indent=2))
    for p in args.archivos:
        with p.open(encoding='utf-8-sig') as f:
            result = resumir(f)
        print(json.dumps({'archivo': p.name, 'resumen': result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
