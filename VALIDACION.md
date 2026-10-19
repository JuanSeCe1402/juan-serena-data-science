# Validación y límites

Revisión e incorporación: 19 de octubre de 2026. Las fechas históricas de archivos no se usan como prueba de ejecución o autoría.

## Resultados locales de la incorporación

| Suite | Casos aprobados | Alcance |
|---|---:|---|
| NANA | 30 | Núcleo, interfaz, demo pública, protección de salidas y metadatos |
| DARWIN | 63 | Generación, partición, preprocesamiento, métricas, interfaz y configuración |
| FREY | 57 | Cálculos, validación, interfaz, PDF y configuración |
| TIKAL | 60 | Flujos de clientes, pedidos, inventario y tareas, aislamiento y configuración |
| ESCULAPIO | 74 | Agenda, roles, concurrencia, pausa humana, transportes simulados e interfaz |
| Portal WUNSCE | 83 | Rutas, contacto, SEO, navegación y configuración |
| Métodos numéricos | 4 | Reproducción de polinomios, degeneración, inversa, ajuste y orden de RK4 |
| Bioimpedancia | 4 | Particiones completas/disjuntas, normalización sin información reservada y contrato de 600 variables |
| **Total** | **375** | Casos parametrizados de pytest y métodos de unittest |

Las seis suites de aplicaciones se ejecutaron por separado con Python 3.12.14 en Windows y dependencias ya instaladas, sin leer configuraciones privadas. ESCULAPIO se mantuvo en demo, sin integraciones ni trabajos externos. Los casos de WhatsApp verifican respuestas simuladas; no se enviaron mensajes reales. No se probó una instalación limpia de todos los requisitos durante esta incorporación.

La comprobación general revisa sintaxis de los módulos Python, vínculos Markdown y las cuatro demos CLI existentes con entradas inválidas. Se corrigió su lectura explícita en UTF-8 para Windows y se excluyen dependencias y cachés. La comprobación de publicación busca artefactos privados y ciertos formatos de secretos. Es una detección limitada y no una garantía de ausencia de información sensible.

```bash
python herramientas/verificar.py
python herramientas/comprobar_publicacion.py
python -m unittest discover -s proyectos/metodos-numericos -v
python -m unittest discover -s proyectos/bioimpedancia/reproducible -v
```

Para bioimpedancia instalar previamente su requirements.txt. Para cada aplicación instalar sus propios requisitos y ejecutar pytest desde su carpeta. El workflow de aplicaciones usa trabajos aislados; no despliega servicios. El resultado de GitHub Actions debe consultarse por ejecución y no se presume a partir de los resultados locales.

## Ejecuciones pequeñas de bioimpedancia

Se ejecutaron generador y evaluación con 15 muestras sintéticas, semilla 42, 600 variables y partición 9/3/3. Se guardan salidas de Ridge y BioNet en la carpeta reproducible. Ridge se ejecutó con Python 3.12.14, NumPy 2.5.4 y scikit-learn 1.9.1. BioNet se ejecutó durante dos épocas con Python 3.9.13, NumPy 2.0.2, scikit-learn 1.6.1 y PyTorch 2.8.0 en CPU.

Estas salidas comprueban el flujo y contienen también resultados desfavorables. Tres muestras de prueba no permiten estimar rendimiento científico. No reproducen las métricas del manuscrito ni demuestran identificabilidad, exactitud física o validación clínica. No se cargaron las bases ni checkpoints anteriores; no se publican sus métricas como resultados de esta revisión.

## Material histórico y límites

Las herramientas CLI de movilidad, espectros, convergencia y STIX solo requieren biblioteca estándar y mantienen sus ejemplos sintéticos. La demo estadística conserva su verificación histórica local descrita en el proyecto; no se reejecutó en esta incorporación.

No se ejecutaron las interfaces históricas Tkinter, Pygame u OpenGL; no se compiló Fortran ni se validó la simulación de hidrógeno. No se compilaron el manuscrito ni sus figuras. No se verificaron calibraciones, despliegues nuevos, Docker, Gunicorn en Linux, servicios externos o mejoras comerciales. Un chequeo de sintaxis no acredita que esos prototipos funcionen correctamente.

El modelo multiescala de la tesis y el generador temporal son exploraciones distintas. Las afirmaciones físicas originales y unidades siguen pendientes de revisión, aunque la separación estadística se haya mejorado.

## Demos web

Las cuatro aplicaciones web están en `demos-web/dist`. Ejecuta `node demos-web/test.mjs` para comprobar el parser CSV con comillas y saltos de línea, fechas inválidas, limpieza de espectros, deduplicación STIX y fórmulas de recargo/margen/impuesto. Se verificaron en el navegador las cuatro rutas con sus ejemplos y el recálculo de cotización al cambiar el peso. La carga de archivos utiliza las mismas funciones puras, con límites de tamaño y mensajes de error.

Los prototipos originales permanecen documentados por separado. La cotización no es una factura; el máximo espectral no es una identificación física; los patrones STIX no son un diagnóstico de seguridad.
