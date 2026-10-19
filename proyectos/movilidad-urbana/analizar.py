"""Resumen de viajes. Sin archivos de entrada usa observaciones SINTÉTICAS."""
import argparse
import csv
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def resumir(rows):
    horas, tipos = Counter(), Counter()
    duraciones, descartadas = [], 0
    for row in rows:
        try:
            duracion = float(row['Trip Duration'])
            inicio = datetime.fromisoformat(row['Start Time'])
            if duracion < 0 or not __import__('math').isfinite(duracion):
                raise ValueError('duración inválida')
        except (ValueError, KeyError, TypeError):
            descartadas += 1
            continue
        duraciones.append(duracion)
        horas[inicio.hour] += 1
        tipos[row.get('User Type') or 'Sin especificar'] += 1
    return {'viajes_validos': len(duraciones), 'filas_descartadas': descartadas,
            'duracion_media_segundos': sum(duraciones) / len(duraciones) if duraciones else None,
            'viajes_por_hora': dict(sorted(horas.items())), 'tipos_usuario': dict(tipos)}


def demo():
    datos = 'Start Time,Trip Duration,User Type\n2025-01-01 08:00:00,600,Demo A\n2025-01-01 08:15:00,1200,Demo B\n2025-01-01 09:00:00,300,Demo A\n'
    return resumir(csv.DictReader(io.StringIO(datos)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archivos', nargs='*', type=Path)
    args = ap.parse_args()
    if not args.archivos:
        print(json.dumps({'origen': 'SINTÉTICO', 'resumen': demo()}, ensure_ascii=False, indent=2))
    for p in args.archivos:
        with p.open(encoding='utf-8-sig', newline='') as f:
            resultado = resumir(csv.DictReader(f))
        print(json.dumps({'archivo': p.name, 'resumen': resultado}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
