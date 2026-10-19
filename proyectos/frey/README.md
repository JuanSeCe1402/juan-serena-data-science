# Costos, márgenes y escenarios — FREY

Motor con Decimal, costo por lote, margen sobre venta, escenarios y PDF. Las entradas son hipotéticas y la utilidad mostrada es bruta estimada.

**Estado:** implementación recuperada para portafolio con pruebas automatizadas; ver el alcance y resultados en [VALIDACION](../../VALIDACION.md).

## Ejecutar localmente

Python 3.12 recomendado. Cada aplicación es independiente: no mezclar sus dependencias ni importar sus módulos desde la raíz.

```bash
cd proyectos/frey
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
