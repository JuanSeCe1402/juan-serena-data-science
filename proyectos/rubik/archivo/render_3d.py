import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import kociemba
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
from PIL import Image, ImageTk
import math

class CubeRenderer:
    """Clase encargada del renderizado 3D del cubo"""
    def __init__(self):
        self.rot_x = 30
        self.rot_y = -45
        self.rot_z = 0
        self.last_x = 0
        self.last_y = 0
        self.size = 0.5
        self.dragging = False
        self.animation_queue = []
        self.animation_progress = 0
        self.animation_speed = 5
        self.colors = {
            'W': (1.0, 1.0, 1.0),  # Blanco
            'Y': (1.0, 1.0, 0.0),  # Amarillo
            'R': (1.0, 0.0, 0.0),  # Rojo
            'O': (1.0, 0.5, 0.0),  # Naranja
            'B': (0.0, 0.0, 1.0),  # Azul
            'G': (0.0, 1.0, 0.0),  # Verde
            'N': (0.2, 0.2, 0.2)   # Negro (caras internas)
        }

    def init_gl(self, width, height):
        """Inicializa OpenGL con la configuración básica"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLight(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
        self.resize_gl(width, height)

    def resize_gl(self, width, height):
        """Maneja el redimensionamiento de la ventana OpenGL"""
        if height == 0:
            height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width)/float(height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_cube_face(self, color):
        """Dibuja una cara individual del cubo"""
        glBegin(GL_QUADS)
        glColor3fv(color)
        s = self.size
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        glEnd()

    def draw_cube(self, state):
        """Dibuja el cubo completo"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10.0)
        glRotatef(self.rot_x, 1.0, 0.0, 0.0)
        glRotatef(self.rot_y, 0.0, 1.0, 0.0)
        glRotatef(self.rot_z, 0.0, 0.0, 1.0)

        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    glPushMatrix()
                    glTranslatef(x * 2.1 * self.size, y * 2.1 * self.size, z * 2.1 * self.size)
                    self.draw_subcube(x, y, z, state)
                    glPopMatrix()

    def draw_subcube(self, x, y, z, state):
        """Dibuja un subcubo individual con sus colores correspondientes"""
        face_indices = {
            'F': 18 + (y + 1) * 3 + (x + 1),
            'B': 36 + (y + 1) * 3 + (-x + 1),
            'R': 27 + (y + 1) * 3 + (z + 1),
            'L': 9 + (y + 1) * 3 + (-z + 1),
            'U': 0 + (-z + 1) * 3 + (x + 1),
            'D': 45 + (z + 1) * 3 + (x + 1)
        }

        for face, idx in face_indices.items():
            glPushMatrix()
            if face == 'F':
                self.draw_cube_face(self.colors[state[idx]] if z == 1 else self.colors['N'])
            elif face == 'B':
                glRotatef(180, 0, 1, 0)
                self.draw_cube_face(self.colors[state[idx]] if z == -1 else self.colors['N'])
            elif face == 'R':
                glRotatef(90, 0, 1, 0)
                self.draw_cube_face(self.colors[state[idx]] if x == 1 else self.colors['N'])
            elif face == 'L':
                glRotatef(270, 0, 1, 0)
                self.draw_cube_face(self.colors[state[idx]] if x == -1 else self.colors['N'])
            elif face == 'U':
                glRotatef(90, 1, 0, 0)
                self.draw_cube_face(self.colors[state[idx]] if y == 1 else self.colors['N'])
            elif face == 'D':
                glRotatef(270, 1, 0, 0)
                self.draw_cube_face(self.colors[state[idx]] if y == -1 else self.colors['N'])
            glPopMatrix()

class RubiksCube:
    """Clase que maneja la lógica del cubo de Rubik"""
    def __init__(self):
        self.state = ['W'] * 9 + ['R'] * 9 + ['B'] * 9 + ['O'] * 9 + ['G'] * 9 + ['Y'] * 9
        self.move_history = []
        self.future_moves = []
        self.renderer = CubeRenderer()

    def apply_move(self, move):
        if move not in ['U', 'D', 'L', 'R', 'F', 'B', "U'", "D'", "L'", "R'", "F'", "B'", 'U2', 'D2', 'L2', 'R2', 'F2', 'B2']:
            raise ValueError(f"Movimiento inválido: {move}")
        if len(move) == 2 and move[1] == '2':
            self.apply_move(move[0])
            self.apply_move(move[0])
            return

        faces = {'U': 0, 'L': 9, 'F': 18, 'R': 27, 'B': 36, 'D': 45}
        rotations = {
            'U': ([0,1,2,5,8,7,6,3], [36,37,38,18,19,20,9,10,11,45,46,47]),
            'L': ([9,10,11,14,17,16,15,12], [0,3,6,18,21,24,45,48,51,38,41,44]),
            'F': ([18,19,20,23,26,25,24,21], [6,7,8,27,30,33,47,46,45,17,14,11]),
            'R': ([27,28,29,32,35,34,33,30], [8,5,2,36,39,42,47,50,53,26,23,20]),
            'B': ([36,37,38,41,44,43,42,39], [2,1,0,9,12,15,53,52,51,35,32,29]),
            'D': ([45,46,47,50,53,52,51,48], [24,25,26,33,34,35,42,43,44,15,16,17])
        }

        face = faces[move[0]]
        direction = 1 if len(move) == 1 else -1
        new_face = [self.state[face + i] for i in rotations[move[0]][0][::direction]]
        for i, new_pos in enumerate(rotations[move[0]][1]):
                self.state[new_pos] = edge[(i - direction * 3) % len(edge)]
        self.move_history.append(move)
        self.future_moves.clear()

    def shuffle(self, num_moves=20):
        moves = ['U', 'D', 'L', 'R', 'F', 'B', "U'", "D'", "L'", "R'", "F'", "B'", 'U2', 'D2', 'L2', 'R2', 'F2', 'B2']
        for _ in range(num_moves):
            self.apply_move(random.choice(moves))

    def is_solved(self):
        return all(self.state[i] == self.state[i - i % 9] for i in range(54))

class RubiksCubeSolver:
    """Clase que maneja la interfaz gráfica para la simulación del cubo de Rubik"""
    def __init__(self, root):
        self.root = root
        self.root.title("Rubik's Cube Solver")
        self.cube = RubiksCube()
        self.init_ui()
        self.solution = []

    def init_ui(self):
        frame = tk.Frame(self.root)
        frame.pack()

        # Área de OpenGL para el renderizado del cubo
        self.canvas = tk.Canvas(frame, width=400, height=400)
        self.canvas.pack()

        # Botones de control
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Shuffle", command=self.shuffle_cube).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Solve", command=self.solve_cube).pack(side=tk.LEFT)

        # Área para mostrar los pasos de solución
        self.solution_text = scrolledtext.ScrolledText(self.root, width=40, height=10)
        self.solution_text.pack()

    def shuffle_cube(self):
        self.cube.shuffle()
        self.update_display()

    def solve_cube(self):
        # Convierte el estado del cubo en el formato adecuado para el solver de Kociemba
        cube_str = ''.join(self.cube.state)
        try:
            self.solution = kociemba.solve(cube_str).split()
            self.solution_text.insert(tk.END, "Solución: " + ' '.join(self.solution) + "\n")
        except Exception as e:
            messagebox.showerror("Error", "No se pudo resolver el cubo: " + str(e))

    def update_display(self):
        self.canvas.delete("all")
        self.cube.renderer.draw_cube(self.cube.state)

# Ejecuta la aplicación
root = tk.Tk()
app = RubiksCubeSolver(root)
root.mainloop()
