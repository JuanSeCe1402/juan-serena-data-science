# DARWIN con transacciones reales · Online Retail II

## Pregunta y utilidad

¿Qué clientes con al menos una compra en los últimos 180 días volverán a comprar durante los próximos 30 días? El experimento ordena clientes conocidos para revisar prioridades de seguimiento. No estima el efecto de enviar una campaña ni acredita ingresos adicionales.

**[Resultados medidos y comparación](RESULTADOS.md) · [Métricas completas](metricas.json) · [Código reproducible](../retail_publico.py) · [Pruebas de ventanas y limpieza](../tests/test_retail_publico.py)**

En el corte final de **2,772 clientes**, el Random Forest elegido en validación obtuvo **average precision 0.608**, frente a **0.428** del ranking por recencia. En el 20% superior, la recompra observada fue **65.4%** frente a **47.4%** por recencia; la tasa general fue 32.8%. Son resultados retrospectivos de una sola ventana, sin medir el efecto de contactar clientes.

## Fuente y licencia

Chen, D. (2012). **Online Retail II** [Dataset]. UCI Machine Learning Repository. DOI: [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D). [Ficha original y licencia CC BY 4.0](https://archive.ics.uci.edu/dataset/502/online+retail+ii). Consulta y descarga: 19 de octubre de 2026.

Son transacciones de un comercio británico entre diciembre de 2009 y diciembre de 2011. Es una sola empresa histórica, con numerosos clientes mayoristas: no representa al comercio actual de México ni a todos los consumidores. Los precios están en GBP.

Se leen ambas hojas del XLSX original. Se publican código y resultados agregados; el ZIP, las transacciones, los identificadores y modelos serializados permanecen fuera del repositorio. El SHA-256 del ZIP y las versiones efectivas de Python y bibliotecas quedan en `metricas.json`.

## Diseño antes de evaluar

| Partición | Fecha de corte | Historial | Etiqueta |
|---|---|---|---|
| Entrenamiento | 2010-09-01 | 180 días anteriores al corte | Compra en los siguientes 30 días |
| Validación | 2011-03-01 | 180 días anteriores al corte | Compra en los siguientes 30 días |
| Prueba final | 2011-09-01 | 180 días anteriores al corte | Compra en los siguientes 30 días |

Los intervalos son cerrados al inicio y abiertos al final. Se descarta el último día incompleto del archivo (2011-12-09). Cada ventana debe estar completamente observada. Las etiquetas de entrenamiento ya se conocen antes de validación, y las de validación antes de prueba. Algunos clientes aparecen en varias fechas: es deliberado para predecir la recompra de clientes conocidos; no es una evaluación sobre personas completamente nuevas.

Las variables son pedidos distintos, gasto bruto GBP, unidades, productos distintos, días activos, días desde la última compra y ticket medio. Solo usan operaciones anteriores al corte; no incluyen el ID, país, descripción ni ninguna compra futura. La limpieza quita filas incompletas o no finitas, cancelaciones, cantidades/precios no positivos, duplicados exactos en los seis campos utilizados y fechas fuera del periodo completo. Los conteos secuenciales constan en el JSON. Esta definición mide compras positivas, sin descontar devoluciones posteriores; un duplicado podría ser una línea legítima repetida y esta decisión puede subestimar cantidades.

Se comparan dos candidatos fijados en código: regresión logística con escalado ajustado solo con entrenamiento y Random Forest (300 árboles, profundidad 6, hoja mínima 20). Se selecciona por **average precision en validación**. No se vuelve a ajustar con validación ni se optimizan umbrales en prueba. Semilla 42, un hilo. La versión sintética de la aplicación conserva su propio flujo y dependencias.

## Interpretación

`average_precision` resume el ranking de positivos; ROC AUC evalúa discriminación y Brier evalúa error de probabilidades. Las referencias son un score constante igual a la prevalencia de entrenamiento y un ranking por compra más reciente. La transformación exponencial de recencia solo permite calcular métricas de ranking; no se presenta como probabilidad calibrada.

La precisión del 20% superior usa `ceil(0.20 * n)` clientes y desempate determinista por orden de ID. Su lift divide esa precisión por la proporción real de recompra del conjunto. Es una medida retrospectiva de concentración, **no un aumento de ventas ni un efecto causal**. Las probabilidades del modelo tampoco se acreditan como calibradas.

Es una primera evaluación con un único corte final y sin intervalos de confianza. Antes de uso comercial hacen falta varias ventanas, incertidumbre, revisión de deriva, validación sobre el negocio destinatario y un experimento controlado para medir el efecto de una intervención.

## Reproducir

Desde la raíz del repositorio, descargar el ZIP original sin desactivar la verificación TLS:

```powershell
New-Item -ItemType Directory -Force ../darwin-datos-locales
curl.exe -L --fail --retry 3 -o ../darwin-datos-locales/online_retail_ii.zip "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
cd proyectos/darwin
python -m pip install -r requirements-public-data.txt -r requirements-dev.txt
python retail_publico.py --archive ../../../darwin-datos-locales/online_retail_ii.zip
python -m pytest -q
```

Comparar el SHA-256 antes de contrastar métricas. El ZIP debe terminar de descargarse antes de ejecutar; una descarga parcial no se acepta como dataset. La lectura de más de un millón de líneas desde Excel puede tardar varios minutos. La carpeta de datos se crea fuera del checkout. En Linux/macOS sustituir `curl.exe` por `curl` y crear la carpeta con `mkdir -p ../darwin-datos-locales`. Los requisitos de pruebas están en `requirements-dev.txt`; las pruebas usan fixtures pequeños y no descargan datos en CI.

Este experimento se preparó con asistencia de Codex. La atribución de los datos pertenece a su fuente; los resultados no se confunden con experiencia comercial o validación de la demo desplegada.
