> Referencia operativa adaptada del proyecto original. Para comprobaciones de esta incorporación ver [VALIDACION](../../VALIDACION.md). Los ejemplos de despliegue no acreditan un despliegue ejecutado desde este portafolio; su CI comprueba suites locales, sin desplegar servicios.

# FREY · Demo pública de costos y precios

[Abrir FREY](https://proyectos/frey-production.up.railway.app/)

FREY ayuda a explorar cuánto cuesta un lote y qué precio cubre un margen objetivo.
Presenta costo total, costo unitario, margen sobre venta, precio sugerido y utilidad
bruta estimada. Los ejemplos son ficticios; no son métricas, resultados ni clientes.
El lore de la balanza queda como contexto secundario de marca.

## Probar sin datos reales

En `/app` elige «lote de piezas» o «servicio». Edita los supuestos y calcula.
Usa solo valores hipotéticos; no pongas nombres de personas ni información de clientes.
Todos los importes corresponden al **lote completo**, en MXN, sin impuestos ni descuentos.
La cantidad divide los totales, no multiplica otra vez los costos.

Ejemplo reproducible: materiales 250, trabajo 300, máquina 180, energía 40, indirectos
120, merma 5 %, cantidad 10 y margen objetivo 30 %. Costo total 934.50, costo unitario
93.45, precio del lote 1335.00, utilidad bruta estimada 400.50. Estas son salidas del
cálculo con esos supuestos, no resultados comerciales.

## Fórmulas y redondeo

- Base = materiales + trabajo + máquina + energía + indirectos.
- Merma = base × porcentaje / 100, redondeo HALF_UP a centavos.
- Total = base + merma. Costo unitario = total / cantidad.
- Precio del lote = total / (1 − margen / 100), redondeado hacia arriba al centavo.
- Utilidad bruta estimada = precio del lote − total.
- El margen se calcula sobre la venta, **no es markup/recargo sobre costo**.
- Las referencias unitarias se redondean a dos decimales por separado; multiplicarlas
  puede dar diferencias de centavos. El importe de referencia es el total del lote.

El motor usa Decimal y valida en servidor: costos 0 a 1,000,000 por concepto, al menos
un costo positivo, cantidad entera 1 a 100000, merma 0–100 %, margen 0–95 %, hasta dos
decimales. Acepta punto o coma decimal sin separadores de miles. Rechaza negativos,
NaN, infinito, notación exponencial, datos incompletos y márgenes imposibles.

FREY no comprueba costos omitidos, demanda, competencia ni impuestos. La utilidad
mostrada no es utilidad neta. El PDF es un escenario demostrativo, no una oferta.

## Local · Python 3.12

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python app.py
```

Abre http://127.0.0.1:8000. `.env` no sobrescribe variables del proceso.
Sin SECRET_KEY local se usa clave efímera; reiniciar invalida la sesión.

```bash
python -m pytest -q
python -m pip check
python tools/verify_deploy.py --server flask
# Linux
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') gunicorn app:app
python tools/verify_deploy.py --server gunicorn
# Con Docker instalado
python tools/verify_deploy.py --server docker
```

## Seguridad y PDF

CSRF en los dos formularios, cookie HttpOnly/SameSite=Lax, Secure en Railway/HTTPS,
sesión de 30 minutos y límite de solicitud 16 KB. SECRET_KEY aleatoria estable de al
menos 32 caracteres obligatoria en Railway. Debug desactivado, CSP self, protección
contra framing, nosniff y resultados/PDF/health sin caché ni indexación.

El navegador no decide los totales del PDF. `/quote` solo usa entradas normalizadas
de la sesión firmada y **recalcula** con el mismo motor. Nombre escapado en Jinja y
en Paragraph de ReportLab, máximo 80 caracteres y sin controles. No se guardan PDFs
ni archivos de datos en disco; PDF en memoria. El nombre y supuestos se conservan en
la cookie firmada, que no está cifrada: nunca introducir datos sensibles. No hay
cuentas ni control distribuido de abuso; son controles básicos de una demo pequeña.

PDF con tablas, entradas, supuestos, fórmulas, comparaciones y paginación. Texto
extraíble y layout revisado por renderizado. No se afirma conformidad PDF/UA.

## Railway y dominio futuro

Repo central: Root Directory `/proyectos/frey` y configuración `/proyectos/frey/railway.toml`.
En uploads CLI solo de esta carpeta usar `railway up ./proyectos/frey --path-as-root
--service wunsce-frey --detach` desde la raíz del repo.

Docker Python 3.12, appuser sin root; CMD `gunicorn app:app`. Gunicorn lee PORT y
escucha `0.0.0.0`, fallback 8000, un worker y dos hilos. Healthcheck `/health`: HTTP
200 con `service=frey-web`. No necesita BD, volumen ni subida de archivos.
Variables: SECRET_KEY, SITE_URL (origen HTTPS), WUNSCE_URL (retorno) y PORT (Railway).
La CLI avisa migrar railway.toml a IaC antes del 1 de diciembre de 2026.

Para usar `frey.wunsce.com`, añadir dominio al servicio, aplicar el registro DNS que
Railway indique y esperar HTTPS. Después cambiar SITE_URL y, cuando corresponda,
WUNSCE_URL al dominio corporativo. No se modifican DNS ni se asume dominio comprado.

## UX y accesibilidad

Inicio explica primero el problema; los ejemplos usan el motor real. Formularios por
pasos con labels, ayudas y errores que conservan entradas; foco visible, skip-link,
menú con Escape/aria-expanded, retorno Back to WUNSCE visible incluso en móvil y
tablas con captions y desplazamiento por teclado. Paleta, tipografía y marca FREY
conservadas. Ver `docs/REVISION_PRODUCCION.md` para evidencias y límites.


## SEO público y lanzamiento

Las cuatro páginas públicas (inicio, funcionalidades, caso y arquitectura) tienen
metadescripciones distintas, canonical, Open Graph y Twitter Card. La imagen
social reutiliza la identidad WUNSCE existente, alojada dentro de la aplicación.
`/sitemap.xml` incluye solo esas cuatro URLs; `/robots.txt` anuncia el sitemap.
Se conserva `noindex` en las demos y en errores: los datos y las descargas no
forman parte del sitemap. El origen sigue definido mediante `SITE_URL`.
Las pruebas `tests/test_public_seo.py` verifican estos contratos y el recurso PNG.
