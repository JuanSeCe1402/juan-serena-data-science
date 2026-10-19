import math
import numpy as np
from matplotlib import pylab as plt
from os import remove



foco=400
quitar_fondo=False


for i in range(0,10):
    foco=foco+100*i
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
    plt.clf()
