import pygame
import sys
from matplotlib import pylab as plt


#DATOS
foco=400
foco_hiperbola=200
a=100

pygame.init()

#Detalles ventana
width, height=1000,800
screen= pygame.display.set_mode((width, height))
pygame.display.set_caption("Cassegrain")
screen.fill((0,0,0))

yellow=(255, 255, 0)


#Creamos la parabola,hiperbola y la importamos
import figuras

show=False

figuras.parabola_hiperbola(foco,foco_hiperbola,a,show)
parabola_hiperbola=pygame.image.load('parabola_hiperbola.png')
parabola=pygame.transform.rotate(parabola_hiperbola,180)
pos_parabola_hiperbola=(width-800, (height-480)/2)#163
screen.blit(parabola,pos_parabola_hiperbola )

#Detectamos la posicion de la parabola
pxarray = pygame.PixelArray(screen)

detect=[]
for y in range(height):
    find=False
    for x in range(width):
        if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
            detect=(x,y)
            find=True
            break
    if find:
        break

detect1=[]
for y in range(height):
    for x in range(width):
        if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
            detect1=(x,y)
            break

cont=0
detect2=[]
for y in range(height):
    for x in range(width):
        if pxarray[x, y] == screen.map_rgb((255, 0, 0)):
            if detect2==[]:
                detect2.append((x,y-1))
            else:
                for t in detect2:
                    if abs( (x)-t[0] ) > 1:
                        cont+=1
                        if cont==len(detect2):
                            detect2.append((x,y-1))

altura_parabola=detect1[1]-detect[1]

detect3=[]
for x in range(width):
    if pxarray[x, detect[1]+altura_parabola//2] == screen.map_rgb((122, 241, 255)):
        detect3=(x,detect[1]+altura_parabola//2)
        break
dist=detect3[0]-detect2[0][0]


num_rayos=4
div_parabola=altura_parabola//(num_rayos+1)

antes=[]

for x in range(width):
    for y in range(height):
        antes.append((pygame.Surface.get_at(screen,(x,y)) , (x,y)))


#Dibujamos los rayos
col_parabola=[]
for i in range(1,num_rayos+1):
    y=detect[1] + i*div_parabola
    if i==1 or i==num_rayos:
        for x in range(width):
            if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
                pygame.draw.line(screen,yellow, (0, y), (x-1, y), 1)
                pygame.draw.line(screen,yellow, detect2[0], (x-1, y), 1)
                col_parabola.append( (x, y) )



col_hiperbola=[]

despues=[]
for x in range(width):
    for y in range(height):
        despues.append((pygame.Surface.get_at(screen,(x,y)) , (x,y)))

for i in range(len(antes)):
    if antes[i][0]==(122, 241, 255, 255):
        if antes[i][0] !=despues[i][0]:
            col_hiperbola.append(antes[i][1])


for i in col_hiperbola:
    pygame.draw.line(screen,yellow,i,detect2[1])
    pygame.draw.line(screen,(240,240,240),detect2[0],i)


pxarray.close()


clock=pygame.time.Clock()

#ciclo principal
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
