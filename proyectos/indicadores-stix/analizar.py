"""Contar y deduplicar indicadores de bundles STIX locales."""
import argparse
import json
from collections import Counter
from pathlib import Path


def resumir(bundles):
    tipos, identifiers, patrones = Counter(), set(), set()
    sin_id, sin_patron, indicadores = 0, 0, 0
    for bundle in bundles:
        objects = bundle.get('objects', [])
        if not isinstance(objects, list):
            raise ValueError('objects debe ser una lista')
        for item in objects:
            if not isinstance(item, dict):
                raise ValueError('Cada objeto STIX debe ser un diccionario')
            tipos[item.get('type', 'sin_tipo')] += 1
            if item.get('type') == 'indicator':
                indicadores += 1
                if item.get('id'):
                    identifiers.add(item['id'])
                else:
                    sin_id += 1
                if item.get('pattern'):
                    patrones.add(item['pattern'])
                else:
                    sin_patron += 1
    return {'objetos_por_tipo': dict(sorted(tipos.items())), 'indicadores': indicadores,
            'ids_unicos': len(identifiers), 'patrones_unicos': len(patrones),
            'indicadores_sin_id': sin_id, 'indicadores_sin_patron': sin_patron,
            'repeticiones_de_patron': indicadores - sin_patron - len(patrones)}


def demo():
    return resumir([{'type': 'bundle', 'objects': [
        {'type': 'indicator', 'id': 'indicator--demo-a', 'pattern': "[domain-name:value = 'example.invalid']"},
        {'type': 'indicator', 'id': 'indicator--demo-b', 'pattern': "[domain-name:value = 'example.invalid']"},
        {'type': 'malware', 'id': 'malware--demo'}]}])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archivos', nargs='*', type=Path)
    args = ap.parse_args()
    result = resumir([json.loads(p.read_text(encoding='utf-8')) for p in args.archivos]) if args.archivos else demo()
    print(json.dumps({'origen': 'archivos locales' if args.archivos else 'SINTÉTICO', 'resumen': result},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
