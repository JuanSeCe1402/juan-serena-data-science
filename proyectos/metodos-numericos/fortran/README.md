# Ejercicios de Runge–Kutta en Fortran

Fuentes académicas recuperadas: epidemia logística, concentraciones y salmuera. Su autoría y enunciados originales deben completarse antes de asignar una licencia de redistribución global. No son predicciones de fenómenos reales.

Se corrigió en `contaminantes.f95` la unidad de salida no inicializada mediante `newunit`, se cierra el archivo de Gnuplot y se reporta `t+h` al comparar concentraciones del paso siguiente. El criterio de cruce usa una tolerancia por paso, sin búsqueda de eventos continua. No se invoca automáticamente Gnuplot.

No se encontró gfortran disponible: estos programas no se compilaron en esta preparación. Con un compilador Fortran compatible:

```bash
gfortran -std=f2008 -Wall -Wextra -fcheck=all epidemia_logistica.f95 -o epidemia
./epidemia
```

Ejecutar desde una carpeta de trabajo separada: el ejercicio de contaminantes genera archivos de salida. Los contrastes analíticos de la implementación Python de RK4 se ejecutan por separado.

[Volver a métodos numéricos](../README.md)
