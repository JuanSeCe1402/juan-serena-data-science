# Importamos la librería tkinter para la interfaz gráfica
import tkinter as tk
from tkinter import ttk

# Definimos las funciones para convertir entre longitudes de onda y frecuencias
def wavelength_to_frequency(wavelength):
    speed_of_light = 3.0e8  # m/s
    frequency = speed_of_light / wavelength
    return frequency

def energy_from_wavelength(wavelength):
    planck_constant = 6.626e-34  # J*s
    speed_of_light = 3.0e8  # m/s
    energy = planck_constant * speed_of_light / wavelength
    return energy

# Definimos los rangos y nombres de las bandas
bands = [
    ("Rayos Gamma", (0.001e-9, 0.01e-9)),
    ("Rayos X", (0.01e-9, 1e-9)),
    ("Rayos UV", (1e-9, 0.39e-6)),
    ("Óptico", (0.39e-6, 0.7e-6)),
    ("Infrarrojo", (0.7e-6, 1e-3)),
    ("Microondas", (1e-3, 100e-3)),
    ("Radio", (100e-3, 1000e-3))
]

# Función para calcular y mostrar los resultados
def calculate_results():
    input_wavelength = float(entry_wavelength.get())
    input_wavelength_meters = input_wavelength * 1e-9  # Convert to meters

    for band_name, (min_wavelength, max_wavelength) in bands:
        if min_wavelength <= input_wavelength_meters <= max_wavelength:
            frequency = wavelength_to_frequency(input_wavelength_meters)
            energy = energy_from_wavelength(input_wavelength_meters) / 1.602e-19  # Convert to eV
            label_band.config(text=band_name)
            label_wavelength_meters.config(text=f"{input_wavelength_meters:.2e} m")
            label_frequency.config(text=f"{frequency:.2e} Hz")
            label_energy.config(text=f"{energy:.2e} eV")
            break

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Espectro Electromagnético")

frame = ttk.Frame(root, padding=20)
frame.grid(column=0, row=0)

label_instructions = ttk.Label(frame, text="Ingresa la longitud de onda en nanómetros:")
label_instructions.grid(column=0, row=0, columnspan=2)

entry_wavelength = ttk.Entry(frame)
entry_wavelength.grid(column=0, row=1)

button_calculate = ttk.Button(frame, text="Calcular", command=calculate_results)
button_calculate.grid(column=1, row=1)

label_band = ttk.Label(frame, text="")
label_band.grid(column=0, row=2, columnspan=2)

label_wavelength_meters = ttk.Label(frame, text="")
label_wavelength_meters.grid(column=0, row=3, columnspan=2)

label_frequency = ttk.Label(frame, text="")
label_frequency.grid(column=0, row=4, columnspan=2)

label_energy = ttk.Label(frame, text="")
label_energy.grid(column=0, row=5, columnspan=2)

root.mainloop()
