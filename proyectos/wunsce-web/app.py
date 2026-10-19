import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from lore import CHARACTERS, CHARACTERS_BY_SLUG
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, url_for, Response

# Existing process variables (including Railway) take precedence over .env.
load_dotenv(Path(__file__).with_name(".env"))


def web_url(name):
    value = os.getenv(name, "").strip()
    try:
        parsed = urlsplit(value)
        # Accessing .port also validates malformed/out-of-range ports.
        port = parsed.port
        if (parsed.scheme in {"http", "https"} and parsed.hostname
                and parsed.username is None and parsed.password is None
                and port != 0 and not any(c.isspace() for c in value)):
            return value
    except ValueError:
        pass
    return ""


def whatsapp_number(variable="CONTACT_WHATSAPP"):
    value = os.getenv(variable, "").strip()
    if not re.fullmatch(r"[+0-9 ()-]*", value):
        return ""
    digits = re.sub(r"[^0-9]", "", value)
    return digits if re.fullmatch(r"[1-9][0-9]{6,14}", digits) else ""


app = Flask(__name__)

PROJECTS = [
    {
        "slug": "esculapio",
        "name": "ESCULAPIO",
        "subtitle": "Operación digital de consultorio",
        "category": "SALUD DIGITAL",
        "status": "WEB PUBLICADA + DEMO ADMINISTRATIVA",
        "summary": "Una implementación vertical con web profesional publicada y una demo independiente de agenda, mensajes y seguimiento administrativo con datos ficticios.",
        "cta_label": "Ver caso de estudio",
        "ecosystem_action": "Aplicar a un consultorio",
        "ecosystem_summary": "Lleva las capacidades digitales a un contexto concreto: presencia profesional y demostración de operación administrativa.",
        "tagline": "Conectar la atención con una operación más clara.",
    },
    {
        "slug": "nana",
        "name": "NANA",
        "subtitle": "Entorno de transformación de datos",
        "category": "INGENIERÍA DE DATOS",
        "status": "DEMO PÚBLICA",
        "cta_label": "Explorar transformación de datos",
        "ecosystem_action": "Transformar datos",
        "ecosystem_summary": "Ordena archivos y convierte información inconsistente en una base estructurada para trabajar.",
        "summary": "Transforma archivos CSV inconsistentes en datos limpios y estructurados, listos para bases de datos, tableros y análisis.",
        "tagline": "Dar estructura a la información dispersa.",
    },
    {
        "slug": "frey",
        "name": "FREY",
        "subtitle": "Inteligencia de costos y precios",
        "category": "ANALÍTICA DE NEGOCIO",
        "status": "DEMO PÚBLICA",
        "cta_label": "Explorar costos y precios",
        "ecosystem_action": "Evaluar costos y precios",
        "ecosystem_summary": "Ayuda a comparar costos, margen, precio sugerido y utilidad antes de tomar una decisión comercial.",
        "summary": "Convierte los costos operativos en escenarios de margen, precios sugeridos y cotizaciones listas para compartir con tus clientes.",
        "tagline": "Entender el costo. Cuidar el margen. Dar valor al precio.",
    },
    {
        "slug": "tikal",
        "name": "TIKAL",
        "subtitle": "Entorno de operaciones de negocio",
        "category": "OPERACIONES",
        "status": "DEMO PÚBLICA · DATOS FICTICIOS",
        "cta_label": "Explorar operaciones",
        "ecosystem_action": "Organizar operaciones",
        "ecosystem_summary": "Da seguimiento a clientes, cotizaciones, pedidos, inventario y tareas del trabajo diario.",
        "summary": "Reúne clientes, pedidos, inventario y tareas en un espacio de trabajo ligero para entender y coordinar la operación diaria.",
        "tagline": "Ver cómo se mueve tu negocio.",
    },
    {
        "slug": "darwin",
        "name": "DARWIN",
        "subtitle": "Analítica predictiva de negocio",
        "category": "APRENDIZAJE AUTOMÁTICO",
        "status": "DEMO PÚBLICA · DATOS SINTÉTICOS",
        "summary": "Explora cómo un modelo aprende de datos sintéticos, evalúa sus predicciones y clasifica clientes en niveles High, Medium y Low. Muestra métricas calculadas en la demo.",
        "cta_label": "Explorar analítica predictiva",
        "ecosystem_action": "Analizar patrones",
        "ecosystem_summary": "Explora patrones y predicciones con datos sintéticos y resultados que se explican en lenguaje simple.",
        "tagline": "Aprender del pasado para elegir el siguiente paso.",
    },
]

# Same catalog feeds the home, directory, detail and ecosystem map.
PROJECTS.sort(key=lambda project: ("nana", "darwin", "tikal", "frey", "esculapio").index(project["slug"]))


def project_catalog():
    """Resolve deployment links from the environment; never invent a public URL."""
    catalog = []
    for source in PROJECTS:
        project = dict(source)
        project["url"] = web_url(project["slug"].upper() + "_URL")
        project["display_status"] = project["status"] if project["url"] else "ENLACE PÚBLICO NO CONFIGURADO"
        project["implementation_url"] = web_url("ESCULAPIO_IMPLEMENTATION_URL") if project["slug"] == "esculapio" else ""
        catalog.append(project)
    return catalog

SERVICES = [
    {
        "name": "Automatización y asistentes inteligentes",
        "short": "AUTOMATIZACIÓN",
        "summary": "Conectamos herramientas y simplificamos tareas repetitivas con flujos confiables y asistentes que acompañan tu operación.",
        "items": ["Flujos de WhatsApp", "Formularios y notificaciones", "Gestión de citas", "Integración de sistemas", "Asistentes internos"],
    },
    {
        "name": "Analítica y entornos de datos",
        "short": "ANALÍTICA",
        "summary": "Limpiamos, organizamos y analizamos tu información para convertirla en decisiones que puedas explicar y sostener.",
        "items": ["Limpieza de datos", "Entornos SQL", "Tableros de indicadores", "Indicadores clave", "Análisis de negocio"],
    },
    {
        "name": "Entornos digitales",
        "short": "ENTORNOS",
        "summary": "Diseñamos sitios web y herramientas de trabajo que responden a las necesidades reales de cada organización.",
        "items": ["Sitios web profesionales", "Paneles operativos", "Portales para clientes", "Flujos a la medida", "Publicación y despliegue"],
    },
]

PAGE_META = {
    "universe": ("Universo WUNSCE · Folklore, personajes y propósito", "Wus y Wis son los principios de WUNSCE. Descubre el lore de NANA, FREY, TIKAL, DARWIN y ESCULAPIO y su función en cada proyecto."),
    "home": ("WUNSCE · Automatización, analítica y entornos digitales", "Explora el ecosistema WUNSCE: transformación de datos, analítica predictiva, operaciones, costos y una implementación vertical de consultorio."),
    "services": ("Servicios de automatización y analítica · WUNSCE", "Asistentes inteligentes, integración de sistemas, limpieza de datos, dashboards y entornos digitales adaptados a tu operación."),
    "projects": ("Proyectos y ecosistema digital · WUNSCE", "Explora ESCULAPIO, NANA, FREY, TIKAL y DARWIN: proyectos de salud digital, datos, costos, operaciones e inteligencia."),
    "about": ("WUNSCE · Nuestra historia y filosofía", "Comprender, elegir y transformar. Conoce la historia de Wus y Wis y los principios que guían los sistemas de WUNSCE."),
    "contact": ("Contacto · Hablemos de tu proyecto · WUNSCE", "Cuéntanos qué proceso, datos o sistema quieres mejorar. Inicia una conversación con WUNSCE sobre automatización y entornos digitales."),
}


def site_origin():
    """Use the public origin explicitly, independently of proxy headers."""
    configured = web_url("SITE_URL")
    if configured:
        parsed = urlsplit(configured)
        if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("SITE_URL must be an HTTP(S) origin without path or credentials")
        return configured.rstrip("/")
    if os.getenv("SITE_URL", "").strip():
        raise ValueError("SITE_URL must be a valid absolute HTTP(S) origin")
    domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if domain and re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        return "https://" + domain
    return request.url_root.rstrip("/")


def public_url(endpoint, **values):
    return site_origin() + url_for(endpoint, **values)


@app.context_processor
def inject_seo():
    project = next((p for p in PROJECTS if p["slug"] == (request.view_args or {}).get("slug")), None)
    indexable = request.endpoint in PAGE_META or (request.endpoint == "project_detail" and project is not None)
    if request.endpoint == "project_detail" and project:
        title, description = project["subtitle"] + " · " + project["name"] + " · WUNSCE", project["summary"]
        canonical = public_url("project_detail", slug=project["slug"])
    elif request.endpoint in PAGE_META:
        title, description = PAGE_META[request.endpoint]
        canonical = public_url(request.endpoint)
    else:
        title, description = "Página no encontrada · WUNSCE", "La página que buscas no está disponible. Explora los servicios y proyectos de WUNSCE o vuelve al inicio."
        canonical = None
    origin = site_origin()
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": origin + "/#organization", "name": "WUNSCE Analytics & Environments", "url": origin + "/", "logo": public_url("static", filename="img/wunsce-emblem-transparent.png")},
        {"@type": "WebSite", "@id": origin + "/#website", "name": "WUNSCE Analytics & Environments", "url": origin + "/", "inLanguage": "es-MX", "publisher": {"@id": origin + "/#organization"}},
    ]}
    return dict(seo_title=title, seo_description=description, canonical_url=canonical,
                seo_indexable=indexable, social_image=public_url("static", filename="img/og-wunsce.png"), structured_data=schema)


@app.route("/sitemap.xml")
def sitemap():
    urls = [public_url(endpoint) for endpoint in PAGE_META]
    urls += [public_url("project_detail", slug=project["slug"]) for project in PROJECTS]
    return Response(render_template("sitemap.xml", urls=urls), mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nDisallow: /health\nSitemap: " + public_url("sitemap") + "\n", mimetype="text/plain")


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("img/favicon.ico")


@app.after_request
def response_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if response.status_code >= 400 or request.endpoint == "health":
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.context_processor
def inject_globals():
    return {
        "contact_email": os.getenv("CONTACT_EMAIL", ""),
        "contact_whatsapp": whatsapp_number(),
        "contact_phone": whatsapp_number("CONTACT_PHONE"),
        "linkedin_url": web_url("LINKEDIN_URL"),
        "github_url": web_url("GITHUB_URL"),
        "characters": CHARACTERS,
        "brand_principles": [CHARACTERS_BY_SLUG[slug] for slug in ("wus", "wis")],
        "project_characters": [CHARACTERS_BY_SLUG[project["slug"]] for project in PROJECTS],
        "characters_by_slug": CHARACTERS_BY_SLUG,
    }

@app.route("/")
def home():
    return render_template("home.html", projects=project_catalog(), services=SERVICES,
                           featured_project=featured_project())


def featured_project():
    """Publish only a complete, explicitly configured real demo."""
    fields = ("name", "function", "status", "problem", "solution", "cta_label", "screenshot_alt")
    project = {key: os.getenv("FEATURED_PROJECT_" + key.upper(), "").strip() for key in fields}
    project["cta_url"] = web_url("FEATURED_PROJECT_CTA_URL")
    screenshot = os.getenv("FEATURED_PROJECT_SCREENSHOT", "").strip()
    project["screenshot"] = web_url("FEATURED_PROJECT_SCREENSHOT")
    if not project["screenshot"] and screenshot:
        root = Path(app.static_folder).resolve()
        candidate = (root / screenshot).resolve()
        if (candidate.is_relative_to(root / "img") and candidate.is_file()
                and candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".avif"}):
            project["screenshot"] = url_for("static", filename=candidate.relative_to(root).as_posix())
    return project if all(project.values()) else None

@app.route("/services")
def services():
    return render_template("services.html", services=SERVICES)

@app.route("/projects")
def projects():
    return render_template("projects.html", projects=project_catalog())

@app.route("/projects/<slug>")
def project_detail(slug):
    project = next((p for p in project_catalog() if p["slug"] == slug), None)
    if not project:
        return render_template("404.html"), 404
    return render_template("project_detail.html", project=project)

@app.route("/universo")
def universe():
    return render_template("universe.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "wunsce-main"})

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT") or "8000")
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535")
    app.run(host="0.0.0.0", port=port)
