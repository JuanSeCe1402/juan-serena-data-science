# Applied Data Lab en Railway

El laboratorio conserva sus cuatro aplicaciones HTML/CSS/JavaScript. Caddy sirve únicamente `dist/`; los archivos de análisis se procesan dentro del navegador. No requiere base de datos, volumen, claves API ni carga de archivos al servidor.

**URL pública verificada:** [https://juan-serena-data-lab-production.up.railway.app/](https://juan-serena-data-lab-production.up.railway.app/)

## Configuración del servicio

- Proyecto: WUNSCE; servicio independiente `juan-serena-data-lab`.
- Entorno: production; una réplica.
- Repositorio: `JuanSeCe1402/juan-serena-data-science`; rama `main`.
- Root Directory: `/demos-web`; Dockerfile: `Dockerfile`.
- Inicio: el CMD del Dockerfile, sin sobrescritura.
- Healthcheck: `/`, timeout 60 segundos.
- Puerto: variable `PORT` de Railway; 8080 por defecto. El dominio público debe apuntar a ese puerto.
- Watch pattern: `/demos-web/**`.

El contenedor ejecuta Caddy con usuario 1000 y valida su configuración al construir. Railway termina HTTPS en el proxy; Caddy atiende HTTP dentro del servicio. El panel de administración de Caddy está deshabilitado.

Las rutas de herramientas usan fragmentos (`/#cortex`, `/#movilidad`, `/#espectros`, `/#stix`), conservados al cambiar de dominio. Las rutas de archivos inexistentes devuelven 404; no se reemplazan por HTML, para evitar ocultar errores al cargar módulos JavaScript.

## Verificar o desplegar

```bash
# Desde la raíz del repositorio
node demos-web/test.mjs
railway up --project 14e204d8-0276-4b58-9a9e-6f6a2acaacfc --service juan-serena-data-lab --environment production --detach
```

Con Docker instalado, construir desde esta carpeta y probar un puerto alternativo:

```bash
docker build -t juan-serena-data-lab .
docker run --rm -e PORT=8090 -p 8090:8090 juan-serena-data-lab
```

Comprobar `/`, `/app.mjs`, `/core.mjs` y `/style.css`, el MIME JavaScript de los módulos, las cuatro herramientas, la descarga JSON y un 404. Los assets tienen caché de cinco minutos; el HTML requiere revalidación.

La publicación previa en Sites se conserva durante la migración. Las actualizaciones del portafolio deben apuntar al dominio Railway comprobado. Los datos que un visitante seleccione no se envían al servicio de alojamiento para análisis.

[Código e instrucciones](README.md) · [Portafolio](../README.md)

## Validación de la migración — 19 de octubre de 2026

Railway completó el despliegue `fb7170b7-ce49-480d-9b18-2a2a6cccdccf` desde el commit `98db69f262cdc7d36a9c4c2d52277bb3e1558911`. La construcción validó Caddy y el healthcheck de `/` pasó.

Se verificaron por HTTPS, con validación normal de certificados de Windows, las cuatro rutas de archivos (`/`, `/app.mjs`, `/core.mjs`, `/style.css`): HTTP 200, contenido idéntico al repositorio mediante SHA-256 y MIME correcto. Cinco rutas inexistentes o de archivos de configuración devolvieron 404.

En el navegador se comprobaron las cuatro demos: Cortex mostró $125.64 con sus parámetros iniciales; movilidad, 240 viajes; espectros, 301 pares y máximo en X=1552; STIX, ocho objetos, cinco indicadores y un patrón repetido. Se ejecutó `node test.mjs` con sus casos de lógica e inválidos.

La fuente GitHub está configurada en `main`, con raíz `/demos-web`. El despliegue inicial terminó correctamente, pero la creación del disparador automático fue rechazada por Railway porque su integración de GitHub no tiene acceso autorizado a este repositorio. Por ello no se afirma que los pushes futuros desplieguen automáticamente.

Para habilitar autodeploy, el titular debe conceder a la aplicación de Railway acceso al repositorio en GitHub y conectar el disparador de `main` en Railway. No se ampliaron permisos de cuenta durante esta migración. Hasta entonces, actualizar mediante `railway up` desde la raíz del checkout, como se indica arriba; el Root Directory del servicio limita la construcción a `/demos-web`.
