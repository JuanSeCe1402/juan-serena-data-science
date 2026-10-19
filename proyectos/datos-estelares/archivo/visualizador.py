import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
from ttkthemes import ThemedStyle

# Función para obtener la lista de tablas en la base de datos
def obtener_tablas(conexion):
    cursor = conexion.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    return [tabla[0] for tabla in tablas]

# Función para obtener las columnas de una tabla
def obtener_columnas(conexion, tabla):
    cursor = conexion.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = cursor.fetchall()
    return [columna[1] for columna in columnas]

# Función para cargar datos desde la base de datos
def cargar_datos(conexion, tabla, columnas):
    query = f"SELECT {', '.join(columnas)} FROM {tabla}"
    df = pd.read_sql_query(query, conexion)
    return df

# Función para graficar los datos
def graficar_datos(conexion, tablas, columnas, tipo_grafico):
    sns.set(style="darkgrid", palette="dark:#5A5A5A", font_scale=1.2, rc={"axes.labelcolor": "white"})
    fig, ax = plt.subplots(figsize=(10, 6))

    for tabla in tablas:
        df = cargar_datos(conexion, tabla, columnas)
        for columna in columnas:
            if tipo_grafico == 'linea':
                sns.lineplot(x=df.index, y=df[columna], label=f'{tabla} - {columna}')
            elif tipo_grafico == 'punto':
                sns.scatterplot(x=df.index, y=df[columna], label=f'{tabla} - {columna}')
            # Puedes agregar más tipos de gráficos según tus necesidades

    plt.title('Comparación de Datos', fontsize=16, color="white")
    plt.xlabel('Índice', fontsize=14, color="white")
    plt.ylabel('Valor', fontsize=14, color="white")
    plt.legend()
    plt.tight_layout()
    plt.show()

# Función para manejar la selección de tablas y columnas
def actualizar_columnas(*args):
    if conexion:
        tablas_seleccionadas = tablas_combobox.get().split(", ")
        if len(tablas_seleccionadas) == 1:
            tabla_seleccionada = tablas_seleccionadas[0]
            columnas_disponibles = obtener_columnas(conexion, tabla_seleccionada)
            columnas_listbox.delete(0, tk.END)
            for columna in columnas_disponibles:
                columnas_listbox.insert(tk.END, columna)
        else:
            columnas_listbox.delete(0, tk.END)

def generar_grafica():
    if not conexion:
        messagebox.showerror("Error", "Selecciona una base de datos primero.")
        return

    tablas_seleccionadas = tablas_combobox.get().split(", ")
    columnas_seleccionadas = columnas_listbox.curselection()

    if not tablas_seleccionadas or (len(tablas_seleccionadas) == 1 and not columnas_seleccionadas):
        messagebox.showerror("Error", "Selecciona al menos una tabla o una columna.")
        return

    tablas_seleccionadas = [tabla.strip() for tabla in tablas_seleccionadas]

    if len(tablas_seleccionadas) == 1:
        columnas_seleccionadas = [columnas_listbox.get(index) for index in columnas_seleccionadas]

    tipo_grafico_seleccionado = tipo_grafico_combobox.get()

    graficar_datos(conexion, tablas_seleccionadas, columnas_seleccionadas, tipo_grafico_seleccionado)

# Función para seleccionar la base de datos
def seleccionar_base_datos():
    global conexion
    archivo_db = filedialog.askopenfilename(filetypes=[("Base de datos SQLite", "*.db")])

    if not archivo_db:
        return

    if conexion:
        conexion.close()

    conexion = sqlite3.connect(archivo_db)
    tablas_disponibles = obtener_tablas(conexion)

    tablas_combobox['values'] = tablas_disponibles
    tablas_combobox.set(", ".join(tablas_disponibles))  # Establecer el valor predeterminado

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Visualizador de Datos")
style = ThemedStyle(root)
style.set_theme("black")  # Puedes cambiar el tema según tus preferencias

conexion = None  # Variable global para la conexión a la base de datos

# Widgets
seleccionar_db_button = ttk.Button(root, text="Seleccionar Base de Datos", command=seleccionar_base_datos)
seleccionar_db_button.pack(pady=10)

tablas_label = ttk.Label(root, text="Seleccionar Tablas:")
tablas_combobox = ttk.Combobox(root, state="readonly", postcommand=actualizar_columnas)
tablas_combobox.pack()

columnas_label = ttk.Label(root, text="Seleccionar Columnas:")
columnas_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, exportselection=0)
columnas_listbox.pack()

tipo_grafico_label = ttk.Label(root, text="Seleccionar Tipo de Gráfico:")
tipo_grafico_combobox = ttk.Combobox(root, values=['linea', 'punto'], state="readonly")
tipo_grafico_combobox.set('linea')  # Establecer el valor predeterminado
tipo_grafico_combobox.pack()

graficar_button = ttk.Button(root, text="Generar Gráfica", command=generar_grafica)
graficar_button.pack()

# Iniciar la interfaz
root.mainloop()
