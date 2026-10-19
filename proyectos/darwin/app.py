from flask import Response
from xml.etree import ElementTree as ET
import csv
import io
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
from dotenv import load_dotenv
from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, session, url_for, flash
from core import Config, ValidationError, FEATURES, FEATURE_LABELS, MODELS, STEPS, run_experiment, raw_dataset

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR/".env")
app = Flask(__name__)
secret = os.getenv("SECRET_KEY", "")
if (secret and len(secret)<32) or (os.getenv("RAILWAY_ENVIRONMENT_ID") and len(secret)<32):
    raise RuntimeError("Set a random stable SECRET_KEY of at least 32 characters")
app.secret_key = secret or secrets.token_hex(32)
RUNTIME_DIR = Path(os.getenv("DARWIN_RUNTIME_DIR", str(Path(tempfile.gettempdir())/"wunsce_darwin_demo"))).resolve()
if RUNTIME_DIR.is_relative_to(BASE_DIR/"static"):
    raise RuntimeError("Runtime must not be publicly served")
RUNTIME_DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
app.config.update(MAX_CONTENT_LENGTH=4096, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=bool(os.getenv("RAILWAY_ENVIRONMENT_ID")), PERMANENT_SESSION_LIFETIME=timedelta(minutes=30), RESULT_TTL=1800, MAX_RESULTS=100, TRAIN_COOLDOWN=10, MIN_TRAIN_INTERVAL=2)
TRAIN_LOCK = threading.Lock()
LAST_TRAIN = 0.0


def safe_url(value, default=""):
    try:
        p = urlsplit(value.strip())
        if p.scheme in ("http","https") and p.hostname and p.port!=0 and not p.username and not p.password and not any(c.isspace() for c in value):
            return value.strip().rstrip("/")
    except ValueError:
        pass
    return default


WUNSCE_URL = safe_url(os.getenv("WUNSCE_URL",""),"https://wunsce-main-production.up.railway.app")
SITE_URL = safe_url(os.getenv("SITE_URL",""))
if SITE_URL and (urlsplit(SITE_URL).path or urlsplit(SITE_URL).query or urlsplit(SITE_URL).fragment):
    raise RuntimeError("SITE_URL must be an origin")
if SITE_URL.startswith("https://"):
    app.config["SESSION_COOKIE_SECURE"] = True


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


@app.before_request
def protect():
    if request.method=="POST":
        token = request.form.get("csrf_token", "")
        if not token or not secrets.compare_digest(token,session.get("csrf","")):
            abort(400)


@app.after_request
def headers(response):
    response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY", "Referrer-Policy":"strict-origin-when-cross-origin", "Content-Security-Policy":"default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'", "Permissions-Policy":"camera=(), microphone=(), geolocation=()"})
    if request.endpoint in ("product_app","download","download_input","reset_demo","health") or response.status_code>=400:
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    if response.status_code==429:
        response.headers["Retry-After"] = str(app.config["TRAIN_COOLDOWN"])
    return response


PUBLIC_DESCRIPTIONS = {'/': 'Explora analítica predictiva de negocio con DARWIN: datos sintéticos, modelos, métricas calculadas y señales de recompra por cliente ficticio.', '/features': 'Conoce el flujo de DARWIN: preparación de datos sintéticos, variables, modelos, evaluación y predicciones explicadas para personas no técnicas.', '/case-study': 'Reproduce un experimento ficticio de recompra con DARWIN. Entiende su objetivo, evaluación y límites sin atribuir precisión a datos reales.', '/architecture': 'Conoce la arquitectura de DARWIN: Flask, preparación de datos, modelos de scikit-learn y resultados temporales aislados por sesión.'}

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
    origin = SITE_URL or safe_url("https://"+os.getenv("RAILWAY_PUBLIC_DOMAIN","")) or request.url_root.rstrip("/")
    return dict(seo_description=PUBLIC_DESCRIPTIONS.get(request.path, 'Demostración pública de DARWIN · WUNSCE. Usa solo datos ficticios.'), social_image=origin + '/static/img/og-wunsce.png', wunsce_url=WUNSCE_URL, csrf_token=csrf_token, models=MODELS, feature_labels=FEATURE_LABELS, steps=STEPS, canonical_url=origin+request.path if request.endpoint in ("home","features","case_study","architecture") else None, demo_page=request.endpoint in ("product_app","download","download_input","reset_demo"))


def cleanup_results():
    for path in RUNTIME_DIR.glob("*.json"):
        if re.fullmatch(r"[a-f0-9]{32}",path.stem):
            try:
                if time.time()-path.stat().st_mtime>app.config["RESULT_TTL"]:
                    path.unlink()
            except FileNotFoundError:
                pass


def result_path():
    identifier = session.get("result_id", "")
    return RUNTIME_DIR/(identifier+".json") if re.fullmatch(r"[a-f0-9]{32}",identifier) else None


def load_result():
    if "result" in g:
        return g.result
    cleanup_results()
    path = result_path()
    try:
        result = json.loads(path.read_text(encoding="utf8")) if path else None
    except (FileNotFoundError,json.JSONDecodeError):
        result = None
    if result is None:
        session.pop("result_id",None)
    g.result = result
    return result


def save_result(result):
    cleanup_results()
    if len(list(RUNTIME_DIR.glob("*.json")))>=app.config["MAX_RESULTS"]:
        abort(503)
    identifier = secrets.token_hex(16)
    path = RUNTIME_DIR/(identifier+".json")
    temporary = path.with_suffix(".part")
    try:
        temporary.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding="utf8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    old = result_path()
    session["result_id"] = identifier
    session.permanent = True
    if old:
        old.unlink(missing_ok=True)


def read_config():
    values = {k:request.form.get(k,"").strip() for k in ("n","seed","model")}
    if not re.fullmatch(r"[0-9]{1,4}",values["n"]) or not re.fullmatch(r"[0-9]{1,6}",values["seed"]):
        raise ValidationError("Clientes y semilla deben ser enteros dentro de los límites indicados.")
    return Config(int(values["n"]),int(values["seed"]),values["model"])


@app.get("/")
def home():
    return render_template("home.html")


@app.get("/features")
def features():
    return render_template("features.html")


@app.get("/case-study")
def case_study():
    return render_template("case_study.html")


@app.get("/architecture")
def architecture():
    return render_template("architecture.html")


@app.get("/health")
def health():
    try:
        with tempfile.TemporaryFile(dir=RUNTIME_DIR) as probe:
            probe.write(b"ok")
    except OSError:
        return jsonify(status="unavailable",service="darwin-web"),503
    return jsonify(status="ok",service="darwin-web")


@app.route("/app", methods=["GET","POST"])
def product_app():
    global LAST_TRAIN
    result = load_result()
    values = result["config"] if result else {"n":1500,"seed":42,"model":"logistic"}
    error = None
    code = 200
    if request.method=="POST":
        values = {k:request.form.get(k,"") for k in ("n","seed","model")}
        try:
            config = read_config()
            if result and result["config"]=={"n":config.n,"seed":config.seed,"model":config.model}:
                return redirect(url_for("product_app")+"#results")
            if time.time()-session.get("last_train",0)<app.config["TRAIN_COOLDOWN"]:
                abort(429)
            if not TRAIN_LOCK.acquire(blocking=False):
                abort(503)
            try:
                if time.monotonic()-LAST_TRAIN<app.config["MIN_TRAIN_INTERVAL"]:
                    abort(429)
                cleanup_results()
                if len(list(RUNTIME_DIR.glob("*.json")))>=app.config["MAX_RESULTS"]:
                    abort(503)
                LAST_TRAIN = time.monotonic()
                result = run_experiment(config)
                result["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                save_result(result)
                session["last_train"] = time.time()
            finally:
                TRAIN_LOCK.release()
            return redirect(url_for("product_app")+"#results")
        except ValidationError as exc:
            error = str(exc)
            code = 422
    selected = request.args.get("segment", "")
    if selected and selected not in ("High","Medium","Low"):
        abort(404)
    predictions = [r for r in result["predictions"] if not selected or r["segment"]==selected] if result else []
    return render_template("app.html",result=result,values=values,error=error,selected=selected,preview=predictions[:20],matched_count=len(predictions)),code


@app.post("/download")
def download():
    result = load_result()
    if not result:
        abort(410)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output,fieldnames=list(result["predictions"][0]))
    writer.writeheader()
    writer.writerows(result["predictions"])
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),as_attachment=True,download_name="darwin_synthetic_holdout_predictions.csv",mimetype="text/csv")


@app.post("/download-input")
def download_input():
    result = load_result()
    if not result:
        abort(410)
    df = raw_dataset(Config(**result["config"]))
    df["data_source"] = "synthetic_demo"
    return send_file(io.BytesIO(df.to_csv(index=False).encode("utf-8-sig")),as_attachment=True,download_name="darwin_synthetic_input.csv",mimetype="text/csv")


@app.post("/reset-demo")
def reset_demo():
    path = result_path()
    if path:
        path.unlink(missing_ok=True)
    session.pop("result_id",None)
    session.pop("csrf",None)
    flash("Tu ejecución demo se eliminó. Puedes generar otro experimento.","success")
    return redirect(url_for("product_app"))


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(410)
@app.errorhandler(413)
@app.errorhandler(429)
@app.errorhandler(500)
@app.errorhandler(503)
def error_page(error):
    messages = {400:"El formulario no es válido. Vuelve a abrir la demo.",404:"Esta página o clasificación no existe.",410:"Tu resultado venció o se borró. Ejecuta de nuevo la demo.",413:"La solicitud supera el límite de 4 KB.",429:"Espera unos segundos antes de entrenar otro experimento.",500:"No se pudo completar el experimento. Vuelve a intentarlo.",503:"La demo está ocupada o sin espacio temporal. Inténtalo más tarde."}
    return render_template("error.html",code=error.code,message=messages[error.code]),error.code


@app.errorhandler(OSError)
def storage_error(_):
    return render_template("error.html",code=503,message="El almacenamiento temporal no está disponible. Inténtalo más tarde."),503


if __name__=="__main__":
    port = int(os.getenv("PORT") or "8000")
    if not 1<=port<=65535:
        raise ValueError("Invalid PORT")
    app.run(host="0.0.0.0",port=port,debug=False)
