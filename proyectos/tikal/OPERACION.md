> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# Operaciones para pequeñas empresas · TIKAL

Demo pública de WUNSCE para explorar clientes ficticios, pedidos, inventario y tareas en un entorno ligero. La función operativa es el mensaje principal; TIKAL, «La Ciudad que Recuerda», conserva su lugar como identidad de marca.

**Lead → Quote → Order → Production → Delivered → Paid**

Cada pedido empieza en Lead y avanza una etapa por acción explícita. Los botones registran estados: no generan cotizaciones, ejecutan producción, realizan entregas ni procesan pagos. Solo Paid se suma como importe registrado cobrado; Delivered permanece pendiente de cobro. Los importes son ejemplos, no resultados comerciales verificados.

## Alcance de la demo

- Datos iniciales enteramente ficticios y señalados como demo. No introducir datos reales, personales o sensibles.
- Cada navegador recibe su propia SQLite temporal mediante una sesión firmada. Ningún identificador de registro permite consultar otra sesión.
- Caducidad fija de 30 minutos; limpieza oportunista en las siguientes solicitudes de datos. Un reinicio o despliegue puede borrar los datos antes. No se garantiza borrado en un instante exacto sin nuevas solicitudes.
- «Reiniciar mi demo» elimina únicamente el espacio de esa sesión y vuelve a cargar ejemplos.
- Máximo 50 registros por módulo y 100 espacios temporales por instancia. Solicitudes limitadas a 16 KB. Son límites de recursos, no un sistema distribuido contra abuso.
- Clientes con prefijo `Demo ` y correos opcionales con dominio `.test`; sin teléfono. Responsables limitados a equipos ficticios. Esto reduce la captura accidental de datos personales, pero el usuario sigue siendo responsable del texto que introduce.
- Inventario con stock entero no negativo y alerta cuando stock ≤ mínimo. Ajuste absoluto manual, sin reservas, descuentos automáticos, relación de materiales ni movimientos contables.
- Tareas Pending → In Progress → Done, fecha opcional y enlace opcional a un pedido del mismo espacio. Los vencimientos usan la fecha del servidor.
- Los estados y ajustes incluyen comprobaciones de versión para rechazar formularios desactualizados con 409.

No utilizar como sistema real de clientes o contabilidad. Para una operación persistente se requieren autenticación, permisos por empresa, almacenamiento duradero, respaldo, auditoría y reglas de negocio adicionales. Esta demo no verifica cobros bancarios ni presta servicios fiscales.

## Desarrollo local

Python 3.12 recomendado. Desde `wunsce-tikal/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python app.py
```

Abrir `http://127.0.0.1:8000`. En Linux/macOS, activar con `source .venv/bin/activate` y copiar con `cp .env.example .env`. Generar una clave local con `python -c "import secrets; print(secrets.token_hex(32))"` y guardarla exclusivamente en `.env`, nunca en Git. Sin clave configurada se genera una efímera para desarrollo.

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Clave aleatoria estable de al menos 32 caracteres; obligatoria en Railway. No compartir ni publicar. |
| `PORT` | Puerto de escucha; Railway lo proporciona. Local: 8000 por defecto. Gunicorn valida rango 1–65535. |
| `SITE_URL` | Origen público HTTPS sin ruta para canonical y cookies seguras; p. ej. `https://tikal.wunsce.com` después de configurar dominio y TLS. |
| `WUNSCE_URL` | Destino de «Back to WUNSCE». Por defecto, web principal en Railway. |
| `TIKAL_RUNTIME_DIR` | Directorio temporal privado opcional, fuera de `static/`. Por defecto, `wunsce_tikal_demo` en el temporal del sistema. |

No configurar un volumen para esta demo. No usar información sensible como datos de prueba. No habilitar debug público.

## Pruebas y arranque

```bash
python -m pip check
python -m pytest -q
python tools/verify_deploy.py --server flask
# Linux o contenedor:
gunicorn app:app --check-config
gunicorn app:app
python tools/verify_deploy.py --server gunicorn
python tools/verify_deploy.py --server docker
```

Gunicorn requiere Unix/Linux. En Windows, el smoke test Flask comprueba HTTP real; no demuestra arranque de Gunicorn. El modo Docker construye la imagen, comprueba el CMD con un PORT alternativo y verifica que el usuario no sea root. Requiere Docker instalado y activo. El CI `.github/workflows/railway-checks.yml` ejecuta estas verificaciones en Ubuntu.

`GET /health` devuelve 200 y `{"service":"tikal-web","status":"ok"}` si SQLite responde y el directorio temporal es escribible; devuelve 503 si falla. No inicializa un espacio demo ni expone secretos. No es una comprobación de capacidad disponible para nuevos visitantes.

## Datos, seguridad y arquitectura

Se mantiene Flask + Jinja + CSS/JS propios + SQLite. `database.py` define esquema, índices y datos demo; `validation.py` valida campos; `app.py` gestiona rutas y sesiones. Las claves foráneas están activadas y las restricciones SQL refuerzan estados y cantidades. Los importes se guardan como centavos enteros y se formatean con Decimal para evitar errores de coma flotante.

Las consultas usan parámetros. Inserciones y cambios se realizan en transacciones; el control de capacidad usa `BEGIN IMMEDIATE`. Los formularios requieren CSRF; la sesión usa HttpOnly, SameSite=Lax y Secure en Railway/HTTPS. Se renueva el token al iniciar o reiniciar un espacio. Jinja escapa HTML, se aplica CSP con recursos del mismo origen, se bloquea el enmarcado y las pantallas de datos usan no-store/noindex. Los errores públicos no exponen trazas. Sin servicios de email, analítica externa ni procesador de pagos.

La demo está diseñada para una réplica, un worker Gunicorn y dos hilos. No compartir esta arquitectura de archivos temporales entre réplicas. Para crecimiento y datos persistentes, planificar una base de datos compartida con autenticación y permisos; no basta con añadir un volumen a la demo pública.

Las tablas permiten desplazamiento horizontal local en móvil; formularios y pipeline se reorganizan. Hay enlaces de salto, foco visible, menú con `aria-expanded`, etiquetas de formulario, errores anunciados, estados escritos y navegación de retorno visible. Las comprobaciones automatizadas no sustituyen una auditoría manual completa con lectores de pantalla y teclado.

## Railway

Crear servicio independiente, no modificar los otros servicios. Para desplegar únicamente esta aplicación desde la raíz del repositorio central:

```bash
railway up ./proyectos/tikal --path-as-root --service wunsce-tikal --detach
```

Como alternativa GitHub, configurar Root Directory `/proyectos/tikal`. El `Dockerfile` usa Python 3.12 slim, dependencias fijadas, usuario sin privilegios y `CMD ["gunicorn", "app:app"]`. `gunicorn.conf.py` escucha en `0.0.0.0:$PORT`. `railway.toml` selecciona Dockerfile y `/health`; no sobreescribir el comando de arranque en el panel. Configurar `SECRET_KEY`, `SITE_URL` y `WUNSCE_URL`. El puerto del dominio público debe coincidir con PORT (8080 en el servicio actual).

Para `tikal.wunsce.com`, añadir primero el dominio en Railway, configurar los registros DNS indicados y comprobar TLS; después actualizar `SITE_URL`. Este repositorio no modifica DNS. La CLI actual advierte sobre la retirada del soporte de `railway.toml` el 1 de diciembre de 2026: migrar a la configuración admitida por Railway antes de esa fecha.

El original del escritorio `WUNSCE_TIKAL_FULL_WEBSITE_RAILWAY/WUNSCE_TIKAL_WEB` se conserva. La versión mantenida está en `WUNSCE_CENTRAL_REPOSITORY/WUNSCE/proyectos/tikal`.

Consultar [la revisión de producción](docs/REVISION_PRODUCCION.md) para evidencias del despliegue y límites pendientes.


## SEO público y lanzamiento

Las cuatro páginas públicas (inicio, funcionalidades, caso y arquitectura) tienen
metadescripciones distintas, canonical, Open Graph y Twitter Card. La imagen
social reutiliza la identidad WUNSCE existente, alojada dentro de la aplicación.
`/sitemap.xml` incluye solo esas cuatro URLs; `/robots.txt` anuncia el sitemap.
Se conserva `noindex` en las demos y en errores: los datos y las descargas no
forman parte del sitemap. El origen sigue definido mediante `SITE_URL`.
Las pruebas `tests/test_public_seo.py` verifican estos contratos y el recurso PNG.
