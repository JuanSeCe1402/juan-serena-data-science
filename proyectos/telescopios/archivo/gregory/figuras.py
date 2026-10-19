
import math
import numpy as np
from matplotlib import pylab as plt


def parabola(foco,quitar_fondo):
    a=[]
    b=[]
    c=[]

    for i in range(0,1000):
        x=i/25
        y=-2*math.sqrt(foco*(x))
        a.append(x)
        b.append(y)
        y=+2*math.sqrt(foco*(x))
        c.append(y)



    ax = plt.axes()
    ax.set_xticks(np.arange(0,foco,50))
    ax.set_yticks(np.arange(0,foco,50))


    plt.plot(a,b, '#7af1ff')
    plt.plot(a,c, '#7af1ff')

    plt.xlim(-5-foco//50, foco+5+foco//50)
    plt.ylim(-200,200)

    plt.gca().set_aspect('equal', adjustable='box')


    plt.scatter(foco,0,c="#ff0000",s=6)
    if quitar_fondo==True:
        plt.tick_params(axis='x', which='both', bottom=False,
                    top=False, labelbottom=False)

        plt.tick_params(axis='y', which='both', right=False,
                    left=False, labelleft=False)
        for pos in ['right', 'top', 'bottom', 'left']:
            plt.gca().spines[pos].set_visible(False)
    plt.savefig('parabola',transparent=True)

    return()

def parabola_elipse(foco,foco_elipse,a1,quitar_fondo):
    a=[]
    b=[]
    c=[]

    for i in range(0,1000):
        x=i/25
        y=-2*math.sqrt(foco*(x))
        a.append(x)
        b.append(y)
        y=+2*math.sqrt(foco*(x))
        c.append(y)

    d=[]
    e=[]
    f=[]
    g=[]

    for i in range(0,100):
        y=i
        x=a1*math.sqrt(1 - y**2/(a1**2-foco_elipse**2))+foco-foco_elipse
        d.append(x)
        e.append(y)

    for i in range(0,100):
        y=-i
        x=a1*math.sqrt(1 - y**2/(a1**2-foco_elipse**2))+foco-foco_elipse
        f.append(x)
        g.append(y)

    plt.plot(a,b, '#7af1ff')
    plt.plot(a,c, '#7af1ff')
    plt.plot(d,e, '#7af0ff')
    plt.plot(f,g, '#7af0ff')
    plt.scatter(foco,0,c="#ff0000",s=5)
    plt.scatter(foco-2*foco_elipse,0,c="#ff0000",s=5)
    plt.scatter(foco-foco_elipse,0,c="blue",s=2)

    if quitar_fondo==True:
        plt.tick_params(axis='x', which='both', bottom=False,
                    top=False, labelbottom=False)

        plt.tick_params(axis='y', which='both', right=False,
                    left=False, labelleft=False)
        for pos in ['right', 'top', 'bottom', 'left']:
            plt.gca().spines[pos].set_visible(False)
    plt.savefig('parabola_elipse',transparent=True)



def parabola_hiperbola(foco,foco_hiperbola,a1,quitar_fondo):
    a=[]
    b=[]
    c=[]

    for i in range(0,1000):
        x=i/25
        y=-2*math.sqrt(foco*(x))
        a.append(x)
        b.append(y)
        y=+2*math.sqrt(foco*(x))
        c.append(y)

    d=[]
    e=[]
    f=[]
    g=[]
    a1=100
    foco_hiperbola=200
    for i in range(0,100):
        y=i
        x=a1*math.sqrt(1 + y**2/(foco_hiperbola**2-a1**2))+foco-200
        d.append(x)
        e.append(y)

    for i in range(0,100):
        y=-i
        x=a1*math.sqrt(1 + y**2/(foco_hiperbola**2-a1**2))+foco-200
        f.append(x)
        g.append(y)

    plt.plot(a,b, '#7af1ff')
    plt.plot(a,c, '#7af1ff')
    plt.plot(d,e, '#7af1ff')
    plt.plot(f,g, '#7af1ff')
    plt.scatter(foco,0,c="#ff0000",s=6)
    plt.scatter(foco-2*foco_hiperbola,0,c="#ff0000",s=6)
    plt.scatter(foco-200,0,c="blue",s=2)

    if quitar_fondo==True:
        plt.tick_params(axis='x', which='both', bottom=False,
                    top=False, labelbottom=False)

        plt.tick_params(axis='y', which='both', right=False,
                    left=False, labelleft=False)
        for pos in ['right', 'top', 'bottom', 'left']:
            plt.gca().spines[pos].set_visible(False)
    plt.savefig('parabola_hiperbola',transparent=True)

    return
