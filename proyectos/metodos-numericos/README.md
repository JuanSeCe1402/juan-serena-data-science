# Métodos numéricos: interpolación y ecuaciones diferenciales

Colección de Lagrange, interpolación inversa, ajuste exponencial y Runge–Kutta de cuarto orden. Conecta ejercicios recuperados en Python y Fortran con una API pequeña y contrastes analíticos.

**Estado:** adaptación Python comprobada; fuentes Fortran recuperadas sin compilación verificada.

```bash
cd proyectos/metodos-numericos
python metodos.py
python -m unittest -v
```

Solo requiere la biblioteca estándar de Python 3.11+. `lagrange` usa forma baricéntrica; `inversa` requiere una tabla estrictamente monótona y no permite extrapolar. El ajuste exponencial minimiza errores en log(y); no equivale a mínimos cuadrados sobre y. La estabilidad y el error de RK4 dependen de la ecuación y del paso; no se afirma que resuelva problemas rígidos.

## Procedencia

El trabajo académico original de interpolación identifica como coautores a **Raul Alfonso Cano Villegas y Juan Manuel Serena Ceceña**. Se conserva su fuente en [archivo/interpolacion_original.py.txt](archivo/interpolacion_original.py.txt), sin números de matrícula. La API y pruebas actuales son adaptaciones nuevas preparadas con asistencia de Codex: eliminan entrada interactiva y variables globales, validan puntos y contrastan polinomios y soluciones conocidas. No se atribuye autoría exclusiva del ejercicio original.

Las fuentes Fortran de epidemia logística, contaminantes y salmuera están en [fortran](fortran/README.md). Sus títulos describen ejercicios de EDO, no modelos predictivos validados de sistemas reales.

[Volver al portafolio](../../README.md)
