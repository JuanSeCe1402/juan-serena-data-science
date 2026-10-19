# Bioimpedancia multiescala e inferencia de parámetros

Proyecto de investigación sobre la conexión entre modelos microscópicos, impedancia macroscópica e inferencia de parámetros. Incluye el manuscrito y bloques de código recuperados, identificados como archivo de investigación.

**Área:** Biofísica y aprendizaje automático · **Estado:** Investigación exploratoria con ejecución pequeña reproducible

## Implementación recuperada y evaluación nueva

La carpeta [reproducible](reproducible/README.md) incorpora funciones de simulación multiescala, el generador temporal de 600 variables y la arquitectura BioNet recuperados de una versión local más desarrollada. Una capa nueva de evaluación separa entrenamiento, validación y prueba antes de normalizar y compara con una referencia constante. Los módulos multiescala y temporal son exploraciones distintas; no se afirma que formen un único simulador validado.

Incluye una vía Ridge y otra PyTorch. Los ejemplos JSON documentan ejecuciones de solo 15 muestras para comprobar el flujo; no son estimaciones de rendimiento científico. Se excluyeron las bases y checkpoints anteriores.

```bash
cd proyectos/bioimpedancia/reproducible
python -m pip install -r requirements.txt
python -m unittest -v
python experimento.py --muestras 30 --modelo ridge
```

## Alcance y limitaciones

No hay validación clínica ni experimental acreditada. Los bloques del manuscrito pueden depender entre sí y no son aplicaciones independientes. Las métricas del manuscrito no se han reproducido. Los ejemplos nuevos describen únicamente su ejecución sintética y sus particiones.

## Siguiente desarrollo

Revisar unidades y geometría de impedancia, estudiar identificabilidad y efecto del ruido y recortes numéricos, y reproducir figuras con experimentos independientes más amplios.

[Volver al portafolio](../../README.md)
