# Evaluación reproducible del modelo sintético de bioimpedancia

Las funciones físicas proceden de la versión local de la tesis con características temporales de 600 dimensiones. Se extrajeron de los scripts originales sin copiar sus bases, pickles, pesos, figuras ni ejecución automática. `modelo_multiescala.py` es una exploración aparte: no forma parte del generador temporal usado en este experimento.

La nueva capa `experimento.py`, preparada con asistencia de Codex, divide IDs antes de normalizar. Ajusta medias y desviaciones de X e y exclusivamente con entrenamiento, reserva validación y prueba, publica los IDs y compara contra la media de entrenamiento. No reutiliza particiones, escaladores ni checkpoints históricos. Esto corrige el procedimiento de evaluación; no valida el modelo físico ni reproduce resultados del manuscrito.

## Ejecución pequeña

Python 3.12 recomendado; desde esta carpeta:

```bash
python -m pip install -r requirements.txt
python -m unittest -v
python experimento.py --muestras 30 --semilla 42 --modelo ridge
```

El generador simula 50 ms con pasos de 0.02 ms por muestra y puede tardar. La salida JSON contiene MAE por parámetro, R² y referencia de media constante, junto con los IDs de cada conjunto. Una ejecución pequeña comprueba el flujo; sus métricas no son una estimación de rendimiento científico. Por defecto no guarda archivos. `--salida resultados/experimento.json` permite guardar uno nuevo sin reemplazar archivos existentes.

Para entrenar la arquitectura PyTorch recuperada, instalar además `requirements-torch.txt` y ejecutar `--modelo bionet --epochs 10`. El mejor estado se selecciona por validación; prueba permanece fuera de selección. Los pesos solo viven en memoria. La ejecución PyTorch se documenta por separado si se verifica; no se presume por haber probado Ridge.

## Supuestos pendientes de revisión

- La extracción recuperada resume temporalmente la parte real e imaginaria de Z; aplica ruido aditivo real y recortes numéricos en Hodgkin–Huxley. Debe estudiarse su efecto.
- La dependencia de conductividad con voltaje es una hipótesis exploratoria; que las variables cambien no prueba identificabilidad de los cinco parámetros.
- La interpretación de impedancia requiere revisar geometría y unidades; una expresión de inversa de conductividad no acredita por sí sola ohmios de una muestra real.
- Las funciones multiescala y temporal no se han contrastado experimentalmente. No se afirma que las cadenas del manuscrito constituyan un único simulador validado.
- No hay datos de pacientes, evaluación clínica ni aplicación diagnóstica.

[Volver a bioimpedancia](../README.md)
