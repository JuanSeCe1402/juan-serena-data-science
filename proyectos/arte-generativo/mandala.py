from turtle import *
import colorsys
import time
from PIL import Image

# Configuración inicial
bgcolor("black")
speed(0)
tracer(0)
pensize(2)

# Parámetros
capas = 12              # cantidad de capas
petalos_por_capa = 20   # pétalos por capa
radio_inicial = 60
incremento_radio = 30
retardo = 0.005

def petalo(tam):
    """Dibuja un pétalo con dos arcos."""
    circle(tam, 60)
    left(120)
    circle(tam, 60)
    left(120)

# Dibujo principal
for capa in range(capas):
    radio = radio_inicial + capa * incremento_radio
    tam_petalo = 15 + capa * 2
    petalos = petalos_por_capa + capa * 2

    for i in range(petalos):
        h = (i / petalos + capa / capas) % 1
        r, g, b = colorsys.hsv_to_rgb(h, 0.8, 1)
        color_hex = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

        angle = i * (360 / petalos)

        penup()
        goto(0, 0)
        setheading(angle)
        forward(radio)
        pendown()

        setheading(angle + 60)
        color(color_hex, "#000000")
        begin_fill()
        petalo(tam_petalo)
        end_fill()

        update()
        time.sleep(retardo)

# Guardar como PNG
ts = getscreen().getcanvas()
ts.postscript(file="mandala_petalos.eps")
img = Image.open("mandala_petalos.eps")
img.save("mandala_petalos.png", "png")

print("✅ Mandala con pétalos guardado como mandala_petalos.png")

done()
