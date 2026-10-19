def calcular_masa(talla, peso, altura_hombre, peso_hombre, altura_mujer, peso_mujer):
    cambio_area_por_kg = 0.01
    cambio_area_por_cm = 0.01

    if sexo == 'hombre':
        cambio_area = cambio_area_por_kg * abs(peso - peso_hombre) + cambio_area_por_cm * abs(talla - altura_hombre)
    elif sexo == 'mujer':
        cambio_area = cambio_area_por_kg * abs(peso - peso_mujer) + cambio_area_por_cm * abs(talla - altura_mujer)

    area_superficial_base = 2.0 if sexo == 'hombre' else 1.5
    area_superficial = area_superficial_base + area_superficial_base * cambio_area

    masa = area_superficial / 0.16
    return masa, area_superficial

def calcular_tasa_metabolica(masa, actividades):
    # Considerar el área superficial proporcionado al calcular la tasa metabólica
    tasa_metabolica = (masa / 2.0) * sum(actividades.values())  # Utilizar 2.0 m^2 como área de referencia
    return tasa_metabolica

def comparar_con_foco(tasa_metabolica):
    # Comparar la tasa metabólica con la potencia de un foco (en julios por hora)
    potencia_foco_por_hora = 100
    diferencia_por_hora = abs(tasa_metabolica - potencia_foco_por_hora)
    return diferencia_por_hora

def kcal_por_dia(tasa_metabolica):
    # Convertir la tasa metabólica de julios por hora a kcal por día
    factor_conversion = 4190
    tasa_metabolica_kcal = tasa_metabolica / factor_conversion
    return tasa_metabolica_kcal

def comparar_con_estandar(tasa_metabolica_kcal):
    # Comparar la tasa metabólica en kcal/día con los valores estándar sugeridos por dietistas
    estandar_min = 25
    estandar_max = 32
    diferencia_estandar = abs(tasa_metabolica_kcal - (estandar_min + estandar_max) / 2)
    return diferencia_estandar

def watts_por_segundo(tasa_metabolica):
    # Convertir la tasa metabólica de julios por hora a vatios por segundo
    return tasa_metabolica / 3600  # Convertir de julios por hora a vatios por segundo

# Datos estándar
altura_hombre_estandar = 1.78
peso_hombre_estandar = 80
altura_mujer_estandar = 1.62
peso_mujer_estandar = 50

# Solicitar información al usuario
print("¿Eres hombre o mujer?")
sexo = input().lower()

# Validar la entrada del usuario
while sexo not in ['hombre', 'mujer']:
    print("Por favor, ingresa 'hombre' o 'mujer'.")
    sexo = input().lower()

talla = float(input("Ingresa tu altura en metros: "))
peso = float(input("Ingresa tu peso en kg: "))

# Ajustes de área superficial
cambio_area_por_kg = 0.01
cambio_area_por_cm = 0.01

# Calcular masa y área superficial
masa, area_superficial = calcular_masa(talla, peso, altura_hombre_estandar, peso_hombre_estandar, altura_mujer_estandar, peso_mujer_estandar)

# Lista de actividades y tasa metabólica asociada (W/m^2 por hora)
actividades = {
    "Dormir": 40,
    "Caminar": 160,
    "Actividad física moderada": 175,
    "Ejercicio aeróbico moderado": 300,
    "Actividad física baja": 60
}

# Solicitar la duración de cada actividad
duracion_actividades = {}
for actividad in actividades:
    horas = float(input(f"¿Cuántas horas dedicas a {actividad.lower()}? "))
    duracion_actividades[actividad] = horas

# Calcular tasa metabólica
tasa_metabolica = calcular_tasa_metabolica(masa, duracion_actividades)

# Comparar con la potencia de un foco
diferencia_foco = comparar_con_foco(tasa_metabolica)

# Calcular tasa metabólica en kcal/día
tasa_metabolica_kcal = kcal_por_dia(tasa_metabolica)

# Comparar con los valores estándar sugeridos por dietistas
diferencia_estandar = comparar_con_estandar(tasa_metabolica_kcal)

# Convertir tasa metabólica a vatios por segundo
tasa_watts_por_segundo = watts_por_segundo(tasa_metabolica)

# Mostrar resultados explicativos en notación científica
print("\nResultados:")
print(f"  - Valor de tu masa: {masa:.2e} kg/m^2")
print(f"  - Área superficial ajustada: {area_superficial:.2e} m^2")
print(f"  - Estimación de tasa metabólica: {tasa_metabolica:.2e} J/hora ({tasa_watts_por_segundo:.4e} W/segundo)")
print(f"  - Comparación con la potencia de un foco de 100 W por hora: Diferencia de {diferencia_foco:.2e} J/hora")
print(f"  - Estimación de tasa metabólica en kcal/día: {tasa_metabolica_kcal:.2e} kcal/día")
print(f"  - Diferencia respecto a los valores estándar: {diferencia_estandar:.2e} kcal/día")
