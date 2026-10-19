"""Detectar artefactos privados y formatos conocidos de secretos antes de publicar.

Comprobación limitada: no demuestra ausencia de secretos ni sustituye revisión.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','.venv','venv','__pycache__','.pytest_cache'}
FORBIDDEN={'.db','.sqlite','.sqlite3','.pt','.pth','.pkl','.pickle','.zip','.rar','.7z','.pem','.key','.log'}
SECRET=re.compile(r'gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|sk-[A-Za-z0-9_-]{25,}|EA[A-Z][A-Za-z0-9]{60,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
TEXT={'.py','.txt','.md','.js','.html','.css','.json','.toml','.yml','.yaml','.csv','.f95'}


def main():
    failures=[]; checked=0
    for p in ROOT.rglob('*'):
        if not p.is_file() or EXCLUDED.intersection(p.relative_to(ROOT).parts):continue
        rel=p.relative_to(ROOT)
        if p.suffix.lower() in FORBIDDEN or (p.name.startswith('.env') and p.name!='.env.example'):
            failures.append(f'Artefacto privado o generado: {rel}')
        if p.suffix.lower() in TEXT or p.name=='.env.example':
            checked+=1
            for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
                if SECRET.search(line):failures.append(f'Posible secreto: {rel}:{n}')
    if failures:raise SystemExit('\n'.join(failures))
    print(f'OK: {checked} archivos de texto revisados; sin artefactos prohibidos ni formatos de secretos detectados.')
    print('Los valores ficticios de pruebas y .env.example requieren además revisión humana.')


if __name__=='__main__':main()
