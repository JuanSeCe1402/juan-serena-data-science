import matplotlib.pyplot as plt

# Definir los procesos del ciclo del hidrógeno
procesos = ['Fijación del hidrógeno', 'Intercambio atmosférico',
            'Fijación biológica y asimilación', 'Ciclo del agua',
            'Descomposición de la materia orgánica', 'Respiración y fermentación']

# Definir las etapas del ciclo del hidrógeno
etapas = ['Atmósfera', 'Superficie terrestre', 'Biosfera']

# Crear un gráfico de barras para representar los procesos
plt.figure(figsize=(10, 6))
plt.barh(procesos, [1]*len(procesos), color='skyblue')

# Añadir etiquetas y título al gráfico
plt.xlabel('Etapas del ciclo del hidrógeno')
plt.ylabel('Procesos')
plt.title('Diagrama de flujo del ciclo del hidrógeno')

# Añadir etiquetas a las etapas
for i, etapa in enumerate(etapas):
    plt.text(0.5, i, etapa, ha='center', va='center')

# Mostrar el gráfico
plt.grid(False)
plt.show()
