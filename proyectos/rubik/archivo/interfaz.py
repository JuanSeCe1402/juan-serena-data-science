import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import kociemba  # Necesitarás instalar esta biblioteca (pip install kociemba)

class RubiksCube:
    def __init__(self):
        self.state = ['W'] * 9 + ['R'] * 9 + ['B'] * 9 + ['O'] * 9 + ['G'] * 9 + ['Y'] * 9
        self.move_history = []
        self.future_moves = []

    def set_state(self, state):
        if len(state) != 54 or not all(c in 'WRBOGY' for c in state):
            raise ValueError("Estado del cubo inválido")
        self.state = list(state)

    def apply_move(self, move):
        if move not in ['U', 'D', 'L', 'R', 'F', 'B', "U'", "D'", "L'", "R'", "F'", "B'"]:
            raise ValueError(f"Movimiento inválido: {move}")

        faces = {'U': 0, 'L': 9, 'F': 18, 'R': 27, 'B': 36, 'D': 45}
        rotations = {
            'U': ([0, 1, 2, 5, 8, 7, 6, 3], [36, 37, 38, 18, 19, 20, 9, 10, 11, 45, 46, 47]),
            'L': ([9, 10, 11, 14, 17, 16, 15, 12], [0, 3, 6, 18, 21, 24, 45, 48, 51, 38, 41, 44]),
            'F': ([18, 19, 20, 23, 26, 25, 24, 21], [6, 7, 8, 27, 30, 33, 47, 46, 45, 17, 14, 11]),
            'R': ([27, 28, 29, 32, 35, 34, 33, 30], [8, 5, 2, 36, 39, 42, 47, 50, 53, 26, 23, 20]),
            'B': ([36, 37, 38, 41, 44, 43, 42, 39], [2, 1, 0, 9, 12, 15, 53, 52, 51, 35, 32, 29]),
            'D': ([45, 46, 47, 50, 53, 52, 51, 48], [24, 25, 26, 33, 34, 35, 42, 43, 44, 15, 16, 17])
        }

        face, direction = faces[move[0]], 1 if len(move) == 1 else -1
        face_rotation, edge_rotation = rotations[move[0]]

        new_face = [self.state[face + i] for i in face_rotation[::direction]]
        for i, new_pos in enumerate(face_rotation):
            self.state[face + new_pos] = new_face[i]

        edge = [self.state[i] for i in edge_rotation]
        edge = edge[3 * direction:] + edge[:3 * direction]
        for i, pos in enumerate(edge_rotation):
            self.state[pos] = edge[i]

        self.move_history.append(move)
        self.future_moves = []

    def undo_move(self):
        if not self.move_history:
            return None
        move = self.move_history.pop()
        inverse_move = move[0] if "'" in move else move + "'"
        self.apply_move(inverse_move)
        self.move_history.pop()
        self.future_moves.append(move)
        return inverse_move

    def redo_move(self):
        if not self.future_moves:
            return None
        move = self.future_moves.pop()
        self.apply_move(move)
        return move

    def scramble(self):
        moves = ['U', 'D', 'L', 'R', 'F', 'B', "U'", "D'", "L'", "R'", "F'", "B'"]
        scramble_moves = [random.choice(moves) for _ in range(20)]
        for move in scramble_moves:
            self.apply_move(move)
        return ' '.join(scramble_moves)

    def solve(self):
        try:
            cube_state = ''.join(self.state)
            cube_str = self.convert_to_kociemba(cube_state)
            solution = kociemba.solve(cube_str)
            return solution
        except Exception as e:
            raise ValueError(f"Error resolviendo el cubo: {str(e)}")

    def convert_to_kociemba(self, state):
        mapping = {'W': 'U', 'R': 'R', 'B': 'F', 'O': 'L', 'G': 'B', 'Y': 'D'}
        return ''.join(mapping[c] for c in state)

class RubiksCubeSolver:
    def __init__(self, master):
        self.master = master
        master.title("Solucionador de Cubo de Rubik")

        self.cube = RubiksCube()
        self.colors = ['white', 'red', 'blue', 'orange', 'green', 'yellow']
        self.color_map = {'W': 'white', 'R': 'red', 'B': 'blue', 'O': 'orange', 'G': 'green', 'Y': 'yellow'}
        self.reverse_color_map = {v: k for k, v in self.color_map.items()}
        self.current_color = tk.StringVar(value=self.colors[0])

        self.create_layout()

    def create_layout(self):
        main_frame = tk.Frame(self.master)
        main_frame.pack(padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=10)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, padx=10)

        self.create_color_selector(left_frame)
        self.create_cube_faces(left_frame)
        self.create_buttons(right_frame)
        self.create_move_history(right_frame)

    def create_color_selector(self, parent):
        color_frame = tk.Frame(parent)
        color_frame.pack(pady=10)

        tk.Label(color_frame, text="Selecciona un color:").pack()

        for color in self.colors:
            rb = tk.Radiobutton(color_frame, variable=self.current_color, value=color,
                                bg=color, indicatoron=0, width=3, height=1)
            rb.pack(side=tk.LEFT, padx=2)

    def create_cube_faces(self, parent):
        self.faces = {}
        face_layout = [
            (1, 0, 'U'), (0, 1, 'L'), (1, 1, 'F'), (2, 1, 'R'), (3, 1, 'B'), (1, 2, 'D')
        ]

        cube_frame = tk.Frame(parent)
        cube_frame.pack(pady=10)

        for col, row, face in face_layout:
            face_frame = tk.Frame(cube_frame)
            face_frame.grid(row=row, column=col, padx=5, pady=5)
            tk.Label(face_frame, text=face).grid(row=0, column=1)
            self.faces[face] = []
            for i in range(3):
                for j in range(3):
                    square = tk.Button(face_frame, width=2, height=1, bg='lightgray',
                                       command=lambda f=face, x=i, y=j: self.change_color(f, x, y))
                    square.grid(row=i+1, column=j, padx=1, pady=1)
                    self.faces[face].append(square)

    def create_buttons(self, parent):
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Mezclar", command=self.scramble_cube).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Resolver", command=self.solve_cube).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Deshacer", command=self.undo_move).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Rehacer", command=self.redo_move).pack(fill=tk.X, pady=2)

        tk.Label(button_frame, text="Ingresa movimientos:").pack(pady=(10, 2))
        self.move_entry = tk.Entry(button_frame, width=20)
        self.move_entry.pack(pady=2)
        tk.Button(button_frame, text="Aplicar Movimientos", command=self.apply_user_moves).pack(fill=tk.X, pady=2)

    def create_move_history(self, parent):
        history_frame = tk.Frame(parent)
        history_frame.pack(pady=10)

        tk.Label(history_frame, text="Historial de movimientos:").pack()

        self.history_text = scrolledtext.ScrolledText(history_frame, width=30, height=10)
        self.history_text.pack(pady=5)

        tk.Button(history_frame, text="Guardar Historial", command=self.save_history_to_file).pack(fill=tk.X)

    def change_color(self, face, row, col):
        # Cambia el color del botón en la interfaz según el color seleccionado
        index = row * 3 + col
        selected_color = self.current_color.get()
        self.faces[face][index].config(bg=selected_color)
        color_code = self.reverse_color_map[selected_color]

        face_map = {'U': 0, 'L': 9, 'F': 18, 'R': 27, 'B': 36, 'D': 45}
        cube_index = face_map[face] + index
        self.cube.state[cube_index] = color_code

    def scramble_cube(self):
        scramble_moves = self.cube.scramble()
        self.update_history(f"Mezcla: {scramble_moves}")
        self.update_interface()

    def solve_cube(self):
        try:
            solution = self.cube.solve()
            self.update_history(f"Solución: {solution}")
            messagebox.showinfo("Solución", f"Movimientos para resolver: {solution}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def undo_move(self):
        inverse_move = self.cube.undo_move()
        if inverse_move:
            self.update_history(f"Deshacer: {inverse_move}")
            self.update_interface()

    def redo_move(self):
        move = self.cube.redo_move()
        if move:
            self.update_history(f"Rehacer: {move}")
            self.update_interface()

    def apply_user_moves(self):
        moves = self.move_entry.get().split()
        for move in moves:
            try:
                self.cube.apply_move(move)
                self.update_history(f"Movimiento: {move}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                break
        self.update_interface()

    def update_history(self, text):
        self.history_text.insert(tk.END, text + "\n")
        self.history_text.see(tk.END)

    def save_history_to_file(self):
        history = self.history_text.get(1.0, tk.END).strip()
        if history:
            with open("historial_de_movimientos.txt", "w") as file:
                file.write(history)
            messagebox.showinfo("Guardado", "Historial guardado en 'historial_de_movimientos.txt'")
        else:
            messagebox.showwarning("Advertencia", "No hay movimientos para guardar.")

    def update_interface(self):
        # Actualiza la interfaz con el estado actual del cubo
        face_map = {'U': 0, 'L': 9, 'F': 18, 'R': 27, 'B': 36, 'D': 45}
        for face, start_idx in face_map.items():
            for i in range(9):
                color_code = self.cube.state[start_idx + i]
                color = self.color_map[color_code]
                self.faces[face][i].config(bg=color)


if __name__ == "__main__":
    root = tk.Tk()
    rubiks_solver = RubiksCubeSolver(root)
    root.mainloop()
