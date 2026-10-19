# Convergencia de cálculos de manganeso

Extractor de energías finales y señales de finalización en salidas de Quantum ESPRESSO. Convierte un conjunto de salidas en una tabla para estudios de convergencia.

**Área:** Física computacional · **Estado:** Herramienta CLI con prueba sintética

## Uso

```bash
python extraer.py
```

## Alcance y limitaciones

JOB DONE indica finalización del programa y no garantiza convergencia electrónica ni exactitud física. El extractor informa ambos indicadores por separado. Los originales de investigación permanecen locales.

## Siguiente desarrollo

Asociar parámetros de entrada, pseudopotenciales y tolerancias de energía para comparar costo y precisión.

[Volver al portafolio](../../README.md)
