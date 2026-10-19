> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# Analítica predictiva para negocio · DARWIN

Demo pública de WUNSCE para entender un experimento de predicción de recompra con datos enteramente sintéticos. Mantiene Flask + Jinja, pandas y scikit-learn; DARWIN y el lore de adaptación son identidad secundaria.

**Dataset → Cleaning → Features → Model → Evaluation → Prediction → Business Action**

## Qué muestra

- Entrada: historial ficticio de pedidos, gasto (MXN demo), ticket medio, días desde última compra, descuentos, devoluciones y categorías. IDs `DEMO-00001`; sin nombres, correos ni personas reales.
- Objetivo: `repurchased`, etiqueta binaria simulada para recompra en los siguientes 30 días. Es una hipótesis del generador, no una observación de clientes reales.
- Modelos: regresión logística o Random Forest. La interfaz explica el modelo elegido y sus parámetros.
- Evaluación: accuracy, precision, recall, F1, ROC-AUC, matriz de confusión y accuracy de referencia mayoritaria; todas calculadas durante la ejecución.
- Predicción: solo clientes del 25% reservado para evaluación, con score, clase predicha, etiqueta simulada, clasificación y sugerencia de revisión humana.
- Segmentos: **Low** si score < 0.35; **Medium** si 0.35 ≤ score < 0.70; **High** si score ≥ 0.70. Son señales de recompra, no de riesgo de abandono. La clase binaria usa un umbral distinto, 0.50.
- CSV del dataset de entrada y de todas las predicciones de evaluación. Incluyen `data_source=synthetic_demo`; las predicciones también `evaluation_set=held_out_test`.

No hay carga de archivos, captura de datos personales, importación de modelos, conexión con CRM, campañas ni decisiones automáticas. No introducir datos reales o sensibles. Las sugerencias de negocio son ejemplos para revisar con contexto.

## Método y límites

`core.py` genera datos reproducibles con semilla. El objetivo se simula con una función logística del historial y muestreo Bernoulli, con azar; esta relación artificial no demuestra relaciones de un negocio real. El dataset crudo añade un 1% de duplicados y valores faltantes conocidos en gasto y descuentos para demostrar limpieza.

1. Validar esquema y conservar IDs demo y objetivos binarios válidos; eliminar duplicados por ID.
2. Marcar valores históricos no finitos o fuera de rango como faltantes y derivar ticket medio por fila. Esta etapa no calcula estadísticas de población.
3. Dividir aleatoriamente por cliente: 75% entrenamiento, 25% prueba, estratificado por objetivo y con la semilla seleccionada.
4. Ajustar `SimpleImputer(strategy="median")` solo en entrenamiento. La regresión logística además ajusta `StandardScaler` solo en entrenamiento y usa `max_iter=1000`. Random Forest usa 100 árboles, profundidad máxima 6, mínimo 5 muestras por hoja y `n_jobs=1`.
5. Evaluar en prueba sin reajustar modelo, imputación o escalado. La referencia predice siempre la clase mayoritaria elegida en entrenamiento. Precision usa cero si no hay positivos predichos.
6. Mostrar scores únicamente del conjunto reservado. Nunca usar ID o `repurchased` como entradas ni mezclar predicciones de entrenamiento con resultados de evaluación.

Los umbrales son fijos; no se optimizan con prueba. No hay búsqueda de hiperparámetros, calibración adicional, validación temporal, intervalos de confianza, validación externa ni estudio de sesgo. Una sola partición estratificada no es una validación de pronóstico temporal. Un score no es garantía de recompra. Ni una accuracy ni un ROC-AUC de esta simulación acreditan precisión futura real. No se publican métricas comerciales estáticas ni resultados de clientes.

## Local

Python 3.12 recomendado. Desde `wunsce-darwin/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python app.py
```

Abrir `http://127.0.0.1:8000`. En Linux/macOS, `source .venv/bin/activate` y `cp .env.example .env`. Generar una clave con `python -c "import secrets; print(secrets.token_hex(32))"` y guardarla solo en `.env`. Sin clave local se genera una efímera; Railway exige una estable.

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Aleatoria, al menos 32 caracteres. Obligatoria en Railway; no subir a Git. |
| `PORT` | Railway lo proporciona. Por defecto 8000 local; rango válido 1–65535. |
| `SITE_URL` | Origen público HTTPS sin ruta, query ni fragmento; canonical y cookies seguras. |
| `WUNSCE_URL` | Enlace visible Back to WUNSCE. Por defecto, la web principal en Railway. |
| `DARWIN_RUNTIME_DIR` | Directorio temporal privado fuera de static. Por defecto, `wunsce_darwin_demo` en el temporal del sistema. |

Para `darwin.wunsce.com`, añadir primero dominio, DNS y TLS en Railway, verificarlo y después actualizar `SITE_URL`. Esta entrega no cambia DNS ni afirma que ese dominio ya esté activo.

## Seguridad y recursos

- Formularios CSRF, consultas de configuración con lista cerrada de modelos, 500–3000 clientes y semillas 0–999999. Solicitudes limitadas a 4 KB.
- Una sesión firmada guarda solo identificador opaco del resultado y control de frecuencia; el JSON permanece fuera de static. No se guardan ni cargan objetos pickle/joblib de modelos.
- Resultados separados por sesión y escritos de forma atómica; TTL fijo de 30 minutos y limpieza oportunista al acceder a resultados. Puede haber borrado antes por despliegue/reinicio. No se garantiza purga en un instante exacto sin solicitudes posteriores.
- Máximo 100 resultados temporales por instancia. Eliminar mi resultado afecta únicamente la sesión propia. Los resultados no se comparten mediante URL.
- Un entrenamiento simultáneo por proceso; dos segundos mínimos entre inicios globales y diez entre ejecuciones distintas de una sesión. La misma configuración reutiliza su resultado vigente. Una solicitud rechazada no realiza entrenamiento.
- Gunicorn: un worker, dos hilos, timeout 90 s; BLAS y forest limitados a un hilo durante entrenamiento. Una sola réplica; no añadir workers/réplicas sin rediseñar los límites y el almacenamiento compartido.
- Cookie HttpOnly, SameSite=Lax y Secure en Railway/HTTPS; CSP del mismo origen, no enmarcado, no-store/noindex en datos y errores públicos sin trazas. La sesión no autentica usuarios reales.
- Los CSV se generan en el servidor desde resultados sintéticos propios; no se devuelven contenidos arbitrarios enviados por formularios.

Para operar sobre datos reales hacen falta autenticación y permisos, almacenamiento y respaldo, evaluación temporal representativa, calibración, revisión de sesgos y políticas de uso, control de abuso distribuido y seguimiento del modelo. Esta demo no sustituye ese trabajo.

## Tests y despliegue

```bash
python -m pip check
python -m pytest -q
python tools/verify_deploy.py --server flask
# Linux:
gunicorn app:app --check-config
gunicorn app:app
python tools/verify_deploy.py --server gunicorn
# Docker instalado y activo:
python tools/verify_deploy.py --server docker
```

Gunicorn no funciona directamente en Windows. El smoke local Flask verifica HTTP, no Gunicorn. El modo Docker construye y ejecuta la imagen con PORT alternativo y verifica usuario no root. El CI central ejecuta cada aplicación por separado en Ubuntu.

`/health` devuelve 200 con `{"service":"darwin-web","status":"ok"}` cuando la aplicación ha importado sus dependencias y el directorio temporal es escribible; 503 si falla la escritura. No entrena un modelo ni afirma que haya capacidad para una ejecución nueva. Las pruebas del pipeline se ejecutan aparte.

Railway: servicio independiente con Root Directory `/proyectos/darwin` si se conecta a GitHub, Start Command vacío, Dockerfile y healthcheck `/health`. Desde la raíz del repositorio central se puede subir únicamente esta app:

```bash
railway up ./proyectos/darwin --path-as-root --service wunsce-darwin --detach
```

El Dockerfile usa Python 3.12 slim, dependencias fijadas, usuario sin privilegios y `CMD ["gunicorn", "app:app"]`. Gunicorn escucha en `0.0.0.0:$PORT`. Configurar clave estable, `SITE_URL`, `WUNSCE_URL` y el puerto público igual a PORT (8080 en el servicio actual). Sin volumen persistente para la demo. La CLI actual advierte sobre la retirada del soporte de `railway.toml` el 1 de diciembre de 2026; migrar la configuración antes de esa fecha.

El ZIP original `archivo local original` se conserva. La versión mantenida está en el repositorio central `WUNSCE/proyectos/darwin/`. Ver [la revisión de producción](docs/REVISION_PRODUCCION.md) para evidencias y alcance de las verificaciones.


## SEO público y lanzamiento

Las cuatro páginas públicas (inicio, funcionalidades, caso y arquitectura) tienen
metadescripciones distintas, canonical, Open Graph y Twitter Card. La imagen
social reutiliza la identidad WUNSCE existente, alojada dentro de la aplicación.
`/sitemap.xml` incluye solo esas cuatro URLs; `/robots.txt` anuncia el sitemap.
Se conserva `noindex` en las demos y en errores: los datos y las descargas no
forman parte del sitemap. El origen sigue definido mediante `SITE_URL`.
Las pruebas `tests/test_public_seo.py` verifican estos contratos y el recurso PNG.
