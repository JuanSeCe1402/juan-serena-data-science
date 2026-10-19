import pygame
import numpy as np

# Inicialización de Pygame
pygame.init()

# Configuración de la pantalla
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Átomos")

# Definición de colores
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Clase para representar los átomos
class Atom(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = np.random.uniform(-2, 2, size=(2,))

    def update(self):
        self.rect.move_ip(self.velocity)
        if self.rect.left < 0 or self.rect.right > width:
            self.velocity[0] *= -1
        if self.rect.top < 0 or self.rect.bottom > height:
            self.velocity[1] *= -1

# Creación de átomos
all_atoms = pygame.sprite.Group()
for _ in range(10):
    pos = np.random.randint(20, width-20), np.random.randint(20, height-20)
    atom = Atom(pos)
    all_atoms.add(atom)

# Bucle principal del juego
clock = pygame.time.Clock()
running = True
while running:
    screen.fill(WHITE)

    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Actualización de la posición de los átomos
    all_atoms.update()

    # Dibujar átomos en la pantalla
    all_atoms.draw(screen)

    # Refrescar pantalla
    pygame.display.flip()

    # Control de velocidad de la animación
    clock.tick(60)

# Salida del juego
pygame.quit()
