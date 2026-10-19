> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# Operación digital de consultorio · ESCULAPIO

Web pública, caso de estudio y copia administrativa revisada con datos demo. Coordina atención inicial administrativa, agenda, pacientes, mensajes y seguimiento humano. **No realiza diagnóstico, tratamiento ni recomendaciones clínicas automatizadas.** No es un expediente clínico.

## Procedencia y arquitectura

La base encontrada usa **FastAPI**, no Flask. Se conserva FastAPI + Jinja + SQLAlchemy y los módulos existentes de agenda, conversación y mensajería. Gunicorn ejecuta `app:app` mediante `uvicorn_worker.UvicornWorker` (ASGI); un worker WSGI de Flask no sirve para esta aplicación.

Se copiaron únicamente fuentes de `archivo local original`. `Consultorio AZUL` contiene las mismas fuentes salvo configuración. Ambas carpetas originales permanecen intactas. No se copiaron sus archivos .env, bases de datos, respaldos, adjuntos ni credenciales. La configuración de esta copia se escribió desde cero. La web Node del consultorio existente y su servicio Railway no se modificaron.

## Dos modos diferentes

### Demo pública (predeterminado)

- `DEMO_MODE=true`, `INTEGRATIONS_ENABLED=false`, `ENABLE_JOBS=false`.
- Seleccionar doctor/asistente en `/demo` es una **simulación de rol**, no autenticación de una clínica real. El servidor aplica sus permisos a la base demo de esa sesión.
- SQLite temporal independiente por cookie firmada. Hasta 50 espacios por instancia y 100 registros por tabla controlada. El límite incluye bitácora y mensajes; no es un control distribuido contra abuso.
- Caducidad fija de 30 minutos y limpieza oportunista al acceder a la demo. Reinicios/despliegues pueden borrar antes; no hay garantía de purga exacta sin solicitudes posteriores. «Cerrar y eliminar mi demo» borra únicamente el espacio propio.
- Solo alias `Paciente Demo 01`–`Paciente Demo 99` e identificadores ficticios `00000001`–`00000099`; no son números de WhatsApp. Sin edades, notas clínicas, adjuntos ni texto libre de mensajes. Las respuestas administrativas se eligen de una lista.
- Webhook, envío de agenda y acceso a adjuntos deshabilitados en la demo. Las funciones de transporte devuelven simulación sin abrir conexiones externas, aunque existieran credenciales en el entorno.
- Los mensajes demo quedan con estado **simulated**, nunca como entregados a una persona real. El simulador de eventos muestra la solicitud humana y el comportamiento del bot pausado.
- Sin volumen, datos reales, campañas, trabajos programados ni restauración de bases de un consultorio en esta demostración.

### Instalación privada (requiere preparación propia)

`DEMO_MODE=false` elimina la selección pública de roles. El panel exige HTTP Basic sobre HTTPS con usuarios distintos y hashes de contraseña configurados en el servidor. Los roles doctor/asistente se obtienen del servidor; una cookie o campo de formulario no permite elegirlos.

| Acción | Asistente | Doctor |
| --- | --- | --- |
| Consultar agenda, pacientes, calendario y buzón | Sí | Sí |
| Crear/reprogramar/cancelar citas y registrar asistencia | Sí | Sí |
| Registrar respuesta administrativa | Sí | Sí |
| Cambiar horarios/excepciones | No | Sí |
| Eliminar pacientes o mensajes/conversaciones | No | Sí |
| Pausar/reanudar manualmente el bot | No | Sí |

Usar `ADMIN_USER`, `ADMIN_PASSWORD_HASH` y opcionalmente `ASSISTANT_USER`, `ASSISTANT_PASSWORD_HASH`. No se aceptan contraseñas predeterminadas conocidas ni hashes de bajo coste. Se admiten scrypt con N≥32768, r≥8, p≥1 o PBKDF2-SHA256 con ≥600000 iteraciones. Para generar un hash sin escribir la contraseña en argumentos o historial:

```bash
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Contraseña: ')))"
```

Guardar el hash solamente como secreto de entorno. Hay límite de intentos fallidos por IP en una instancia; no sustituye SSO/MFA, un proxy de autenticación ni controles distribuidos. El panel privado requiere HTTPS y debe restringirse al equipo autorizado.

**No conectar datos reales por el solo hecho de activar este modo.** Antes se requieren migración revisada sobre una copia, almacenamiento persistente y permisos, respaldo/restauración comprobados, política de retención, privacidad y validación del canal externo. Esta revisión no certifica cumplimiento sanitario ni sustituye una revisión de operación privada.

## Agenda y handoff

- Reservas serializadas mediante bloqueo local y transacción `BEGIN IMMEDIATE` en SQLite. Claves foráneas y restricciones activadas. Tipos y duraciones controlados; horarios fuera de disponibilidad no se reservan.
- El horizonte máximo de reserva es 90 días. Las fechas, horas, días de trabajo, duración y referencias se validan.
- Citas versionadas. Reprogramar, cancelar o registrar asistencia rechaza formularios desactualizados; SQLAlchemy también detecta escrituras concurrentes sobre una versión anterior.
- Una solicitud humana pausa el bot. Los mensajes nuevos se guardan, pero no disparan respuestas automáticas mientras permanezca pausado.
- Vaciar un chat conserva pausa manual y nunca reactiva el bot. Solo el rol doctor puede reanudarlo explícitamente.
- Reactivación automática desactivada por defecto y obligatoriamente en cero para la demo. En modo privado existe la opción temporizada: solo puede aplicarse a solicitudes humanas ya atendidas; la pausa manual nunca vence automáticamente.
- La agenda PDF requiere acceso, usa nombres de archivo únicos para evitar mezclas entre sesiones, marca la demo y se elimina tras la respuesta de descarga. No hay documentos en static.

## Integraciones

El código conserva el adaptador de WhatsApp. La demo lo mantiene apagado; no se realizaron llamadas a cuentas reales. Se probaron firma HMAC-SHA256, integridad del cuerpo, identificación del canal, lotes de eventos, duplicados y errores de transporte con respuestas simuladas.

Una instalación privada solo puede habilitar `INTEGRATIONS_ENABLED=true` con versión de API aprobada, ID de número, token, token de verificación y secreto de aplicación configurados. La firma es obligatoria; los eventos deben pertenecer al ID de canal esperado. Se limita el cuerpo a 32 KB y se procesan lotes de hasta 50 eventos, con identificadores únicos para evitar reprocesamiento de mensajes.

La descarga de adjuntos tiene otra compuerta `ALLOW_MEDIA_DOWNLOAD=false` por defecto, límite de tamaño y destinos HTTPS restringidos. No se habilitó aquí. Los errores del proveedor se almacenan de forma genérica, sin cuerpo de respuesta ni tokens. No se atribuye un envío o entrega real a las pruebas simuladas.

`ENABLE_JOBS=false` por defecto. En privado, activarlo requiere una sola réplica/worker y revisar horarios, destinatarios y retención de recordatorios, agenda y backups. El respaldo SQLite usa la API de backup; no se probó una restauración de datos reales. Una prueba de extremo a extremo con el proveedor y destinatarios autorizados sigue siendo necesaria antes de usar un canal real.

## Local

Python 3.12. Desde `wunsce-esculapio/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Abrir `http://127.0.0.1:8000`. En Linux/macOS usar `source .venv/bin/activate` y `cp .env.example .env`. Generar una clave aleatoria estable de 32 caracteres o más para `SECRET_KEY`. Localmente la demo admite una efímera; Railway y modo privado requieren una configurada. No subir .env ni hashes/credenciales a Git.

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Firma de sesión y CSRF; clave aleatoria estable ≥32 caracteres. |
| `DEMO_MODE` | `true` predeterminado. SQLite por sesión, alias ficticios y transportes externos prohibidos. |
| `INTEGRATIONS_ENABLED` | `false` predeterminado. No se permite `true` con demo activa. |
| `ENABLE_JOBS` | `false`; prohibido en demo. |
| `PORT` | Puerto proporcionado por Railway, 8000 local por defecto; rango 1–65535. |
| `SITE_URL` | Origen público HTTPS para canonical y cookies seguras. |
| `WUNSCE_URL` | Destino Back to WUNSCE; web principal en Railway por defecto. |
| `ESCULAPIO_RUNTIME_DIR` | Directorio privado, escribible por el usuario del contenedor y fuera de static. |
| `TIMEZONE` | `America/Mexico_City` por defecto. |
| `DATABASE_URL` | Solo modo privado; ignorada en demo. Esta entrega verifica SQLite en una instancia, no escalado a PostgreSQL. |

Ver `.env.example` para los nombres de configuración privada y del proveedor. En privado, montar almacenamiento duradero fuera de static y comprobar sus permisos antes de iniciar. No hay migraciones destructivas automáticas: una base con esquema antiguo hace fallar el arranque con aviso de migración requerida. Nunca ensayar migraciones sobre la única copia de una base real.

## Seguridad y accesibilidad

CSRF en formularios y solicitudes JSON, cookies HttpOnly/SameSite=Lax/Secure en Railway/HTTPS, consultas parametrizadas, SQL sin valores de parámetros en logs, auditoría de acciones sin nombres/teléfonos/cuerpos de mensaje y errores públicos sin trazas ni entradas reflejadas. Límite de formularios de 16 KB también con transferencia por fragmentos; no-store/noindex en pantallas de datos. Gunicorn no registra URLs de acceso para evitar teléfonos en logs. Las notificaciones de escritorio muestran texto genérico.

Recursos del mismo origen, CSP sin scripts inline, sin fuentes de Google ni terceros. Hay foco visible, enlace de salto, etiquetas, controles de movimiento alternativos a arrastrar, navegación por teclado, calendario con controles nativos y objetivos táctiles ampliados. Se conserva la paleta del panel; la web pública usa la identidad WUNSCE. Las auditorías automáticas no equivalen a una certificación WCAG ni a una sesión manual completa con lector de pantalla.

## Pruebas y Railway

```bash
python -m pip check
python -m pytest -q
python tools/verify_deploy.py --server uvicorn
# Linux o contenedor:
gunicorn app:app --check-config
gunicorn app:app
python tools/verify_deploy.py --server gunicorn
python tools/verify_deploy.py --server docker
```

Gunicorn requiere Linux/Unix; el smoke Uvicorn local en Windows no se presenta como prueba de Gunicorn. El modo Docker construye y ejecuta la imagen con un PORT alternativo y comprueba usuario no root. El CI Ubuntu ejecuta estas verificaciones para las seis aplicaciones.

`GET /health` responde 200 con `{"service":"esculapio-web","status":"ok"}` cuando el runtime es escribible y SQLite responde (en privado consulta la base configurada); 503 si falla. No crea espacios demo, no expone credenciales ni certifica integraciones externas.

Railway: servicio separado, Root Directory `/proyectos/esculapio` si se conecta a GitHub, Start Command vacío. Dockerfile Python 3.12 slim, usuario no root, `gunicorn app:app` y worker ASGI configurado, un worker/una réplica, escucha `0.0.0.0:$PORT`, healthcheck `/health`.

Desde la raíz central:

```bash
railway up ./proyectos/esculapio --path-as-root --service wunsce-esculapio --detach
```

Para el dominio futuro `esculapio.wunsce.com`, configurar dominio/DNS/TLS y después `SITE_URL`. No se modificaron DNS en esta entrega. El servicio público actual usa datos demo y no recibe volúmenes ni secretos de los consultorios existentes.

Ver [el informe de revisión](docs/REVISION_PRODUCCION.md) para resultados y límites de las comprobaciones ejecutadas.


## SEO público y lanzamiento

Las cuatro páginas públicas (inicio, funcionalidades, caso y arquitectura) tienen
metadescripciones distintas, canonical, Open Graph y Twitter Card. La imagen
social reutiliza la identidad WUNSCE existente, alojada dentro de la aplicación.
`/sitemap.xml` incluye solo esas cuatro URLs; `/robots.txt` anuncia el sitemap.
Se conserva `noindex` en las demos y en errores: los datos y las descargas no
forman parte del sitemap. El origen sigue definido mediante `SITE_URL`.
Las pruebas `tests/test_public_seo.py` verifican estos contratos y el recurso PNG.
