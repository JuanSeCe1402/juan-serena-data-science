# Resultados medidos · Online Retail II

Modelo elegido en validación: **forest**. Corte final: 2011-09-01.

Prueba: **2,772 clientes**, 908 recompraron en 30 días (32.8%).

| Método | ROC AUC | Average precision | Precisión del 20% superior | Lift del 20% superior |
|---|---:|---:|---:|---:|
| forest | 0.715 | 0.608 | 65.4% | 2.00 |
| Recencia | 0.631 | 0.428 | 47.4% | 1.45 |
| Constante de entrenamiento | 0.500 | 0.328 | 34.8% | 1.06 |

El lift es concentración retrospectiva de recompras; no mide ventas generadas por una campaña.

El desempate de scores iguales sigue el orden de ID; la precisión superior del score constante no es una selección informada.

Una sola ventana final no acredita generalización. Consultar [método y límites](README.md) y [salida completa con hash y versiones](metricas.json).
