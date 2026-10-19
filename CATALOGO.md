# Catálogo de proyectos

El portafolio reúne 31 líneas de trabajo: aplicaciones, investigación, herramientas y archivo académico. Para una primera visita, empezar por la [selección principal](README.md).

## Explorar por disciplina

| Área | Proyecto | Estado |
|---|---|---|
| Analítica de datos | [Estadística aplicada: comparación de dos grupos](proyectos/estadistica-aplicada/README.md) | Demo con datos sintéticos |
| Analítica de datos | [Movilidad urbana y bicicletas compartidas](proyectos/movilidad-urbana/README.md) | Herramienta CLI con demo sintética |
| Señales y datos científicos | [Procesamiento de espectros ópticos](proyectos/espectros-opticos/README.md) | Herramienta CLI con demo sintética |
| Física computacional | [Convergencia de cálculos de manganeso](proyectos/convergencia-manganeso/README.md) | Herramienta CLI con prueba sintética |
| Biofísica y aprendizaje automático | [Bioimpedancia multiescala e inferencia de parámetros](proyectos/bioimpedancia/README.md) | Investigación exploratoria con ejecución pequeña |
| Aplicaciones y análisis de costos | [Cortex Studio 3D: costos y cotizaciones](proyectos/cortex-impresion-3d/README.md) | Prototipo recuperado |
| Astrofísica y bases de datos | [Modelos estelares y visualización con SQLite](proyectos/datos-estelares/README.md) | Archivo académico en revisión |
| Procesamiento de señales | [Análisis de audio](proyectos/audio/README.md) | Prototipo incompleto |
| Aprendizaje automático | [Clasificación supervisada: Titanic](proyectos/titanic/README.md) | Prototipo histórico con pendientes |
| Óptica y simulación | [Simuladores de telescopios](proyectos/telescopios/README.md) | Prototipos con entradas pendientes |
| Algoritmos y gráficos 3D | [Cubo de Rubik: algoritmos e interfaz](proyectos/rubik/README.md) | Prototipos en revisión |
| Física estadística | [Regímenes de gases y energía de Fermi](proyectos/gases/README.md) | Exploración científica |
| Simulación educativa | [Movimiento de proyectiles](proyectos/proyectiles/README.md) | Prototipo educativo |
| Programación creativa | [Arte generativo con mandalas](proyectos/arte-generativo/README.md) | Prototipo visual |
| Física y aplicaciones educativas | [Calculadora del espectro electromagnético](proyectos/espectro-electromagnetico/README.md) | Prototipos educativos |
| Ciberseguridad y análisis de datos | [Análisis de indicadores STIX](proyectos/indicadores-stix/README.md) | Herramienta CLI con demo sintética |
| Desarrollo web | [Barras de envío gratuito para comercio electrónico](proyectos/ecommerce/README.md) | Fragmentos de integración |
| Datos, astronomía y divulgación | [Starlight: propuesta de observación y datos meteorológicos](proyectos/starlight/README.md) | Propuesta conceptual |
| Ingeniería de datos y biofísica | [Serena: arquitectura de datos biomédicos](proyectos/serena/README.md) | Propuesta conceptual |
| Divulgación, investigación y planificación | [Comunicación científica y gestión de proyectos](proyectos/comunicacion-cientifica/README.md) | Documentación de experiencias |
| Aprendizaje automático aplicado | [DARWIN](proyectos/darwin/README.md) | Demo sintética con evaluación reservada |
| Ingeniería de datos | [NANA](proyectos/nana/README.md) | Transformación y perfilado |
| Análisis de costos | [FREY](proyectos/frey/README.md) | Escenarios y PDF |
| Datos transaccionales | [TIKAL](proyectos/tikal/README.md) | Demo operativa |
| Desarrollo backend | [ESCULAPIO](proyectos/esculapio/README.md) | Demo administrativa |
| Desarrollo web | [Portal WUNSCE](proyectos/wunsce-web/README.md) | Sitio Flask y despliegue documentado |
| Métodos numéricos | [Interpolación y Runge–Kutta](proyectos/metodos-numericos/README.md) | API Python comprobada y fuentes Fortran |
| Energía y simulación | [Almacenamiento de hidrógeno](proyectos/almacenamiento-hidrogeno/README.md) | Archivo exploratorio en revisión |
| Algoritmos | [Fundamentos de programación](proyectos/fundamentos-programacion/README.md) | Colección académica |
| Programación creativa | [Simulaciones visuales](proyectos/simulaciones-visuales/README.md) | Prototipos de interfaz |
| Estimación y modelado | [Orden de magnitud](proyectos/orden-magnitud/README.md) | Ejercicio académico |


## Demos en línea

**[Abrir Applied Data Lab](https://juan-serena-data-lab.blithe-tang-9862.chatgpt.site)** · Acceso público, sin cuenta ni claves API.

| Aplicación | Qué puedes hacer |
|---|---|
| [Cortex 3D](https://juan-serena-data-lab.blithe-tang-9862.chatgpt.site/#cortex) | Calcular material, electricidad, operación, recargo o margen e impuesto; exportar JSON e imprimir la estimación. |
| [Movilidad urbana](https://juan-serena-data-lab.blithe-tang-9862.chatgpt.site/#movilidad) | Cargar CSV, validar viajes, explorar horarios y estaciones, descargar un reporte. |
| [Espectros ópticos](https://juan-serena-data-lab.blithe-tang-9862.chatgpt.site/#espectros) | Cargar CSV instrumentales, visualizar la señal, localizar el máximo global y exportar métricas. |
| [Indicadores STIX](https://juan-serena-data-lab.blithe-tang-9862.chatgpt.site/#stix) | Cargar uno o varios bundles, contar objetos y deduplicar patrones entre colecciones. |

Los ejemplos de análisis son **sintéticos** y están identificados. Los archivos propios se procesan dentro del navegador. Estas aplicaciones tienen un alcance funcional delimitado; no convierten los prototipos de investigación en modelos científicamente validados.

[Código de las demos web](demos-web/README.md) · [Pruebas de la lógica web](demos-web/test.mjs)


## Cómo interpretar los estados

- **Demo con pruebas:** incluye un flujo demostrable y comprobaciones automatizadas. No acredita resultados comerciales.
- **Investigación exploratoria:** modelos y experimentos con supuestos y limitaciones documentados.
- **Archivo o prototipo:** conserva trabajo académico o experimental; revisar los pendientes de su ficha antes de ejecutarlo.
- **Propuesta:** define una idea y sus siguientes pasos, sin equivaler a una implementación.

## Herramientas que puedes probar desde consola

Estos cinco ejemplos usan exclusivamente la biblioteca estándar de Python:

```bash
python proyectos/movilidad-urbana/analizar.py
python proyectos/espectros-opticos/analizar.py
python proyectos/convergencia-manganeso/extraer.py
python proyectos/indicadores-stix/analizar.py
python proyectos/metodos-numericos/metodos.py
```

Cada aplicación web tiene sus propias dependencias e instrucciones. Los prototipos históricos de interfaz y ML tienen comprobaciones distintas; consultar [VALIDACION](VALIDACION.md).

[Procedencia y atribuciones](PROCEDENCIA.md) · [Próximos pasos](ROADMAP.md) · [Volver a la portada](README.md)
