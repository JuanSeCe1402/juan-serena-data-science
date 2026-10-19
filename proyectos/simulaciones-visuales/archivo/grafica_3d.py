import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Parámetros del sistema
num_atomos = 1000  # Número de átomos
k_B = 1.38e-23  # Constante de Boltzmann
T = 300  # Temperatura en Kelvin

# Generar posiciones iniciales aleatorias
posiciones = np.random.rand(num_atomos, 3)  # x, y, z

# Distribuir velocidades de acuerdo con la distribución de Boltzmann
velocidades = np.random.normal(loc=0, scale=np.sqrt(k_B * T), size=(num_atomos, 3))

# Tiempo de simulación
num_steps = 1000
dt = 1e-15  # Intervalo de tiempo en segundos

# Simulación de movimiento
for _ in range(num_steps):
    # Actualizar posiciones
    posiciones += velocidades * dt

    # Limitar las posiciones al rango [0, 1]
    posiciones = np.clip(posiciones, 0, 1)

    # Visualizar los resultados
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(posiciones[:, 0], posiciones[:, 1], posiciones[:, 2], c='b', marker='o')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_zlim(0, 1)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.pause(0.01)
    plt.cla()

plt.show()
