import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ======================================================
# CONFIGURACIÓN DEL SISTEMA (puedes modificar todo)
# ======================================================

HOURS = 10
DT_MIN = 1
STEPS = int(HOURS * 60 / DT_MIN)

# --- Componentes físicos ---
TANK_VOLUME_M3 = 1.0                # volumen del tanque
T_AMBIENT = 293.15                  # K temperatura ambiente
T_INITIAL = 303.15                  # temperatura inicial del tanque
HEAT_LOSS_W_PER_K = 5.0             # pérdida térmica al ambiente
GAS_CP = 14.3e3                     # J/kg-K calor específico del H2

# --- Electrolizador ---
ELECTROLYZER_POWER_KW = 25.0
ELECTROLYZER_KWH_PER_KG = 50.0
ELECTROLYZER_SCHEDULE = np.ones(STEPS)  # siempre encendido, puedes poner 0 en horas que quieras

# --- Fuel Cell ---
FUELCELL_KWH_PER_KG = 40.0

# Perfil de demanda enteramente sintético, sin observaciones reales
fuelcell_demand_kw = (
    15 + 10*np.sin(np.linspace(0, 3*np.pi, STEPS))  # forma de curva típica
)
fuelcell_demand_kw += np.random.default_rng(42).normal(0, 1, STEPS)  # ruido realista
fuelcell_demand_kw = np.clip(fuelcell_demand_kw, 5, 30)

# --- Compresor ---
COMPRESSOR_ACTIVE = True
COMPRESSOR_MIN_PRESSURE_BAR = 8
COMPRESSOR_POWER_KW = 5  # energía usada al activar
COMPRESSOR_KWH_PER_KG = 3  # energía para comprimir

# --- Fugas ---
LEAK_COEFF_KG_H_BAR = 0.01  # fuga proporcional a presión

# --- Límites de seguridad ---
MAX_PRESSURE_BAR = 20

# --- Constantes ---
R = 8.31446261815324
M_H2 = 2.016e-3
AMB_PRESSURE_PA = 101325

def pressure_from_mass_T(mass_kg, T_kelvin):
    if mass_kg <= 0:
        return AMB_PRESSURE_PA
    n = mass_kg / M_H2
    return n * R * T_kelvin / TANK_VOLUME_M3

def mass_from_pressure_T(P_pa, T_kelvin):
    if P_pa <= AMB_PRESSURE_PA:
        return 0
    n = P_pa * TANK_VOLUME_M3 / (R * T_kelvin)
    return n * M_H2

# ======================================================
# VARIABLES INICIALES
# ======================================================

mass_h2 = 1.0
T_gas = T_INITIAL

mass_series = []
pressure_series = []
temp_series = []
prod_series = []
cons_series = []
leak_series = []
compressor_energy_series = []

for t in range(STEPS):

    # =========================================
    # 1) Electrolizador — producción
    # =========================================
    power_el_kw = ELECTROLYZER_POWER_KW * ELECTROLYZER_SCHEDULE[t]
    prod_kg_min = (power_el_kw / ELECTROLYZER_KWH_PER_KG) / 60

    # =========================================
    # 2) Fuel Cell — consumo
    # =========================================
    demand_kw = fuelcell_demand_kw[t]
    cons_kg_min = (demand_kw / FUELCELL_KWH_PER_KG) / 60

    # =========================================
    # 3) Fugas dependientes de presión
    # =========================================
    P_pa = pressure_from_mass_T(mass_h2, T_gas)
    P_bar = P_pa / 1e5
    leak_kg_h = LEAK_COEFF_KG_H_BAR * max(P_bar - 1, 0)
    leak_kg_min = leak_kg_h / 60

    # =========================================
    # 4) Actualizar masa preliminar
    # =========================================
    delta_mass = prod_kg_min - cons_kg_min - leak_kg_min
    new_mass = mass_h2 + delta_mass
    new_mass = max(new_mass, 0)

    # =========================================
    # 5) Compresor — mantiene presión mínima
    # =========================================
    compressor_energy = 0
    P_new_bar = pressure_from_mass_T(new_mass, T_gas) / 1e5

    if COMPRESSOR_ACTIVE and P_new_bar < COMPRESSOR_MIN_PRESSURE_BAR:
        needed_pressure_pa = COMPRESSOR_MIN_PRESSURE_BAR * 1e5
        needed_mass = mass_from_pressure_T(needed_pressure_pa, T_gas)
        added_mass = max(0, needed_mass - new_mass)
        compressor_energy = added_mass * COMPRESSOR_KWH_PER_KG
        new_mass = needed_mass

    # =========================================
    # 6) Seguridad — venteo si excede presión
    # =========================================
    P_new_bar = pressure_from_mass_T(new_mass, T_gas) / 1e5
    if P_new_bar > MAX_PRESSURE_BAR:
        safe_mass = mass_from_pressure_T(MAX_PRESSURE_BAR * 1e5, T_gas)
        new_mass = safe_mass

    # =========================================
    # 7) Temperatura — pérdidas térmicas
    # =========================================
    # Energía térmica perdida
    dT = (HEAT_LOSS_W_PER_K * (T_AMBIENT - T_gas)) * DT_MIN*60
    dT /= (mass_h2 + 1e-6) * GAS_CP
    T_gas += dT

    # Guardar
    mass_h2 = new_mass

    mass_series.append(mass_h2)
    pressure_series.append(pressure_from_mass_T(mass_h2, T_gas)/1e5)
    temp_series.append(T_gas)
    prod_series.append(prod_kg_min)
    cons_series.append(cons_kg_min)
    leak_series.append(leak_kg_min)
    compressor_energy_series.append(compressor_energy)

# ======================================================
# SALIDAS
# ======================================================

df = pd.DataFrame({
    "time_min": np.arange(STEPS),
    "mass_kg": mass_series,
    "pressure_bar": pressure_series,
    "temperature_K": temp_series,
    "prod_kg_min": prod_series,
    "cons_kg_min": cons_series,
    "leak_kg_min": leak_series,
    "compressor_kwh": compressor_energy_series
})

print(df.head())
print("\nSimulación completada.\n")

plt.figure(figsize=(10,4))
plt.plot(df["time_min"]/60, df["mass_kg"])
plt.xlabel("Horas")
plt.ylabel("Masa H2 (kg)")
plt.title("Masa de H2 en tanque")
plt.grid()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(df["time_min"]/60, df["pressure_bar"])
plt.xlabel("Horas")
plt.ylabel("Presión (bar)")
plt.title("Presión en tanque")
plt.grid()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(df["time_min"]/60, df["temperature_K"])
plt.xlabel("Horas")
plt.ylabel("Temperatura (K)")
plt.title("Temperatura del gas")
plt.grid()
plt.show()
