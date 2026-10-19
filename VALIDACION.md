# Validación y límites

La preparación del portafolio se realizó el 19 de octubre de 2026. Las fechas históricas de archivos no se usan como prueba de ejecución o autoría.

## Comprobaciones automatizadas

Ejecutar desde la raíz:

```bash
python3 herramientas/verificar.py
```

Verifica sintaxis de todos los archivos `.py`, existencia de enlaces Markdown locales, ejemplos sintéticos y casos de datos inválidos de las cuatro herramientas CLI nuevas. Incluye diferencias entre finalización y convergencia en Quantum ESPRESSO, pares no finitos en espectros, duraciones inválidas y patrones duplicados/ausentes en STIX.

Las herramientas de movilidad, espectros, convergencia y STIX solo requieren la biblioteca estándar. La demo de estadística requiere NumPy, SciPy y Matplotlib y se comprueba por separado cuando esas dependencias están disponibles.

## Fuera de estas comprobaciones

- Ejecución completa de interfaces Tkinter, Pygame y OpenGL.
- Entrenamientos de redes neuronales y resultados del manuscrito de bioimpedancia.
- Exactitud física, calibración experimental, publicación científica y validación clínica.
- Compatibilidad de versiones de las dependencias históricas.
- Integración de fragmentos HTML con un carrito de tienda real.

Un chequeo de sintaxis correcto no implica que un prototipo funcione o produzca resultados correctos. Las fichas de cada proyecto enumeran pendientes conocidos.

## Resultado de la preparación local

Se completaron las comprobaciones de sintaxis de 33 archivos Python, enlaces y las cuatro herramientas CLI. La demo estadística se ejecutó adicionalmente en un entorno local con NumPy, SciPy y Matplotlib, produjo JSON y una figura sintética. No se han fijado versiones de dependencias ni probado una instalación limpia.
