# Juan Manuel Serena,uso de Quicksort para la implementacion en NumPy

def quicksort(arr):
  #  """Implementación del algoritmo Quicksort."""
    if len(arr) <= 1:
        return arr
    else:
        pivot = arr[0]
        less = [x for x in arr[1:] if x <= pivot]
        greater = [x for x in arr[1:] if x > pivot]
        return quicksort(less) + [pivot] + quicksort(greater)

def get_user_input():
 #   """Obtiene la lista de números del usuario."""
    while True:
        try:
            input_list = input("Ingresa la lista de números separados por espacios: ")
            user_list = [int(x) for x in input_list.split()]
            return user_list
        except ValueError:
            print("Por favor, ingresa números válidos.")

def main():
  #  """Función principal que ejecuta el programa."""
    user_list = get_user_input()

    if not user_list:
        print("La lista está vacía. No hay nada que ordenar.")
    else:
        sorted_list = quicksort(user_list)
        print("Lista ordenada:", sorted_list)

if __name__ == "__main__":
    main()
