from flask import Response
from xml.etree import ElementTree as ET
import os
import re
import secrets
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from flask import Flask,abort,jsonify,render_template,request,session,url_for,send_file
from core import EXAMPLES,evaluate,scenarios,number
from pdf_export import build_quote

BASE_DIR=Path(__file__).resolve().parent
load_dotenv(BASE_DIR/'.env')
app=Flask(__name__)
secret=os.getenv('SECRET_KEY','')
if (secret and len(secret)<32) or (os.getenv('RAILWAY_ENVIRONMENT_ID') and len(secret)<32):
    raise RuntimeError('Set a stable random SECRET_KEY of at least 32 characters')
app.secret_key=secret or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=16*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=bool(os.getenv('RAILWAY_ENVIRONMENT_ID')),PERMANENT_SESSION_LIFETIME=timedelta(minutes=30))

def safe_url(value,default=''):
    try:
        p=urlsplit(value.strip())
        if p.scheme in ('http','https') and p.hostname and p.port!=0 and not p.username and not p.password and not any(c.isspace() for c in value): return value.strip().rstrip('/')
    except ValueError: pass
    return default

WUNSCE_URL=safe_url(os.getenv('WUNSCE_URL',''),'https://wunsce-main-production.up.railway.app')
SITE_URL=safe_url(os.getenv('SITE_URL',''))
if SITE_URL and (urlsplit(SITE_URL).path or urlsplit(SITE_URL).query or urlsplit(SITE_URL).fragment): raise RuntimeError('SITE_URL must be an origin')
if SITE_URL.startswith('https://'): app.config['SESSION_COOKIE_SECURE']=True

def csrf_token():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

@app.before_request
def protect():
    if request.method=='POST':
        token=request.form.get('csrf_token','')
        if not token or not secrets.compare_digest(token,session.get('csrf','')): abort(400)

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    if request.endpoint in ('product_app','quote','health') or response.status_code>=400:
        response.headers['Cache-Control']='no-store';response.headers['X-Robots-Tag']='noindex, nofollow'
    return response

PUBLIC_DESCRIPTIONS = {'/': 'Explora costos totales y unitarios, margen, precio sugerido y utilidad con FREY. Demo pública con escenarios hipotéticos y exportación PDF.', '/features': 'Conoce las capacidades de FREY: desglose de costos, merma, escenarios de margen, precios sugeridos y cotizaciones PDF demostrativas.', '/case-study': 'Reproduce un lote ficticio en FREY para entender costo, margen, precio y utilidad. Cifras hipotéticas, sin resultados comerciales atribuidos.', '/architecture': 'Conoce la arquitectura de FREY: Flask, cálculos de costos y precios, validaciones y generación de PDF para ejemplos demostrativos.'}

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
def brand():
    origin=SITE_URL or safe_url('https://'+os.getenv('RAILWAY_PUBLIC_DOMAIN','')) or request.url_root.rstrip('/')
    canonical=origin+request.path if request.method=='GET' and request.endpoint in ('home','features','case_study','architecture') else None
    return dict(seo_description=PUBLIC_DESCRIPTIONS.get(request.path, 'Demostración pública de FREY · WUNSCE. Usa solo datos ficticios.'), social_image=origin + '/static/img/og-wunsce.png', wunsce_url=WUNSCE_URL,csrf_token=csrf_token,canonical_url=canonical)

@app.template_filter('money')
def money_filter(value): return f'{value:,.2f}'

@app.get('/')
def home():return render_template('home.html',example=EXAMPLES['lote'],example_result=evaluate(EXAMPLES['lote']))
@app.get('/features')
def features():return render_template('features.html')
@app.get('/case-study')
def case_study():return render_template('case_study.html',example=EXAMPLES['lote'],result=evaluate(EXAMPLES['lote']))
@app.get('/architecture')
def architecture():return render_template('architecture.html')
@app.get('/health')
def health():return jsonify(status='ok',service='frey-web')

@app.route('/app',methods=['GET','POST'])
def product_app():
    if request.method=='GET':
        key=request.args.get('example','lote')
        if key not in EXAMPLES:abort(404)
        return render_template('app.html',values=EXAMPLES[key],error=None)
    values={key:request.form.get(key,'').strip() for key in EXAMPLES['lote']}
    try:
        if not 1<=len(values['name'])<=80 or any(ord(c)<32 for c in values['name']):
            raise ValueError('Nombre: usa entre 1 y 80 caracteres, sin datos de personas o clientes.')
        result=evaluate(values)
    except ValueError as error:
        session.pop('scenario',None)
        return render_template('app.html',values=values,error=str(error)),422
    # Store only validated, normalized hypothetical inputs in the signed session.
    session['scenario']={key:(values[key] if key=='name' else str(result['quantity']) if key=='quantity' else str(number(values[key],key))) for key in values}
    session.permanent=True
    return render_template('results.html',result=result,scenarios=scenarios(result['total_cost'],quantity=result['quantity']),name=values['name'],values=values)

@app.post('/quote')
def quote():
    values=session.get('scenario')
    if not values:abort(400)
    try: pdf=build_quote(values)
    except ValueError:abort(400)
    return send_file(pdf,as_attachment=True,download_name='frey_escenario_demo.pdf',mimetype='application/pdf')

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(500)
def error_page(error):
    messages={400:'La sesión o el formulario venció. Calcula de nuevo el escenario.',404:'La página solicitada no existe.',413:'La solicitud supera el límite de 16 KB.',500:'No se pudo completar el proceso. Vuelve a intentarlo.'}
    return render_template('error.html',code=error.code,message=messages[error.code]),error.code

if __name__=='__main__':
    port=int(os.getenv('PORT') or '8000')
    if not 1<=port<=65535:raise ValueError('Invalid PORT')
    app.run(host='0.0.0.0',port=port,debug=False)
