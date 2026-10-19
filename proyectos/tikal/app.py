from flask import Response
from xml.etree import ElementTree as ET
import os,re,secrets,sqlite3,tempfile,time,uuid
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from flask import Flask,abort,flash,g,jsonify,redirect,render_template,request,session,url_for
from database import connect,seed,STATUSES,STATUS_LABELS,NEXT_ACTIONS,TASK_STATUSES,TASK_LABELS,OWNERS
from validation import ValidationError,text,integer,cents,demo_client,demo_email,sku,due_date

BASE_DIR=Path(__file__).resolve().parent
load_dotenv(BASE_DIR/'.env')
app=Flask(__name__)
secret=os.getenv('SECRET_KEY','')
if (secret and len(secret)<32) or (os.getenv('RAILWAY_ENVIRONMENT_ID') and len(secret)<32):
    raise RuntimeError('Set a random stable SECRET_KEY of at least 32 characters')
app.secret_key=secret or secrets.token_hex(32)
RUNTIME_DIR=Path(os.getenv('TIKAL_RUNTIME_DIR',str(Path(tempfile.gettempdir())/'wunsce_tikal_demo'))).resolve()
if RUNTIME_DIR.is_relative_to(BASE_DIR/'static'):raise RuntimeError('Runtime must not be publicly served')
RUNTIME_DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
app.config.update(MAX_CONTENT_LENGTH=16*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=bool(os.getenv('RAILWAY_ENVIRONMENT_ID')),PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),DEMO_TTL=1800,MAX_SPACES=100,MAX_RECORDS=50)
DATA_ENDPOINTS={'product_app','clients','orders','inventory','tasks','advance_order','advance_task','update_stock','reset_demo'}

def safe_url(value,default=''):
    try:
        p=urlsplit(value.strip())
        if p.scheme in ('http','https') and p.hostname and p.port!=0 and not p.username and not p.password and not any(c.isspace() for c in value):return value.strip().rstrip('/')
    except ValueError:pass
    return default
WUNSCE_URL=safe_url(os.getenv('WUNSCE_URL',''),'https://wunsce-main-production.up.railway.app')
SITE_URL=safe_url(os.getenv('SITE_URL',''))
if SITE_URL and (urlsplit(SITE_URL).path or urlsplit(SITE_URL).query or urlsplit(SITE_URL).fragment):raise RuntimeError('SITE_URL must be an origin')
if SITE_URL.startswith('https://'):app.config['SESSION_COOKIE_SECURE']=True

def csrf_token():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

def space_path():
    identifier=session.get('space_id','')
    return RUNTIME_DIR/(identifier+'.sqlite3') if re.fullmatch(r'[a-f0-9]{32}',identifier) else None

def cleanup_spaces():
    for path in RUNTIME_DIR.glob('*.sqlite3'):
        if re.fullmatch(r'[a-f0-9]{32}',path.stem):
            try:
                if time.time()-path.stat().st_mtime>app.config['DEMO_TTL']:
                    path.unlink()
            except OSError:pass

def get_db():
    if 'database' in g:return g.database
    cleanup_spaces()
    path=space_path()
    active=path and path.is_file() and time.time()-session.get('space_started',0)<app.config['DEMO_TTL']
    if not active:
        if request.method=='POST':abort(409)
        if path and path.is_file():
            try:path.unlink()
            except OSError:pass
        if len(list(RUNTIME_DIR.glob('*.sqlite3')))>=app.config['MAX_SPACES']:abort(503)
        session['space_id']=uuid.uuid4().hex;session['space_started']=time.time();session['csrf']=secrets.token_urlsafe(32);session.permanent=True
        path=space_path();con=connect(path)
        try:seed(con)
        except Exception:
            con.close();path.unlink(missing_ok=True);raise
    else:con=connect(path)
    g.database=con
    return con

@app.teardown_appcontext
def close_database(_):
    con=g.pop('database',None)
    if con is not None:con.close()

@app.before_request
def protect():
    if request.method=='POST':
        token=request.form.get('csrf_token','')
        if not token or not secrets.compare_digest(token,session.get('csrf','')):abort(400)

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    if request.endpoint in DATA_ENDPOINTS or request.endpoint=='health' or response.status_code>=400:
        response.headers['Cache-Control']='no-store';response.headers['X-Robots-Tag']='noindex, nofollow'
    return response

PUBLIC_DESCRIPTIONS = {'/': 'Organiza clientes, pedidos, inventario y tareas con TIKAL. Explora una demo operativa para pequeñas empresas con datos ficticios.', '/features': 'Conoce el flujo de TIKAL desde lead y cotización hasta pedido, producción, entrega y cobro, con inventario y tareas visibles.', '/case-study': 'Explora una operación ficticia en TIKAL: avanza pedidos, revisa pendientes y consulta inventario. No representa clientes ni resultados reales.', '/architecture': 'Conoce la arquitectura de TIKAL: Flask, SQLite temporal por sesión, validaciones y control del flujo operativo de la demo.'}

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
    return dict(seo_description=PUBLIC_DESCRIPTIONS.get(request.path, 'Demostración pública de TIKAL · WUNSCE. Usa solo datos ficticios.'), social_image=origin + '/static/img/og-wunsce.png', wunsce_url=WUNSCE_URL,csrf_token=csrf_token,statuses=STATUSES,status_labels=STATUS_LABELS,next_actions=NEXT_ACTIONS,task_labels=TASK_LABELS,task_statuses=TASK_STATUSES,owners=OWNERS,today=date.today().isoformat(),demo_page=request.endpoint in DATA_ENDPOINTS,canonical_url=origin+request.path if request.endpoint in ('home','features','case_study','architecture') else None)

@app.template_filter('money')
def money_filter(value):return f'{Decimal(value)/100:,.2f}'

@app.get('/')
def home():return render_template('home.html')
@app.get('/features')
def features():return render_template('features.html')
@app.get('/case-study')
def case_study():return render_template('case_study.html')
@app.get('/architecture')
def architecture():return render_template('architecture.html')

@app.get('/health')
def health():
    try:
        with tempfile.TemporaryFile(dir=RUNTIME_DIR) as probe:probe.write(b'ok')
        con=sqlite3.connect(':memory:')
        try:con.execute('SELECT 1').fetchone()
        finally:con.close()
    except (OSError,sqlite3.Error):return jsonify(status='unavailable',service='tikal-web'),503
    return jsonify(status='ok',service='tikal-web')

@app.get('/app')
def product_app():
    con=get_db()
    stats=dict(clients=con.execute('SELECT COUNT(*) FROM clients').fetchone()[0],orders=con.execute('SELECT COUNT(*) FROM orders').fetchone()[0],paid=con.execute("SELECT COALESCE(SUM(amount_cents),0) FROM orders WHERE status='Paid'").fetchone()[0],unpaid=con.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'").fetchone()[0],low_stock=con.execute('SELECT COUNT(*) FROM inventory WHERE stock<=min_stock').fetchone()[0],open_tasks=con.execute("SELECT COUNT(*) FROM tasks WHERE status!='Done'").fetchone()[0])
    pipeline={status:con.execute('SELECT orders.*,clients.name client_name FROM orders JOIN clients ON clients.id=orders.client_id WHERE status=? ORDER BY orders.id',(status,)).fetchall() for status in STATUSES}
    alerts=con.execute('SELECT * FROM inventory WHERE stock<=min_stock ORDER BY stock-min_stock,id').fetchall()
    pending=con.execute("SELECT tasks.*,orders.description order_description FROM tasks LEFT JOIN orders ON orders.id=tasks.order_id WHERE tasks.status!='Done' ORDER BY tasks.due_date IS NULL,tasks.due_date,tasks.id LIMIT 8").fetchall()
    return render_template('app.html',stats=stats,pipeline=pipeline,alerts=alerts,pending=pending)

def capacity(con,table):
    # Fixed whitelist: never interpolate a table from user input.
    if table not in ('clients','orders','inventory','tasks'):raise ValueError('Invalid table')
    if not con.in_transaction:con.execute('BEGIN IMMEDIATE')
    if con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]>=app.config['MAX_RECORDS']:
        raise ValidationError('Límite de 50 registros por módulo demo. Reinicia tu entorno para seguir explorando.')

def reference(con,table,value,label,optional=False):
    if optional and not value:return None
    identifier=integer(value,label,1,100000)
    if table not in ('clients','orders'):raise ValueError('Invalid reference table')
    if not con.execute('SELECT 1 FROM '+table+' WHERE id=?',(identifier,)).fetchone():raise ValidationError(label+': selecciona un registro de tu entorno demo.')
    return identifier

def fields(keys):return {key:request.form.get(key,'').strip() for key in keys}

@app.route('/clients',methods=['GET','POST'])
def clients():
    con=get_db();values={};error=None;code=200
    if request.method=='POST':
        values=fields(['name','email'])
        try:
            name=demo_client(values['name']);email=demo_email(values['email']);capacity(con,'clients')
            with con:con.execute('INSERT INTO clients(name,email) VALUES(?,?)',(name,email))
            flash('Cliente ficticio agregado a tu entorno.','success');return redirect(url_for('clients'))
        except ValidationError as exc:error=str(exc);code=422
        except sqlite3.IntegrityError:error='Ese nombre demo ya existe.';code=422
    return render_template('clients.html',rows=con.execute('SELECT * FROM clients ORDER BY id DESC').fetchall(),values=values,error=error),code

@app.route('/orders',methods=['GET','POST'])
def orders():
    con=get_db();values={};error=None;code=200
    if request.method=='POST':
        values=fields(['client_id','description','amount'])
        try:
            client_id=reference(con,'clients',values['client_id'],'Cliente');description=text(values['description'],'Descripción',100);amount=cents(values['amount']);capacity(con,'orders')
            if request.form.get('status','Lead')!='Lead':raise ValidationError('Los nuevos pedidos comienzan en Lead. Avánzalos paso a paso.')
            with con:con.execute('INSERT INTO orders(client_id,description,amount_cents,status) VALUES(?,?,?,?)',(client_id,description,amount,'Lead'))
            flash('Nuevo lead ficticio creado.','success');return redirect(url_for('orders'))
        except ValidationError as exc:error=str(exc);code=422
    stage=request.args.get('stage','')
    if stage and stage not in STATUSES:abort(404)
    query='SELECT orders.*,clients.name client_name FROM orders JOIN clients ON clients.id=orders.client_id'
    rows=con.execute(query+(' WHERE orders.status=?' if stage else '')+' ORDER BY orders.id DESC',(stage,) if stage else ()).fetchall()
    return render_template('orders.html',rows=rows,clients=con.execute('SELECT * FROM clients ORDER BY name').fetchall(),values=values,error=error,stage=stage),code

@app.post('/orders/<int:identifier>/advance')
def advance_order(identifier):
    con=get_db();row=con.execute('SELECT * FROM orders WHERE id=?',(identifier,)).fetchone()
    if not row:abort(404)
    expected=request.form.get('expected_status','')
    index=STATUSES.index(row['status'])
    if expected!=row['status'] or index==len(STATUSES)-1:abort(409)
    with con:
        changed=con.execute('UPDATE orders SET status=? WHERE id=? AND status=?',(STATUSES[index+1],identifier,expected)).rowcount
        if changed!=1:abort(409)
    flash('Pedido demo actualizado a '+STATUSES[index+1]+'.','success')
    return redirect(url_for('orders'))

@app.route('/inventory',methods=['GET','POST'])
def inventory():
    con=get_db();values={};error=None;code=200
    if request.method=='POST':
        values=fields(['sku','name','stock','min_stock'])
        try:
            product_sku=sku(values['sku']);name=text(values['name'],'Producto',80);stock=integer(values['stock'],'Existencias');minimum=integer(values['min_stock'],'Mínimo');capacity(con,'inventory')
            with con:con.execute('INSERT INTO inventory(sku,name,stock,min_stock) VALUES(?,?,?,?)',(product_sku,name,stock,minimum))
            flash('Producto ficticio agregado.','success');return redirect(url_for('inventory'))
        except ValidationError as exc:error=str(exc);code=422
        except sqlite3.IntegrityError:error='El SKU demo ya existe.';code=422
    return render_template('inventory.html',rows=con.execute('SELECT * FROM inventory ORDER BY name').fetchall(),values=values,error=error),code

@app.post('/inventory/<int:identifier>/stock')
def update_stock(identifier):
    con=get_db();row=con.execute('SELECT * FROM inventory WHERE id=?',(identifier,)).fetchone()
    if not row:abort(404)
    try:
        stock=integer(request.form.get('stock',''),'Existencias');expected=integer(request.form.get('expected_stock',''),'Existencias anteriores')
    except ValidationError as exc:return render_template('error.html',code=422,message=str(exc)),422
    with con:
        if con.execute('UPDATE inventory SET stock=? WHERE id=? AND stock=?',(stock,identifier,expected)).rowcount!=1:abort(409)
    flash('Existencias demo actualizadas manualmente.','success');return redirect(url_for('inventory'))

@app.route('/tasks',methods=['GET','POST'])
def tasks():
    con=get_db();values={};error=None;code=200
    if request.method=='POST':
        values=fields(['title','owner','due_date','order_id'])
        try:
            title=text(values['title'],'Tarea',100);owner=values['owner'];due=due_date(values['due_date']);order_id=reference(con,'orders',values['order_id'],'Pedido',optional=True);capacity(con,'tasks')
            if owner not in OWNERS:raise ValidationError('Selecciona un equipo ficticio de la lista.')
            if request.form.get('status','Pending')!='Pending':raise ValidationError('Las tareas nuevas comienzan pendientes.')
            with con:con.execute('INSERT INTO tasks(title,owner,due_date,status,order_id) VALUES(?,?,?,?,?)',(title,owner,due,'Pending',order_id))
            flash('Tarea demo creada.','success');return redirect(url_for('tasks'))
        except ValidationError as exc:error=str(exc);code=422
    rows=con.execute('SELECT tasks.*,orders.description order_description FROM tasks LEFT JOIN orders ON orders.id=tasks.order_id ORDER BY tasks.status="Done",tasks.due_date IS NULL,tasks.due_date,tasks.id').fetchall()
    return render_template('tasks.html',rows=rows,orders=con.execute('SELECT id,description FROM orders ORDER BY id').fetchall(),values=values,error=error),code

@app.post('/tasks/<int:identifier>/advance')
def advance_task(identifier):
    con=get_db();row=con.execute('SELECT * FROM tasks WHERE id=?',(identifier,)).fetchone()
    if not row:abort(404)
    index=TASK_STATUSES.index(row['status']);expected=request.form.get('expected_status','')
    if expected!=row['status'] or index==len(TASK_STATUSES)-1:abort(409)
    with con:
        if con.execute('UPDATE tasks SET status=? WHERE id=? AND status=?',(TASK_STATUSES[index+1],identifier,expected)).rowcount!=1:abort(409)
    flash('Estado de tarea demo actualizado.','success');return redirect(url_for('tasks'))

@app.post('/reset-demo')
def reset_demo():
    path=space_path()
    if path:
        try:path.unlink(missing_ok=True)
        except OSError:abort(409)
    session.pop('space_id',None);session.pop('space_started',None);session.pop('csrf',None)
    flash('Tu entorno demo se ha reiniciado.','success');return redirect(url_for('product_app'))

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(409)
@app.errorhandler(413)
@app.errorhandler(500)
@app.errorhandler(503)
def error_page(error):
    messages={400:'El formulario o la sesión no es válido. Vuelve a abrir la demo.',404:'El registro no existe en tu entorno.',409:'El entorno venció o el registro cambió. Abre de nuevo el módulo antes de continuar.',413:'La solicitud supera el límite de 16 KB.',500:'No se pudo completar la operación. Vuelve a intentarlo.',503:'La demo está ocupada. Inténtalo más tarde.'}
    return render_template('error.html',code=error.code,message=messages[error.code]),error.code

@app.errorhandler(sqlite3.OperationalError)
def storage_error(_):
    return render_template('error.html',code=503,message='El almacenamiento demo no está disponible temporalmente. Inténtalo de nuevo.'),503

if __name__=='__main__':
    port=int(os.getenv('PORT') or '8000')
    if not 1<=port<=65535:raise ValueError('Invalid PORT')
    app.run(host='0.0.0.0',port=port,debug=False)
