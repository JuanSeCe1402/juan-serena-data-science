from flask import Response
from xml.etree import ElementTree as ET
import os
import re
import secrets
import shutil
import tempfile
import time
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
import pandas as pd
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from core import clean_dataframe, quality_score, dataframe_to_sqlite_file, profile_columns, spreadsheet_safe

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
RUNTIME_DIR = Path(os.getenv('NANA_RUNTIME_DIR', str(Path(tempfile.gettempdir()) / 'wunsce_nana')))
RUNTIME_DIR = RUNTIME_DIR.resolve()
if RUNTIME_DIR.is_relative_to(BASE_DIR / 'static'):
    raise RuntimeError('Runtime directory must not be publicly served')
RUNTIME_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
app = Flask(__name__)
secret = os.getenv('SECRET_KEY', '')
if secret and len(secret) < 32:
    raise RuntimeError('SECRET_KEY must contain at least 32 random characters')
if os.getenv('RAILWAY_ENVIRONMENT_ID') and len(secret) < 32:
    raise RuntimeError('Set a random SECRET_KEY of at least 32 characters in Railway')
app.secret_key = secret or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=1024*1024, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=bool(os.getenv('RAILWAY_ENVIRONMENT_ID')),
                  PERMANENT_SESSION_LIFETIME=timedelta(minutes=30), UPLOADS_ENABLED=False,
                  MAX_ROWS=2000, MAX_COLUMNS=50, JOB_TTL=1800, MAX_JOBS=100)

def safe_url(value, default=''):
    try:
        p = urlsplit(value.strip())
        if p.scheme in ('http','https') and p.hostname and p.port != 0 and not p.username and not p.password and not any(c.isspace() for c in value):
            return value.strip().rstrip('/')
    except ValueError:
        pass
    return default

WUNSCE_URL = safe_url(os.getenv('WUNSCE_URL',''), 'https://wunsce-main-production.up.railway.app')
SITE_URL = safe_url(os.getenv('SITE_URL',''))
if SITE_URL and (urlsplit(SITE_URL).path or urlsplit(SITE_URL).query or urlsplit(SITE_URL).fragment):
    raise RuntimeError('SITE_URL must be an origin without a path, query or fragment')
if SITE_URL.startswith('https://'):
    app.config['SESSION_COOKIE_SECURE'] = True


def cleanup_jobs():
    now = time.time()
    for path in RUNTIME_DIR.iterdir():
        if path.is_dir() and re.fullmatch(r'[a-f0-9]{32}',path.name):
            try:
                if now-path.stat().st_mtime > app.config['JOB_TTL']:
                    shutil.rmtree(path)
            except OSError:
                pass


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']

@app.before_request
def protect_request():
    if request.method == 'POST':
        token = request.form.get('csrf_token','')
        if not token or not secrets.compare_digest(token, session.get('csrf','')):
            abort(400, description='La sesión del formulario venció. Vuelve a abrir la demo.')

@app.after_request
def secure_response(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.endpoint in ('nana_app','download','health') or response.status_code >= 400:
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response

PUBLIC_DESCRIPTIONS = {'/': 'Transforma datos sintéticos desordenados en información estructurada. Explora la demo pública de NANA y sus salidas CSV y SQLite.', '/features': 'Conoce las capacidades de NANA: normalización de columnas, duplicados, valores faltantes, perfilado y exportación CSV y SQLite.', '/case-study': 'Explora un caso ficticio de transformación de datos con NANA. Revisa el problema, el proceso de limpieza y los resultados del ejemplo sintético.', '/architecture': 'Conoce la arquitectura de NANA: Flask, Pandas, procesamiento de datos y artefactos temporales. Alcance actual y posibles siguientes pasos.'}

def public_origin():
    return SITE_URL or safe_url('https://' + os.getenv('RAILWAY_PUBLIC_DOMAIN', '')) or request.url_root.rstrip('/')


@app.get('/sitemap.xml')
def sitemap():
    root = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in PUBLIC_DESCRIPTIONS:
        ET.SubElement(ET.SubElement(root, 'url'), 'loc').text = public_origin() + path
    return Response(ET.tostring(root, encoding='utf-8', xml_declaration=True), mimetype='application/xml')


@app.get('/robots.txt')
def robots():
    return Response('User-agent: *\nAllow: /\nDisallow: /health\nSitemap: ' + public_origin() + '/sitemap.xml\n', mimetype='text/plain')


@app.context_processor
def inject_brand():
    origin = SITE_URL or safe_url('https://' + os.getenv('RAILWAY_PUBLIC_DOMAIN','')) or request.url_root.rstrip('/')
    canonical = origin + request.path if request.method == 'GET' and request.endpoint in ('home','features','case_study','architecture') else None
    return dict(seo_description=PUBLIC_DESCRIPTIONS.get(request.path, 'Demostración pública de NANA · WUNSCE. Usa solo datos ficticios.'), social_image=origin + '/static/img/og-wunsce.png', wunsce_url=WUNSCE_URL, canonical_url=canonical, csrf_token=csrf_token,
                uploads_enabled=app.config['UPLOADS_ENABLED'], contact_email='', contact_whatsapp='')

@app.get('/')
def home(): return render_template('home.html')
@app.get('/features')
def features(): return render_template('features.html')
@app.get('/case-study')
def case_study(): return render_template('case_study.html')
@app.get('/architecture')
def architecture(): return render_template('architecture.html')

@app.route('/app', methods=['GET','POST'])
def nana_app():
    cleanup_jobs()
    if request.method == 'GET': return render_template('app.html')
    jobs = session.get('jobs', [])
    # Per-session cooldown and a bounded global disk budget, suitable for a small demo.
    if time.time()-session.get('last_job',0) < 3:
        abort(429, description='Espera unos segundos antes de volver a ejecutar el ejemplo.')
    if len(list(RUNTIME_DIR.glob('????????????????????????????????'))) >= app.config['MAX_JOBS']:
        abort(503, description='La demo está ocupada. Inténtalo más tarde.')
    try:
        if request.form.get('source') == 'sample':
            source = BASE_DIR/'demo'/'dirty_customers.csv'
        elif app.config['UPLOADS_ENABLED']:
            upload = request.files.get('file')
            if not upload or not upload.filename.lower().endswith('.csv'):
                raise ValueError('Selecciona un archivo CSV sintético.')
            source = upload
        else:
            abort(400, description='La demo pública solo admite el ejemplo sintético incluido.')
        raw = pd.read_csv(source, dtype=str, keep_default_na=False, nrows=app.config['MAX_ROWS']+1)
        if raw.empty: raise ValueError('El archivo está vacío.')
        if len(raw)>app.config['MAX_ROWS'] or len(raw.columns)>app.config['MAX_COLUMNS']:
            raise ValueError('El ejemplo supera el límite de 2000 filas o 50 columnas.')
        clean, report = clean_dataframe(raw)
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
        flash('No se pudo procesar el CSV. Usa UTF-8, separador coma y hasta 2000 filas y 50 columnas.', 'error')
        return redirect(url_for('nana_app'))
    job_id = uuid.uuid4().hex
    out = RUNTIME_DIR/job_id
    out.mkdir(mode=0o700)
    try:
        clean.map(spreadsheet_safe).to_csv(out/'nana_clean_data.csv',index=False)
        dataframe_to_sqlite_file(clean,out/'nana_clean_data.db')
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        app.logger.error('Artifact export failed')
        abort(500)
    # Delete older artifacts of this session before retaining the latest five.
    for previous in jobs[:-4]:
        shutil.rmtree(RUNTIME_DIR/previous,ignore_errors=True)
    session['jobs'] = jobs[-4:]+[job_id]
    session['last_job'] = time.time()
    session.permanent = True
    return render_template('results.html',report=report,score=quality_score(clean,report['duplicates_found']),
        job_id=job_id,preview=clean.head(25).fillna('').to_dict(orient='records'),headers=list(clean.columns),columns=profile_columns(clean))

@app.get('/download/<job_id>/<kind>')
def download(job_id,kind):
    cleanup_jobs()
    if not re.fullmatch(r'[a-f0-9]{32}',job_id) or job_id not in session.get('jobs',[]): abort(404)
    extensions={'csv':'csv','sqlite':'db'}
    if kind not in extensions: abort(404)
    path=RUNTIME_DIR/job_id/('nana_clean_data.'+extensions[kind])
    if not path.is_file() or time.time()-path.parent.stat().st_mtime > app.config['JOB_TTL']: abort(404)
    return send_file(path,as_attachment=True,download_name=path.name,mimetype='text/csv' if kind=='csv' else 'application/octet-stream')

@app.get('/sample.csv')
def sample():
    return send_file(BASE_DIR/'demo'/'dirty_customers.csv',as_attachment=True,download_name='nana_ejemplo_sintetico.csv',mimetype='text/csv')

@app.get('/health')
def health(): return jsonify(status='ok',service='nana-web')

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(429)
@app.errorhandler(503)
@app.errorhandler(500)
def error_page(error):
    messages={400:'Solicitud no válida. Vuelve a abrir la demo.',404:'La página o descarga no existe, venció o pertenece a otra sesión.',413:'La solicitud supera el límite de 1 MB.',429:'Espera unos segundos antes de volver a ejecutar el ejemplo.',503:'La demo está ocupada. Inténtalo más tarde.',500:'No se pudo completar el proceso. Vuelve a intentarlo.'}
    return render_template('error.html',code=error.code,message=messages[error.code]),error.code

if __name__=='__main__':
    port=int(os.getenv('PORT') or '8000')
    if not 1<=port<=65535: raise ValueError('Invalid PORT')
    app.run(host='0.0.0.0',port=port,debug=False)
