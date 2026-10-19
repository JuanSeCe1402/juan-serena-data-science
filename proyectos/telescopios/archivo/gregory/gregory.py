import pygame
import sys

#DATOS
foco=400
foco_elipse=200
a=300


pygame.init()

#Detalles ventana
width, height=1000,800
screen= pygame.display.set_mode((width, height))
pygame.display.set_caption("Gregory")
screen.fill((0,0,0))

yellow=(255, 255, 0)

#Creamos la parabola y la importamos
import figuras

figuras.parabola_elipse(foco,foco_elipse,a,False)
parabola_elipse=pygame.image.load('parabola_elipse.png')
parabola=pygame.transform.rotate(parabola_elipse,180)
pos_parabola_elipse=(width-800, (height-480)/2)#163
screen.blit(parabola,pos_parabola_elipse )

#Detectamos la posicion de la parabola
pxarray = pygame.PixelArray(screen)
pygame.PixelArray.close
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



#Dibujamos los rayos
col_parabola=[]
for i in range(1,num_rayos+1):
    y=detect[1] + i*div_parabola
    if i==1 or i==num_rayos:
        for x in range(width):
            if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
                pygame.draw.line(screen,yellow, (0, y), (x-1, y), 1)
                pygame.draw.line(screen,yellow, detect2[0], (x-1, y), 1)
                col_parabola.append( (x-1, y) )

col_elipse=[]
for i in range(1,num_rayos+1):
    y=detect[1] + i*div_parabola
    if i!=1 or i!=num_rayos:
        for x in range(width):
            if pxarray[x, y] == screen.map_rgb((122, 240, 255)):
                if i ==2:
                    pygame.draw.line(screen,yellow, detect2[0], (x+8, y-20), 1)
                    pygame.draw.line(screen,yellow, (x+8, y-20), detect2[1], 1)
                    col_elipse.append( (x+1, y) )
                if i ==3:
                    pygame.draw.line(screen,yellow, detect2[0], (x+8, y+20), 1)
                    pygame.draw.line(screen,yellow, (x+8, y+20), detect2[1], 1)
                    col_elipse.append( (x+1, y) )



#ciclo principal
while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
