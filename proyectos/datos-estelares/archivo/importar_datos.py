import pandas as pd
import sqlite3

archivo_dat = 'starmodl_py1402 61 Cygni.dat'
lineas_datos = []

try:
    with open(archivo_dat, 'r') as archivo:
        for linea in archivo:
            if linea.strip() and not linea.startswith((' ', 'Notes:')):
                lineas_datos.append(linea.strip())
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {archivo_dat}.")
    exit()
except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    exit()

if not lineas_datos:
    print("Error: No se encontraron líneas de datos.")
    exit()

num_columnas_max = max(len(linea.split()) for linea in lineas_datos)
datos = [linea.split() for linea in lineas_datos]

for linea in datos:
    while len(linea) < num_columnas_max:
        linea.append(None)

nombres_deseados = ['r', 'Qm', 'L_r', 'T', 'P', 'rho', 'kap', 'eps', 'C o R', 'dlPdlT']
df = pd.DataFrame(datos, columns=nombres_deseados)

columnas_numericas = ['r', 'Qm', 'L_r', 'T', 'P', 'rho', 'kap', 'eps', 'dlPdlT']
df[columnas_numericas] = df[columnas_numericas].apply(pd.to_numeric, errors='coerce')



conexion = sqlite3.connect('base_de_datos1402.db')
df.to_sql('61 Cygni', conexion, index=False, if_exists='append')
conexion.close()

print("Proceso completado con éxito. Los datos han sido almacenados en la base de datos.")
