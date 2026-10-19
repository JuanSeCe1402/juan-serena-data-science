from automata.fa.dfa import DFA

# Definimos los datos de matrícula, iniciales y nombre
matricula = "2086172"
iniciales = "dc"
nombre = "luis"

# Creamos los estados del autómata
estados = [f"{matricula}{iniciales}{iniciales[::-1]}{nombre}{nombre}",
           f"{matricula}{iniciales}",
           f"{iniciales[::-1]}{matricula}{iniciales}",
           f"{nombre}{nombre}",
           "inicial",
           "final"]

# Definimos las transiciones del autómata
transiciones = {
    "inicial": {f"{matricula}{iniciales}{iniciales[::-1]}{nombre}{nombre}": f"{matricula}{iniciales}{iniciales[::-1]}{nombre}{nombre}"},
    f"{matricula}{iniciales}": {f"{iniciales[::-1]}": f"{iniciales[::-1]}{matricula}{iniciales}"},
    f"{iniciales[::-1]}{matricula}{iniciales}": {f"{iniciales[::-1]}{matricula}{iniciales}": f"{iniciales[::-1]}{matricula}{iniciales}",
                                                 f"{iniciales}": "final"},
    f"{nombre}{nombre}": {},
    f"{matricula}{iniciales}{iniciales[::-1]}{nombre}{nombre}": {}
}

# Creamos el autómata
dfa = DFA(estados, alfabeto=set(matricula + iniciales + iniciales[::-1] + nombre), transiciones=transiciones, inicial="inicial", finales=["final"])

# Función para validar cadenas
def validar_cadena(cadena):
    aceptada = dfa.accepts_input(cadena)
    if aceptada:
        print(f"La cadena '{cadena}' es válida para la gramática dada.")
    else:
        print(f"La cadena '{cadena}' no es válida para la gramática dada.")

# Ejemplo de uso
validar_cadena(f"{matricula}{iniciales}{iniciales[::-1]}{nombre}{nombre}")  # Válida
validar_cadena(f"{matricula}{iniciales[::-1]}{iniciales}{iniciales[::-1]}{matricula}{iniciales}")  # Válida
validar_cadena(f"{nombre}{nombre}")  # Válida
validar_cadena("cadena_invalida")  # Inválida
