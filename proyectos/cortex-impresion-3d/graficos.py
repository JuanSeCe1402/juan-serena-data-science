import matplotlib.pyplot as plt

def mostrar_grafico_costos(datos):
    etiquetas = ['Material', 'Electricidad', 'Ganancia']
    valores = [datos['costo_material'], datos['costo_electricidad'], datos['ganancia']]

    plt.figure(figsize=(6,6))
    plt.title("Desglose de Costos - Cortex Studio 3D")
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.show()
