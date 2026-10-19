# Applied Data Lab en Railway

El laboratorio conserva sus cuatro aplicaciones HTML/CSS/JavaScript. Caddy sirve únicamente `dist/`; los archivos de análisis se procesan dentro del navegador. No requiere base de datos, volumen, claves API ni carga de archivos al servidor.

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
cd demos-web
node test.mjs
railway up --project <id-del-proyecto> --service juan-serena-data-lab --environment production --detach
```

Con Docker instalado, construir desde esta carpeta y probar un puerto alternativo:

```bash
docker build -t juan-serena-data-lab .
docker run --rm -e PORT=8090 -p 8090:8090 juan-serena-data-lab
```

Comprobar `/`, `/app.mjs`, `/core.mjs` y `/style.css`, el MIME JavaScript de los módulos, las cuatro herramientas, la descarga JSON y un 404. Los assets tienen caché de cinco minutos; el HTML requiere revalidación.

La publicación previa en Sites se conserva durante la migración. Las actualizaciones del portafolio deben apuntar al dominio Railway comprobado. Los datos que un visitante seleccione no se envían al servicio de alojamiento para análisis.

[Código e instrucciones](README.md) · [Portafolio](../README.md)
