# DARWIN · Predicción de recompra con evaluación reproducible

**Machine learning aplicado · Python · pandas · scikit-learn · Flask**

[Probar demo](https://wunsce-darwin-production.up.railway.app/app) · [Núcleo del experimento](core.py) · [Pruebas del modelo](tests/test_core.py)

![Evaluación de DARWIN en una ejecución sintética](../../docs/capturas/darwin.png)

## Problema

Una predicción de recompra necesita contexto: de dónde salen las variables, qué clientes se reservaron y cómo se compara el modelo con una referencia sencilla. Este proyecto hace visible ese recorrido en una aplicación web.

## Implementación

- Generador reproducible de historiales ficticios y limpieza de entradas.
- Regresión logística y Random Forest, con imputación dentro de un Pipeline y escalado para la regresión logística.
- División estratificada 75/25 antes de ajustar el preprocesamiento; IDs y etiqueta excluidos de las variables.
- Métricas, matriz de confusión, scores y exportación de predicciones del conjunto reservado.

## Evidencia y decisiones

La suite incluye **63 casos aprobados** en la incorporación. Comprueba reproducibilidad, particiones disjuntas, ajuste del preprocesamiento solo con entrenamiento y recálculo de métricas, además de interfaz y configuración. [Alcance de validación](../../VALIDACION.md).

La referencia mayoritaria se elige en entrenamiento y se evalúa en la misma prueba. Los umbrales no se optimizan usando prueba. Esta separación hace inspeccionable el procedimiento, sin garantizar rendimiento fuera del generador.

**Límite:** tanto el historial como la recompra son sintéticos. La captura muestra una ejecución de regresión logística con 1500 clientes ficticios y semilla 42; no son resultados comerciales. La partición es aleatoria, no temporal. El siguiente paso sería evaluar sobre una fuente pública documentada con un diseño temporal adecuado.

## Ejecutar localmente

Python 3.12 recomendado. Cada aplicación es independiente: no mezclar sus dependencias ni importar sus módulos desde la raíz.

```bash
cd proyectos/darwin
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
