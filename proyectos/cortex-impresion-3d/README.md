# Cortex Studio 3D: costos y cotizaciones

**[Probar la aplicación web](https://juan-serena-data-lab-production.up.railway.app/#cortex)** · [Código de la versión web](../../demos-web/README.md)

Aplicación Tkinter para costos de material y electricidad, recargo y exportación a PDF. Incluye los módulos recuperados; no contiene cotizaciones ni nombres de clientes.

**Área:** Aplicaciones y análisis de costos · **Estado:** Prototipo recuperado

## Material recuperado

- `app.py`
- `cotizacion_pdf.py`
- `nota_pdf.py`
- `graficos.py`

Los archivos de `archivo/` conservan prototipos del archivo personal. Su presencia no acredita ejecución, resultados ni autoría exclusiva. Las adaptaciones nuevas se identifican en la documentación.

## Entorno

Python 3.10 o posterior. Crea un entorno virtual e instala `requirements.txt` desde esta carpeta. Las dependencias históricas no se han fijado a versiones comprobadas. Tkinter puede requerir un paquete del sistema.

## Uso

```bash
python app.py
```

## Alcance y limitaciones

La interfaz requiere escritorio gráfico. El campo histórico «margen» aplica un recargo sobre costo, no margen sobre ventas. No se verificó el flujo completo de GUI/PDF.

## Siguiente desarrollo

Registrar pedidos anónimos, revisar costos indirectos y medir rentabilidad.

[Volver al portafolio](../../README.md)