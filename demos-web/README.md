# Juan Serena — Applied Data Lab

Cuatro demos web: costos de impresión 3D, movilidad urbana, espectros e indicadores STIX. HTML/CSS/JavaScript sin dependencias de producción.

Los archivos se procesan localmente en el navegador, sin solicitudes de análisis a un servidor. Los ejemplos están etiquetados como sintéticos. Este alcance incluye carga, validación, métricas, visualización y exportación JSON; no equivale a validar los modelos académicos del portafolio.

## En línea

**[Abrir el laboratorio en Railway](https://juan-serena-data-lab-production.up.railway.app/)**

Código versionado en la rama `main` y servicio publicado en Railway. Las cuatro herramientas conservan sus rutas por fragmento. La activación de actualizaciones automáticas requiere conceder a la integración de Railway acceso a este repositorio. [Configuración y despliegue](RAILWAY.md).

## Pruebas

```bash
node test.mjs
```

## Vista local

```bash
python3 -m http.server 8765 --directory dist
```

Las funciones de `dist/core.mjs` se prueban por separado de la interfaz. No se necesitan claves API, cuentas ni datasets privados. La calculadora usa MXN y distingue recargo, margen e impuesto; no emite facturas.
