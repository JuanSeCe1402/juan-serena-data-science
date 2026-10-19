import numpy as np
import matplotlib.pyplot as plt


def fermi_energy(density):
    hbar = 1.0545718e-34  # J*s
    me = 9.10938356e-31  # kg
    return (hbar ** 2 / (2 * me)) * (3 * np.pi ** 2 * density) ** (2 / 3)


def relativistic_energy(density):
    hbar = 1.0545718e-34  # J*s
    c = 3.0e8  # m/s
    return hbar * c * (3 * np.pi ** 2 * density) ** (1 / 3)


def plot_phase_diagram():
    # Crear el rango de densidades similar al de la imagen de referencia
    density = np.logspace(27, 47, 500)  # Ajustado para coincidir con la imagen

    # Calcular energías características
    EF = fermi_energy(density)
    ER = relativistic_energy(density)
    kB = 1.380649e-23  # J/K

    # Configuración inicial del plot
    plt.figure(figsize=(10, 8))

    # Frontera Gas Ideal y Gas Degenerado Clásico (kT = EF)
    plt.plot(density, EF / kB, label='Frontera Gas Ideal y Gas Degenerado Clasico', color='blue')

    # Frontera Gas Ideal y Gas Degenerado Relativista (kT = ER)
    plt.plot(density, ER / kB, label='Frontera Gas Ideal y Gas Degenerado Relativista', color='red')

    # Frontera Gas Degenerado Clásico y Gas Degenerado Relativista (EF = ER)
    # Encontrar punto de intersección
    intersection_idx = np.argmin(np.abs(EF - ER))
    intersection_density = density[intersection_idx]

    # Crear la línea verde completa
    # Solo mostramos la línea a partir del punto de intersección y hacia la derecha
    mask = density >= intersection_density
    plt.plot(density[mask], ER[mask] / kB, color='green',
             label='Frontera Gas Degenerado Clasico y Gas Degenerado Relativista')

    # Frontera Gas Ideal Clásico y Gas Ideal Relativista (línea horizontal a T=10^10 K)
    plt.axhline(y=1e10, color='gold', linestyle='-',
                label='Frontera Gas Ideal Clasico y Gas Ideal Relativista')

    # Añadir etiquetas para las cuatro regiones
    # Gas Ideal Clásico (arriba izquierda)
    plt.text(1e29, 5e11, 'Gas Ideal Clásico', fontsize=12)

    # Gas Ideal Relativista (arriba derecha)
    plt.text(1e42, 5e11, 'Gas Ideal Relativista', fontsize=12)

    # Gas Degenerado Clásico (abajo izquierda)
    plt.text(1e29, 1e5, 'Gas Degenerado Clásico', fontsize=12)

    # Gas Degenerado Relativista (abajo derecha)
    plt.text(1e42, 1e5, 'Gas Degenerado Relativista', fontsize=12)

    # Configuración del plot
    plt.xscale('log')
    plt.yscale('log')
    plt.xlim(1e27, 1e47)  # Ajuste de límites del eje x
    plt.ylim(1e2, 1e13)  # Ajuste de límites del eje y
    plt.xlabel('n m$^{-3}$')
    plt.ylabel('log T/K')
    plt.title('Diagrama de Fases para Gas de Electrones')
    plt.legend(loc='lower right')
    plt.grid(True, which='both', linestyle='-', linewidth=0.5)

    # Guardar la figura
    plt.savefig('diagrama_fases_gas_electrones.png', dpi=300, bbox_inches='tight')
    # También mostrar si el entorno lo permite
    plt.show()


if __name__ == '__main__':
    plot_phase_diagram()
