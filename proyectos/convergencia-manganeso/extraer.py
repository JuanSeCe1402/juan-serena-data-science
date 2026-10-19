"""Resumen de salidas Quantum ESPRESSO; sin argumentos usa un caso sintético."""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?'


def extraer(text):
    energias = re.findall(r'!\s+total energy\s*=\s*(' + NUMBER + r')\s+Ry', text, re.I)
    fallo = bool(re.search(r'convergence\s+NOT\s+achieved', text, re.I))
    convergencia = bool(re.search(r'convergence has been achieved', text, re.I))
    return {'energia_final_Ry': float(energias[-1].replace('D', 'E').replace('d', 'e')) if energias else None,
            'energias_finales_encontradas': len(energias), 'job_done': 'JOB DONE.' in text,
            'convergencia_electronica_reportada': convergencia,
            'fallo_convergencia_reportado': fallo}


def demo():
    return extraer('convergence has been achieved\n! total energy = -4.5126D+02 Ry\nJOB DONE.\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archivos', nargs='*', type=Path)
    args = ap.parse_args()
    rows = []
    for p in args.archivos:
        rows.append({'archivo': p.name, **extraer(p.read_text(errors='replace'))})
    if not rows:
        rows = [{'archivo': 'DEMO_SINTETICA', **demo()}]
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)


if __name__ == '__main__':
    main()
