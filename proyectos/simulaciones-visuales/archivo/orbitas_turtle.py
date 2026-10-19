import turtle
import random
import math

# Configuración de la pantalla
screen = turtle.Screen()
screen.setup(width=800, height=600)
screen.bgcolor("black")
screen.bgpic("stars.gif")  # Fondo de estrellas

# Cargar imágenes para los planetas
screen.register_shape("planet1.gif")
screen.register_shape("planet2.gif")
screen.register_shape("planet3.gif")
screen.register_shape("planet4.gif")

# Crear la tortuga para el sol
sun = turtle.Turtle()
sun.shape("circle")
sun.color("yellow")
sun.shapesize(5)

# Función para crear planetas
def create_planet(shape, color, distance, speed):
    planet = turtle.Turtle()
    planet.shape(shape)
    planet.color(color)
    planet.penup()
    planet.distance = distance
    planet.speed = speed
    planet.angle = random.uniform(0, 360)
    planet.orbit_angle = random.uniform(0.1, 0.5)
    return planet

# Crear planetas
planets = [
    create_planet("planet1.gif", "red", 100, 0.3),
    create_planet("planet2.gif", "blue", 180, 0.2),
    create_planet("planet3.gif", "green", 260, 0.15),
    create_planet("planet4.gif", "orange", 340, 0.1)
]

# Función para mover los planetas
def move_planets():
    for planet in planets:
        x = planet.distance * math.cos(math.radians(planet.angle))
        y = planet.distance * math.sin(math.radians(planet.angle))
        planet.goto(x, y)
        planet.angle += planet.orbit_angle
        if planet.angle > 360:
            planet.angle -= 360

# Animación principal
while True:
    move_planets()

# Mantener la ventana abierta
turtle.mainloop()
