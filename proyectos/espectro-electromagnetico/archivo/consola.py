# Definición de las bandas y sus límites
bands = [
    ("Rayos gamma", (0.001, 0.01), "nm"),
    ("Rayos X", (0.01, 1), "nm"),
    ("Rayos UV", (1, 0.39), "um"),
    ("Óptico", (0.39, 0.7), "um"),
    ("Infrarrojo", (0.7, 1e3), "um"),
    ("Microondas", (1e-3, 0.1), "m"),
    ("Radio", (0.1, 1), "m")
]

# Conversión de unidades
def convert_to_meters(value, unit):
    if unit == "nm":
        return value * 1e-9
    elif unit == "um":
        return value * 1e-6
    elif unit == "mm":
        return value * 1e-3
    else:
        return value

# Cálculo de frecuencia y energía
def calculate_frequency(wavelength_m):
    c = 3e8  # Velocidad de la luz en m/s
    return c / wavelength_m

def calculate_energy(frequency_hz):
    h = 6.626e-34  # Constante de Planck en J*s
    return h * frequency_hz

# Creación de la tabla
print("----------------------------------------------------------------------------------------------------------------")
print("|     Banda     |   Longitud de Onda   |   Longitud de Onda (m)   |     Frecuencia (Hz)     |   Energía (J)   | Energía (eV) |")
print("----------------------------------------------------------------------------------------------------------------")
for band, (min_wavelength, max_wavelength), unit in bands:
    mid_wavelength = (min_wavelength + max_wavelength) / 2
    wavelength_m = convert_to_meters(mid_wavelength, unit)
    frequency_hz = calculate_frequency(wavelength_m)
    energy_joules = calculate_energy(frequency_hz)
    energy_ev = energy_joules / 1.60218e-19  # Conversión de J a eV
    print(f"| {band:<12} | {mid_wavelength:.3e} {unit} | {wavelength_m:.3e} m | {frequency_hz:.3e} Hz | {energy_joules:.3e} J | {energy_ev:.3e} eV |")
print("----------------------------------------------------------------------------------------------------------------")

# Interfaz para ingresar longitud de onda y obtener información
while True:
    try:
        input_wavelength = float(input("\nIngresa una longitud de onda en nm para obtener información (0 para salir): "))
        if input_wavelength == 0:
            break
        for band, (min_wavelength, max_wavelength), unit in bands:
            if min_wavelength <= input_wavelength <= max_wavelength:
                print(f"\nLa longitud de onda {input_wavelength:.3e} nm pertenece a la banda {band}.")
                break
        else:
            print("\nLa longitud de onda no está dentro de ninguna banda conocida.")
    except ValueError:
        print("\nIngresa un valor numérico válido.")
