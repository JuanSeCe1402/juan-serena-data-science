import pygame
import numpy as np

# Inicialización de Pygame
pygame.init()

# Configuración de la pantalla
width, height = 1200, 800
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Sistema Solar")

# Definición de colores
WHITE = (255, 255, 255)

# Clase para representar cuerpos celestes
class CelestialBody(pygame.sprite.Sprite):
    def __init__(self, image, pos, size, velocity=[0, 0], orbit_radius=0):
        super().__init__()
        self.image = pygame.image.load(image)
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = np.array(velocity, dtype=float)
        self.orbit_center = np.array(pos)
        self.orbit_radius = orbit_radius
        self.angle = 0

    def update(self):
        # Actualizar la posición del cuerpo celeste
        new_center = self.orbit_center + np.array([
            self.orbit_radius * np.cos(np.radians(self.angle)),
            self.orbit_radius * np.sin(np.radians(self.angle))
        ])
        self.rect.center = new_center.astype(int)  # Convertir a enteros
        self.angle += np.linalg.norm(self.velocity) / self.orbit_radius  # Velocidad angular
        self.orbit_center += self.velocity.astype(int)  # Convertir a enteros

# Creación de cuerpos celestes
all_celestial_bodies = pygame.sprite.Group()

# Sol
sun = CelestialBody("images/sun.png", (width // 2, height // 2), (100, 100))
all_celestial_bodies.add(sun)

# Planetas
planets_data = [
     {"name": "Mercurio", "image": "images/mercury.png", "radius": 50, "distance": 150, "speed": 1.6},
    {"name": "Venus", "image": "images/venus.png", "radius": 70, "distance": 220, "speed": 1.2},
    {"name": "Tierra", "image": "images/earth.png", "radius": 80, "distance": 300, "speed": 1},
    {"name": "Marte", "image": "images/mars.png", "radius": 60, "distance": 380, "speed": 0.8},
    {"name": "Júpiter", "image": "images/jupiter.png", "radius": 120, "distance": 480, "speed": 0.5},
    {"name": "Saturno", "image": "images/saturn.png", "radius": 110, "distance": 600, "speed": 0.4},
    {"name": "Urano", "image": "images/uranus.png", "radius": 90, "distance": 700, "speed": 0.3},
    {"name": "Neptuno", "image": "images/neptune.png", "radius": 100, "distance": 800, "speed": 0.2}
]


for data in planets_data:
    planet = CelestialBody(data["image"], (width // 2, height // 2), (data["radius"], data["radius"]),
                           orbit_radius=data["distance"], velocity=[0, data["speed"]])
    all_celestial_bodies.add(planet)

# Creación de estrellas de fondo
all_stars_background = pygame.sprite.Group()
for _ in range(200):
    pos = np.random.randint(0, width), np.random.randint(0, height)
    star = CelestialBody("images/star.png", pos, (3, 3))
    all_stars_background.add(star)

# Bucle principal del juego
clock = pygame.time.Clock()
running = True
while running:
    screen.fill(WHITE)

    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Agregar un nuevo cuerpo celeste al hacer clic
            pos = pygame.mouse.get_pos()
            comet = CelestialBody("images/comet.png", pos, (30, 30), velocity=[1, -1])
            all_celestial_bodies.add(comet)

    # Actualizar la posición de los cuerpos celestes
    all_celestial_bodies.update()

    # Dibujar estrellas de fondo y cuerpos celestes en la pantalla
    all_stars_background.draw(screen)
    all_celestial_bodies.draw(screen)

    # Refrescar pantalla
    pygame.display.flip()

    # Control de velocidad de la animación
    clock.tick(60)

# Salida del juego
pygame.quit()
