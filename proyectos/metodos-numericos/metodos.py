"""Adaptaciones nuevas para portafolio: Lagrange, ajuste exponencial y RK4.

Motivadas por ejercicios académicos recuperados; ver README y atribuciones.
"""
import json
import math


def puntos_validos(x, y):
    x, y = list(map(float, x)), list(map(float, y))
    if not x or len(x) != len(y) or not all(math.isfinite(v) for v in x + y):
        raise ValueError('Se necesitan pares finitos y del mismo tamaño.')
    if len(set(x)) != len(x):
        raise ValueError('Las abscisas deben ser distintas.')
    return x, y


def lagrange(x, y, punto):
    x, y = puntos_validos(x, y)
    punto = float(punto)
    if not math.isfinite(punto):
        raise ValueError('El punto debe ser finito.')
    if punto in x:
        return y[x.index(punto)]
    # Forma baricéntrica, sin construir explícitamente el polinomio.
    weights = [1 / math.prod(xi - xj for j, xj in enumerate(x) if i != j)
               for i, xi in enumerate(x)]
    terms = [w / (punto - xi) for w, xi in zip(weights, x)]
    return math.fsum(t * yi for t, yi in zip(terms, y)) / math.fsum(terms)


def inversa(x, y, valor):
    x, y = puntos_validos(x, y)
    ordered = sorted(zip(x, y))
    yy = [p[1] for p in ordered]
    differences = [b - a for a, b in zip(yy, yy[1:])]
    if not differences or not (all(v > 0 for v in differences) or all(v < 0 for v in differences)):
        raise ValueError('La interpolación inversa requiere valores estrictamente monótonos.')
    if not min(yy) <= valor <= max(yy):
        raise ValueError('El valor debe estar dentro del rango observado.')
    return lagrange(y, x, valor)


def ajuste_exponencial(x, y):
    x, y = puntos_validos(x, y)
    if len(x) < 2 or any(v <= 0 for v in y):
        raise ValueError('Se necesitan dos puntos distintos y ordenadas positivas.')
    logs = [math.log(v) for v in y]
    xm, ym = math.fsum(x)/len(x), math.fsum(logs)/len(logs)
    b = math.fsum((xi-xm)*(yi-ym) for xi, yi in zip(x, logs)) / math.fsum((v-xm)**2 for v in x)
    return math.exp(ym - b*xm), b  # y = a * exp(b*x); mínimos cuadrados en log(y)


def rk4(derivada, t0, y0, fin, pasos):
    if type(pasos) is not int or pasos < 1:
        raise ValueError('pasos debe ser un entero positivo.')
    if not all(math.isfinite(v) for v in [t0, y0, fin]) or fin <= t0:
        raise ValueError('Se requiere un intervalo finito creciente.')
    h = (fin-t0)/pasos
    t, y = float(t0), float(y0)
    for i in range(pasos):
        k1 = derivada(t, y)
        k2 = derivada(t+h/2, y+h*k1/2)
        k3 = derivada(t+h/2, y+h*k2/2)
        k4 = derivada(t+h, y+h*k3)
        y += h*(k1+2*k2+2*k3+k4)/6
        t = t0+(i+1)*h
        if not math.isfinite(y):
            raise ValueError('La integración produjo un resultado no finito.')
    return y


def demo():
    a, b = ajuste_exponencial([0, 1, 2], [2, 2*math.exp(.3), 2*math.exp(.6)])
    numeric = rk4(lambda t, y: y, 0, 1, 1, 20)
    return {'lagrange_x2_en_1_5': lagrange([0,1,2],[0,1,4],1.5),
            'inversa_lineal': inversa([0,1,2],[1,3,5],4),
            'exponencial': {'a':a,'b':b},
            'rk4_exp_1': numeric,'error_absoluto':abs(numeric-math.e)}


if __name__ == '__main__':
    print(json.dumps(demo(), ensure_ascii=False, indent=2))
