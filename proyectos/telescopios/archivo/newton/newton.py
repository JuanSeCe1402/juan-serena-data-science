import pygame
import sys
import numpy as np





#DATOS
foco=np.loadtxt('DATOS_NEWTON.txt',delimiter=",",skiprows=1,usecols=0)
espejo=np.loadtxt('DATOS_NEWTON.txt',delimiter=",",skiprows=1,usecols=1)
num_rayos=int(np.loadtxt('DATOS_NEWTON.txt',dtype=int,delimiter=",",skiprows=1,usecols=2))


pygame.init()

#Detalles ventana
width, height=1000,800
screen= pygame.display.set_mode((width, height))
pygame.display.set_caption("Newton")

def main():
    screen.fill((0,0,0))
    #Colores
    white=(255,255,255)
    yellow=	(255, 255, 0)


    #Creamos la parabola y la importamos
    import figuras

    figuras.parabola(foco,False)
    parabola=pygame.image.load('parabola.png')
    parabola=pygame.transform.rotate(parabola,180)
    pos_parabola=(width-600, (height-480)/2)#163
    screen.blit(parabola,pos_parabola )


    #Buscamos la posicion de la parabola
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

    #Buscamos el foco de la parabola
    detect2=[]
    for y in range(height):
        for x in range(width):
            if pxarray[x, y] == screen.map_rgb((255, 0, 0)):
                detect2=(x,y-1)
                break

    altura_parabola=detect1[1]-detect[1]

    #Buscamos la mitad de la parabola
    detect3=[]
    for x in range(width):
        if pxarray[x, detect[1]+altura_parabola//2] == screen.map_rgb((122, 241, 255)):
            detect3=(x,detect[1]+altura_parabola//2)
            break



    dist=detect3[0]-detect2[0]
    ratio=dist/foco
    div_parabola=altura_parabola//(num_rayos+1)


    #Dibujamos los rayos
    col_parabola=[]
    for i in range(1,num_rayos+1):
        y=detect[1] + i*div_parabola
        if num_rayos%2==0:
            for x in range(width):
                if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
                    pygame.draw.line(screen,yellow, (0, y), (x-1, y), 1)
                    pygame.draw.line(screen,yellow, detect2, (x-1, y), 1)
                    col_parabola.append( (x-1, y) )
        else:
            if i!=num_rayos//2+1:
                for x in range(width):
                    if pxarray[x, y] == screen.map_rgb((122, 241, 255)):
                        pygame.draw.line(screen,yellow, (0, y), (x-1, y), 1)
                        pygame.draw.line(screen,yellow, detect2, (x-1, y), 1)
                        col_parabola.append( (x-1, y) )


    #Detectamos colisión de los rayos con el espejo plano
    cont=0
    pxarray = pygame.PixelArray(screen)
    col_espejo=[]
    for i in range(div_parabola//2-5):
        x=detect2[0]+int(espejo*ratio)
        y=detect2[1]

        if pxarray[x-i, y-i] == screen.map_rgb(yellow):
            if col_espejo==[]:
                col_espejo.append((x-i,y-i))

            else:
                for t in col_espejo:
                    if abs( (x-i)-t[0] ) > 1:
                        cont+=1
                        if cont==len(col_espejo):
                            col_espejo.append((x-i,y-i))

        cont=0
        if pxarray[x+i, y+i] == screen.map_rgb(yellow):
            if col_espejo==[]:
                col_espejo.append((x+i,y+i))

            else:
                for t in col_espejo:
                    if abs( (x+i)-t[0] ) > 1:
                        cont+=1
                        if cont==len(col_espejo):
                            col_espejo.append((x+i,y+i))



    #dibujamos el espejo
    for i in range(div_parabola//2-5):
        x=detect2[0]+int(espejo*ratio)
        y=detect2[1]
        pygame.draw.circle(screen, (122, 241, 250), (x-i,y-i),1)
        pygame.draw.circle(screen, (122, 241, 250), (x+i,y+i),1)

    foco_reflejado=(detect2[0]+int(espejo*ratio), detect2[1]-int(espejo*ratio))
    pygame.draw.circle(screen,(255,0,0),(foco_reflejado[0]+1,foco_reflejado[1]),2)


    #dibujamos el rayos reflejado del espejo
    for rayo in col_espejo:
        pygame.draw.line(screen,yellow,rayo,foco_reflejado,1)

    for element in col_espejo:
        pygame.draw.circle(screen,(200,0,0),element,2)

    for rayo in col_espejo:
        pygame.draw.line(screen,(240,240,240),detect2,rayo,1)

    #volvemos a dibujar el espejo

    for i in range(div_parabola//2-5):
        x=detect2[0]+int(espejo*ratio)
        y=detect2[1]
        pygame.draw.circle(screen, (122, 241, 250), (x-i,y-i),1)
        pygame.draw.circle(screen, (122, 241, 250), (x+i,y+i),1)
    return()


clock=pygame.time.Clock()
#ciclo principal
while True:
    clock.tick(20)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


    foco=np.loadtxt('DATOS_NEWTON.txt',delimiter=",",skiprows=1,usecols=0)
    espejo=np.loadtxt('DATOS_NEWTON.txt',delimiter=",",skiprows=1,usecols=1)
    num_rayos=int(np.loadtxt('DATOS_NEWTON.txt',dtype=int,delimiter=",",skiprows=1,usecols=2))
    print(foco)

    main()

    pygame.display.update()
