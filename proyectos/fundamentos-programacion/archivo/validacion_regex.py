import re

def validar_cadena(cadena):
    # Definir las constantes
    inicial_i = "0123456"
    w = "gc"
    wI = "cg"
    j = "yozedh"

    # Longitudes de las partes de la cadena
    len_inicial_i = len(inicial_i)
    len_w = len(w)
    len_wI = len(wI)
    len_j = len(j)

    # Verificar la longitud de la cadena
    len_cadena = len(cadena)
    if len_cadena < len_inicial_i + len_w + len_j * 2:
        return False

    # Verificar la parte inicial_i
    if not cadena.startswith(inicial_i):
        return False

    # Verificar la parte w^n
    i = len_inicial_i
    n = 0
    while cadena[i:i+len_w] == w:
        n += 1
        i += len_w
    if n == 0:
        return False

    # Verificar la parte i
    if cadena[i:i+len_inicial_i] != inicial_i:
        return False
    i += len_inicial_i

    # Verificar la parte wI^2n
    j_index = len_cadena - len_j * 2
    for k in range(n * 2):
        if cadena[i:i+len_wI] != wI:
            return False
        i += len_wI

    # Verificar la parte j^2
    if cadena[i:i+len_j] != j or cadena[j_index:j_index+len_j] != j:
        return False

    return True

while True:
    cadena = input("Introduce la cadena a verificar: ")
    if validar_cadena(cadena):
        print("La cadena es válida.")
    else:
        print("La cadena no es válida.")
    opcion = int(input("Desea ingresar otra cadena? 1.Si 2.No\n"))
    if opcion != 1:
        break
