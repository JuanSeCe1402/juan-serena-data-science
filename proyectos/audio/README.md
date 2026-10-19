# Análisis de audio

Archivo de un prototipo de carga, análisis espectral, temporal y armónico. Se separó el archivo monolítico en módulos para conservar su estructura prevista.

**Área:** Procesamiento de señales · **Estado:** Prototipo incompleto

## Entorno

Python 3.10 o posterior. Crea un entorno virtual e instala `requirements.txt` desde esta carpeta. Las dependencias históricas no se han fijado a versiones comprobadas. Tkinter puede requerir un paquete del sistema.

## Alcance y limitaciones

No se validaron compatibilidades de dependencias. El recomendador histórico mezcla escalas de amplitud y dB y referencia métodos ausentes; no debe usarse para recomendaciones de ecualización, auriculares o volumen. No se afirma que reproduzca una curva Harman validada.

## Siguiente desarrollo

Validar primero señales sintéticas, canales y frecuencia de muestreo; revisar unidades antes de formular recomendaciones.

[Volver al portafolio](../../README.md)
