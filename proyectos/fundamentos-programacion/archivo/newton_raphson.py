import sympy as sp

def newton_raphson(funcion, x0, epsilon, max_iter):
    x = sp.Symbol('x')
    f = sp.sympify(funcion)
    df = sp.diff(f, x)

    xn = x0
    iteracion = 0

    while True:
        f_xn = f.subs(x, xn)
        df_xn = df.subs(x, xn)
        xn1 = xn - f_xn / df_xn
        iteracion += 1

        if abs(xn1 - xn) < epsilon or iteracion >= max_iter:
            break

        xn = xn1

    if iteracion >= max_iter:
        print("El método no converge después de", max_iter, "iteraciones.")
    else:
        print("La raíz aproximada es:", xn1)


funcion = "x**2 - x"
x0 = 2
epsilon = 0.00008
max_iter = 10000

newton_raphson(funcion, x0, epsilon, max_iter)
