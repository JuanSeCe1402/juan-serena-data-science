"""Ejemplo SINTÉTICO para dos grupos independientes; no es un estudio clínico."""
from pathlib import Path
import json
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    rng = np.random.default_rng(1402)
    a, b = rng.normal(35, 7, 40), rng.normal(40, 9, 40)
    result = stats.ttest_ind(a, b, equal_var=False)
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    df = (a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) ** 2 / (
        (a.var(ddof=1) / len(a)) ** 2 / (len(a) - 1) + (b.var(ddof=1) / len(b)) ** 2 / (len(b) - 1))
    delta = float(a.mean() - b.mean())
    margen = float(stats.t.ppf(.975, df) * se)
    report = {'origen': 'DATOS SINTÉTICOS', 'n_por_grupo': 40,
              'media_a': float(a.mean()), 'media_b': float(b.mean()),
              'diferencia_medias_a_menos_b': delta, 'ic95_diferencia': [delta - margen, delta + margen],
              'prueba': 'Welch para grupos independientes de una simulación normal',
              'p_value': float(result.pvalue), 'nota': 'No extrapolar a personas o procedimientos reales.'}
    out = Path(__file__).parent / 'resultados'
    out.mkdir(exist_ok=True)
    (out / 'resumen.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    fig, ax = plt.subplots()
    ax.boxplot([a, b])
    ax.set_xticks([1, 2], ['Grupo A', 'Grupo B'])
    ax.set_ylabel('Valor simulado (unidades arbitrarias)')
    ax.set_title('Comparación de grupos · Datos sintéticos')
    fig.tight_layout()
    fig.savefig(out / 'comparacion.png', dpi=150)
    plt.close(fig)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
