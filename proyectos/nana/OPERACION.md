> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# NANA · Primera demo pública de WUNSCE

NANA transforma un CSV sintético en datos estructurados, un reporte y descargas
CSV/SQLite. Conserva Flask, Jinja y pandas; no necesita base de datos externa.
Es una demo de I+D, no un servicio de tratamiento de datos reales ni un caso de cliente.

[Abrir demo pública](https://proyectos/nana-production.up.railway.app/app)

## Probar

1. Abre `/app` y pulsa **Procesar ejemplo sintético**.
2. Revisa duplicados, faltantes, encabezados y perfil de columnas.
3. Descarga CSV o SQLite desde la misma sesión. El botón **Back to WUNSCE**
   devuelve a la web principal.

El ejemplo contiene seis filas ficticias de productos (DEMO-001, etc.). No incluye
personas, contactos ni información de clientes. Está disponible en `/sample.csv`.
La demo pública **no acepta archivos propios**, aun cuando se envíe un POST manual.
No habilites UPLOADS_ENABLED en un servicio público. La opción interna existe solo
para futuras pruebas controladas y requiere medidas adicionales antes de exponerse.

## Local (Python 3.12)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python app.py
```

Abre http://127.0.0.1:8000. `.env` se carga sin sobrescribir variables del proceso.
En local, si no defines SECRET_KEY se genera una clave efímera: reiniciar invalida
sesiones anteriores. Para probar Gunicorn en Linux configura una clave estable.

```bash
python -m pytest -q
python -m pip check
python tools/verify_deploy.py --server flask
# Linux
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') gunicorn app:app
python tools/verify_deploy.py --server gunicorn
# Si Docker está instalado
python tools/verify_deploy.py --server docker
```

## Railway

- Repo central: Root Directory `/proyectos/nana`, config `/proyectos/nana/railway.toml`.
  Si despliegas solo esta carpeta, usa raíz `/`.
- Dockerfile Python 3.12, usuario sin privilegios; comando `gunicorn app:app`.
  `gunicorn.conf.py` escucha en `0.0.0.0:$PORT`, fallback 8000; un worker, dos hilos.
- Healthcheck `/health` → 200, JSON `status=ok`, `service=nana-web`.
- **SECRET_KEY obligatorio**, aleatorio de al menos 32 caracteres; no incluirlo en Git.
  Generar con `python -c "import secrets; print(secrets.token_hex(32))"`.
- `SITE_URL`: origen HTTPS del dominio público actual, sin ruta.
- `WUNSCE_URL`: URL de retorno, actualmente la web principal en Railway.
- Una réplica, sin volumen: archivos temporales locales. Las descargas no se comparten
  entre réplicas. No escalar horizontalmente sin rediseñar almacenamiento y sesiones.
- La CLI actual avisa migrar railway.toml a IaC antes del 1 de diciembre de 2026.

## Preparado para nana.wunsce.com

Añade `nana.wunsce.com` como dominio del servicio en Railway, crea exactamente el
registro DNS que Railway indique y espera el certificado HTTPS. Después cambia
`SITE_URL=https://nana.wunsce.com`. Cambia `WUNSCE_URL=https://wunsce.com` cuando la
web corporativa tenga su dominio listo. No hay nombres de host embebidos en rutas,
assets ni cookies; cookies sin Domain para aislamiento del subdominio. No apuntar
DNS antes de configurar y verificar el servicio. Dominio y DNS no se crean aquí.

## Seguridad y límites de demo

- CSRF en POST, cookie HttpOnly/SameSite=Lax y Secure en Railway/HTTPS.
- Descargas ligadas a sesión firmada y UUID exacto; cache no-store y noindex.
- TTL de descarga 30 minutos; limpieza al entrar en demo o descargar, y eliminación
  al reiniciar/desplegar. No hay garantía de borrado en reposo exactamente al minuto
  30 si no hay tráfico. No hay almacenamiento persistente ni archivos de entrada guardados.
- Hasta cinco ejecuciones retenidas por sesión, cooldown de tres segundos y máximo
  de 100 carpetas temporales. Límite de solicitud 1 MB; 2000 filas y 50 columnas.
  Son límites básicos de una demo, no un sistema distribuido contra abuso/DoS.
- Salida CSV neutraliza cadenas que comienzan con fórmulas; SQLite conserva el texto.
- Encabezados únicos, consultas de pandas/SQLite, HTML escapado, errores sin detalles
  internos, CSP self, frame-ancestors none y nosniff. Depuración desactivada.
- No logs de datos ni nombres de archivos cargados. Access logs contienen rutas HTTP.

El índice orientativo se calcula sobre esta ejecución: 65 % completitud del resultado
+ 35 % unicidad del archivo original. No mide exactitud, validez semántica ni beneficio
comercial. No se publican métricas de clientes. Las fechas ambiguas, formatos locales,
separadores de miles e identificadores se conservan para revisión, sin inventar valores.

## Accesibilidad y UX

Etiquetas claras, botón de ejecución con dataset incluido, estados de error, skip-link,
foco visible, menú con aria-expanded/Escape, tablas con captions y desplazamiento
horizontal accesible. Paleta WUNSCE conservada, imagen de marca local optimizada,
responsive y movimiento reducido. Lighthouse no sustituye lector de pantalla y teclado
manual. Revisar `docs/REVISION_PUBLICA.md` para evidencias y límites de validación.


## SEO público y lanzamiento

Las cuatro páginas públicas (inicio, funcionalidades, caso y arquitectura) tienen
metadescripciones distintas, canonical, Open Graph y Twitter Card. La imagen
social reutiliza la identidad WUNSCE existente, alojada dentro de la aplicación.
`/sitemap.xml` incluye solo esas cuatro URLs; `/robots.txt` anuncia el sitemap.
Se conserva `noindex` en las demos y en errores: los datos y las descargas no
forman parte del sitemap. El origen sigue definido mediante `SITE_URL`.
Las pruebas `tests/test_public_seo.py` verifican estos contratos y el recurso PNG.
