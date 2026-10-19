import pygame
import math

# Configuración de pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Cañón")

# Colores
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Variables del cañón
angle = 45  # Ángulo de disparo en grados
velocity = 50  # Velocidad inicial del proyectil en m/s
gravity = 9.8  # Aceleración debida a la gravedad en m/s^2

# Función para calcular el alcance máximo
def calculate_range(v, a, g):
    return (v ** 2) * math.sin(2 * math.radians(a)) / g

# Inicialización de pygame
pygame.init()

# Ciclo principal del juego
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Lógica del juego
    range_max = calculate_range(velocity, angle, gravity)
    time_of_flight = (2 * velocity * math.sin(math.radians(angle))) / gravity

    # Dibujo
    screen.fill(WHITE)

    # Dibujar el suelo
    pygame.draw.rect(screen, RED, (0, HEIGHT - 10, WIDTH, 10))

    # Dibujar el cañón
    pygame.draw.rect(screen, RED, (50, HEIGHT - 50, 50, 30))
    pygame.draw.circle(screen, RED, (75, HEIGHT - 50), 25)

    # Dibujar el proyectil
    t = pygame.time.get_ticks() / 1000  # Tiempo en segundos
    x = velocity * math.cos(math.radians(angle)) * t
    y = HEIGHT - 60 - (velocity * math.sin(math.radians(angle)) * t - (0.5 * gravity * t ** 2))
    pygame.draw.circle(screen, RED, (int(x), int(y)), 10)

    # Actualizar la pantalla
    pygame.display.flip()

# Salir del juego
pygame.quit()
