"""Contrastes con soluciones analíticas y entradas degeneradas."""
import math
import unittest
from metodos import lagrange, inversa, ajuste_exponencial, rk4


class MetodosTests(unittest.TestCase):
    def test_reproduce_polynomial_and_nodes(self):
        f=lambda x: 2*x**3-3*x+7
        xs=[-2,-1,0,2]
        for x in xs+[.25,1.5]:
            self.assertAlmostEqual(lagrange(xs,list(map(f,xs)),x),f(x),places=11)

    def test_inverse_domain_and_exponential(self):
        self.assertAlmostEqual(inversa([0,1,2],[1,3,5],4),1.5)
        with self.assertRaises(ValueError):inversa([0,1,2],[0,1,0],.5)
        with self.assertRaises(ValueError):inversa([0,1],[0,1],2)
        a,b=ajuste_exponencial([0,1,2],[3,3*math.exp(-.2),3*math.exp(-.4)])
        self.assertAlmostEqual(a,3);self.assertAlmostEqual(b,-.2)
        with self.assertRaises(ValueError):ajuste_exponencial([0,1],[1,0])

    def test_degenerate_input_rejected(self):
        for x,y in [([1,1],[2,3]),([] ,[]),([0],[math.nan]),([0,1],[2])]:
            with self.assertRaises(ValueError):lagrange(x,y,0)

    def test_rk4_order_and_logistic_solution(self):
        coarse=abs(rk4(lambda t,y:y,0,1,1,10)-math.e)
        fine=abs(rk4(lambda t,y:y,0,1,1,20)-math.e)
        self.assertGreater(coarse/fine,14)
        k,m,x0=.01,100,10
        exact=m/(1+(m/x0-1)*math.exp(-k*m*2))
        self.assertAlmostEqual(rk4(lambda t,x:k*x*(m-x),0,x0,2,200),exact,places=7)


if __name__=='__main__':unittest.main()
