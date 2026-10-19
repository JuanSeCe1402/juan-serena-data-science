# NANA · Limpieza y perfilado de datos

**Ingeniería de datos · Python · pandas · SQLite · Flask**

[Probar demo](https://wunsce-nana-production.up.railway.app/app) · [Motor de transformación](core.py) · [Pruebas del núcleo](tests/test_core.py)

![Perfil de columnas de NANA](../../docs/capturas/nana.png)

## Problema

Un CSV puede contener encabezados inconsistentes, filas duplicadas y valores ausentes. Antes de analizarlo o llevarlo a una base de datos, conviene conocer qué se transformó y qué necesita revisión.

## Implementación

- Normalización y desambiguación de encabezados, tratamiento de marcadores de faltantes y eliminación de duplicados.
- Inferencia conservadora de tipos: preserva identificadores y evita conversiones parciales que descarten valores.
- Perfil de columnas con tipos, faltantes y valores únicos; vista previa y exportación CSV/SQLite.
- Descargas ligadas a la sesión y neutralización de prefijos de fórmulas en el CSV.

## Evidencia y decisiones

El ejemplo incluido pasa de **6 registros a 5** al retirar un duplicado y conserva **2 valores faltantes** para revisión. No inventa datos para completar las celdas. La suite de la incorporación aprobó **30 casos**, con comprobaciones de transformación, aislamiento, salidas e interfaz. [Alcance de validación](../../VALIDACION.md).

**Límite:** la demo pública procesa solo el ejemplo ficticio incluido. Su índice combina completitud y unicidad; no mide exactitud semántica. Las fechas ambiguas y los identificadores se conservan. El siguiente paso es ampliar los casos de prueba de formatos locales y documentar reglas por dominio.

## Ejecutar localmente

Python 3.12 recomendado. Cada aplicación es independiente: no mezclar sus dependencias ni importar sus módulos desde la raíz.

```bash
cd proyectos/nana
python -m venv .venv
# Activar .venv según el sistema
python -m pip install -r requirements-dev.txt
python -m pytest -q
python app.py
```

Abrir http://127.0.0.1:8000. Consultar [OPERACION](OPERACION.md) para variables, arquitectura, recursos y límites. El Dockerfile se construye desde esta carpeta; no se activan despliegues desde este repositorio.

## Procedencia y aportación

Implementación del ecosistema WUNSCE del archivo personal del titular. Se incorpora una sola versión de sus fuentes, interfaz, recursos de marca, ejemplos sintéticos y pruebas. La organización, revisión y preparación pública tuvieron asistencia de Codex; no se atribuye autoría exclusiva sobre dependencias o componentes de terceros. No se copiaron bases, credenciales, adjuntos ni archivos de configuración privados.

La validación local no equivale a un despliegue nuevo, una certificación de seguridad ni un resultado comercial. Las integraciones externas no se acreditan por pruebas simuladas.

[Volver al portafolio](../../README.md)
