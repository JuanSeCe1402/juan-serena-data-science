> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# WUNSCE — Main Website
### Analytics & Environments

Official main website for the WUNSCE ecosystem.

## Included
- Home page
- Services
- Projects / portfolio
- Individual project pages
- Brand story / About
- Contact page
- Responsive design
- Configurable live project links
- Dockerfile
- Railway configuration
- `/health` endpoint

## Local run
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open:
`http://127.0.0.1:8000`

## Railway environment variables
Add these as your projects go live:

```text
CONTACT_EMAIL=
CONTACT_WHATSAPP=
GITHUB_URL=
LINKEDIN_URL=

ESCULAPIO_URL=
NANA_URL=
FREY_URL=
TIKAL_URL=
DARWIN_URL=
```

The project cards automatically show the live link when the corresponding variable is configured.

## Suggested deployment structure
```text
wunsce.com
nana.wunsce.com
frey.wunsce.com
tikal.wunsce.com
darwin.wunsce.com
esculapio.wunsce.com
```

You can initially use Railway-generated domains and later connect custom domains.

## Portfolio integrity
Project statuses intentionally distinguish:
- CLIENT PROJECT / PRODUCTION
- WUNSCE R&D
- WUNSCE LAB

Do not change R&D/LAB projects to client deployments unless that is actually true.


## Revisión y ejecución (Python 3.12 recomendado)

El Python 3.8 instalado en algunos equipos no es compatible con estas dependencias.
Usa Python 3.12 para crear el entorno virtual. Gunicorn se utiliza en Linux/Docker;
en Windows ejecuta `python app.py` para desarrollo.

Copia `.env.example` a `.env` y completa únicamente tus valores reales. La aplicación
carga ese archivo automáticamente; las variables del proceso tienen prioridad.
Las URLs deben incluir `https://` o `http://`. Los números de WhatsApp deben usar
código de país; también se aceptan espacios, paréntesis y el signo +.
Los enlaces vacíos o con esquemas inválidos no se publican. No hay formulario de
contacto ni envío de correo: los botones abren los canales configurados.

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip check
python app.py
```

## Deploy en Railway

La raíz del servicio debe ser la carpeta que contiene `app.py`, `Dockerfile` y
`railway.toml`. Si subes la carpeta contenedora original, configura Root Directory
como `/proyectos/wunsce-web`. Si subes el contenido de esta carpeta como repositorio,
usa la raíz del repositorio.

1. Selecciona el repositorio y la raíz correcta.
2. Usa el Dockerfile incluido. Quita cualquier Start Command configurado manualmente:
   el CMD ejecuta `gunicorn app:app`; `gunicorn.conf.py` lee PORT directamente.
3. Añade las variables de `.env.example` directamente en Railway. No subas `.env`.
4. Genera un dominio público y comprueba `/health`, `/services` y `/projects`.
5. `/health` debe responder 200 con `{"status":"ok","service":"wunsce-main"}`.

El proceso escucha en `0.0.0.0:$PORT`, o en 8000 si PORT no existe. Railway utiliza
`/health` antes de activar el deploy. Los logs de Gunicorn se envían a stdout/stderr.
La imagen corre como usuario sin privilegios y copia solo aplicación, templates y
recursos estáticos; excluye secretos y pruebas.

Para verificar la imagen en un equipo con Docker:

```powershell
docker build -t wunsce-main .
docker run --rm --env-file .env -e PORT=8080 -p 8080:8080 wunsce-main
# Desde otra terminal:
Invoke-RestMethod http://127.0.0.1:8080/health
```


## SEO y accesibilidad para producción

Configura `SITE_URL` como origen público definitivo: esquema y dominio, sin ruta,
parámetros ni credenciales (por ejemplo `https://tu-dominio.com`). Esta variable
es la fuente para canonical, Open Graph, datos estructurados y sitemap.
Si está vacía, se utiliza `RAILWAY_PUBLIC_DOMAIN`; en local, el origen de la petición.
Para un dominio personalizado en Railway, define SITE_URL expresamente.
Una configuración inválida genera un error para evitar publicar URLs incorrectas.

- `/sitemap.xml`: las diez páginas públicas; excluye `/health` y errores.
- `/robots.txt`: permite rastreo y anuncia el sitemap; excluye `/health`.
- `/favicon.ico`, PNG 192 y Apple Touch Icon derivados del emblema actual.
- Open Graph y Twitter Card con imagen local de 1200 × 630.
- Título y descripción por página; canonical sin parámetros de seguimiento.
- JSON-LD Organization/WebSite sin inventar dirección, valoraciones o perfiles.
- 404 real con opciones para volver; `noindex` en errores y health.

El enlace “Saltar al contenido”, el foco visible, el estado del menú, las áreas
para pulsar y los estilos de reflujo mejoran navegación por teclado y móvil.
Los encabezados estáticos en inglés están marcados con `lang="en"`.
La navegación sigue disponible sin JavaScript. La paleta original permanece;
se reutiliza oliva para textos pequeños con mejor contraste sobre fondos claros.
No se ha eliminado ninguna sección.

Verificación: 51 pruebas; navegador a 320, 768 y 1280 px, sin desbordamiento horizontal
en las diez páginas y la 404. Menú móvil probado al abrir y cerrar con Escape.
Esto no constituye una certificación integral WCAG ni una prueba con lector de pantalla.
Después del deploy, comprueba las URLs de metadatos y envía `/sitemap.xml` a Search Console.
No se ha publicado automáticamente el sitio.


## Comprobación reproducible de Railway

Desde esta carpeta (la raíz configurada del servicio), con Python 3.12 en Linux:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip check
gunicorn app:app --check-config
python tools/verify_deploy.py --server gunicorn
python tools/verify_deploy.py --server docker
```

La última comprobación construye el Dockerfile, arranca su CMD sin sobrescribirlo,
injecta PORT=18765, espera HTTP 200 en /health, comprueba siete rutas/recursos y
verifica usuario sin privilegios. Elimina solo su propio contenedor al terminar.
El tag local `wunsce-verify:<pid>` queda disponible para inspección.
La comprobación Gunicorn arranca `python -m gunicorn app:app` en un puerto libre.
En Windows, `--server flask` comprueba HTTP local, pero no sustituye Gunicorn/Docker.

`gunicorn.conf.py` hace que `gunicorn app:app` escuche en `0.0.0.0:$PORT`,
con fallback 8000. No requiere expansión de variables por shell. El comando del
Dockerfile es exec-form, por lo que Gunicorn recibe directamente las señales.
No configures un Start Command manual en Railway.

El workflow central `../.github/workflows/railway-checks.yml` ejecuta pruebas y las dos
comprobaciones en Ubuntu al subir el repositorio. Su existencia no implica que
se haya ejecutado: verifica el resultado de Actions antes de desplegar.


## Hub del ecosistema (19 de octubre de 2026)

La home, el directorio y las fichas usan un catálogo común. La función es el
encabezado principal; NANA, DARWIN, TIKAL, FREY y ESCULAPIO conservan su identidad,
ilustraciones y lore. La sección `/#ecosistema` explica sus funciones con un mapa
adaptable, un ejemplo de negocio y enlaces a las fichas.

Configura en el servicio **wunsce-main** las URLs públicas de `.env.example`:

| Variable | Destino |
| --- | --- |
| `NANA_URL` | Demo de transformación de datos |
| `DARWIN_URL` | Demo de analítica predictiva con datos sintéticos |
| `TIKAL_URL` | Demo operativa con datos ficticios |
| `FREY_URL` | Demo de costos y precios |
| `ESCULAPIO_URL` | Caso de estudio y acceso a la demo administrativa |
| `ESCULAPIO_IMPLEMENTATION_URL` | Opcional: web profesional publicada del Dr. Jonathan |

No hay dominios de despliegue incrustados en templates. Se aceptan únicamente
URLs HTTP(S) sin credenciales; una URL vacía o inválida oculta su CTA externo y
muestra «Enlace público no configurado». La ficha interna permanece disponible.
Los enlaces se resuelven al servir la página; los cambios de variables en Railway
requieren aplicar el despliegue correspondiente. No son comprobaciones de uptime:
los estados describen el alcance publicado y deben actualizarse si este cambia.

El mapa representa capacidades complementarias, no conexiones automáticas ni
intercambio de datos entre demos. ESCULAPIO diferencia la web profesional real de
la demo administrativa independiente; WhatsApp operativo no se da por verificado.
Las imágenes de las fichas son ilustraciones de marca existentes, no capturas de
producto. No se añadieron métricas comerciales, testimonios ni clientes ficticios.

Validación de esta actualización: 81 pruebas, smoke HTTP local y cinco destinos
públicos con HTTP 200. Revisión visual a 320 px y escritorio, menú móvil y ausencia
de desbordamiento a 320 y 1024 px. Lighthouse móvil local: rendimiento 99,
accesibilidad 100, buenas prácticas 100 y SEO 100; medición de laboratorio. Se
corrigió además una discordancia entre el nombre accesible y el texto de los
enlaces «Conocer proyecto». Los informes se conservan fuera del repositorio.

Publicación verificada: despliegue Railway
`1353b648-e586-4d81-816b-a099b15ba3bb` SUCCESS; home, cinco fichas y `/health`
responden 200. Los cinco CTA y el enlace independiente a la web de Jonathan se
comprobaron en el HTML público. Lighthouse móvil sobre Railway: **100 / 100 / 100 /
100** (rendimiento, accesibilidad, buenas prácticas, SEO); la comprobación de
etiquetas accesibles también pasa. Informe local:
`archivo local original`.

El CI del commit `818c3ad` pasó en las seis aplicaciones, incluyendo Gunicorn y
build/arranque Docker en Ubuntu:
https://github.com/JuanSeCe1402/wunsce/actions/runs/39305781509.
La revisión posterior `d6f6e01` añade solo el encabezado accesible del directorio.

Para publicar con la configuración actual de este servicio (`Root Directory =
/proyectos/wunsce-web`), ejecuta `railway up --service wunsce-main` desde la raíz del
monorepo. No subas la carpeta con `--path-as-root`: el servicio necesita conservar
el prefijo `proyectos/wunsce-web/` en el archivo enviado.


## Canales de contacto de lanzamiento

`CONTACT_PHONE` habilita un enlace `tel:` y acepta un número internacional sin
letras. `CONTACT_WHATSAPP` configura el enlace de WhatsApp y `GITHUB_URL` el perfil
público. Los valores se proporcionan como variables del servicio; el correo solo
se muestra si `CONTACT_EMAIL` está configurado. La página evita tarjetas vacías o
canales anunciados como próximos cuando ya hay medios reales disponibles.
