import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json, os
from cotizacion_pdf import generar_pdf
from graficos import mostrar_grafico_costos


class CalculadoraImpresion3D:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Cortex Studio 3D - Calculadora de Costos")
        self.ventana.geometry("700x850")
        self.ventana.configure(bg="#1c1c1c")

        self.archivo_config = "config_impresion3d.json"
        self.precios_material = {
            "PLA": 490, "ABS": 350, "PETG": 400, "TPU": 500, "Resina": 600
        }

        self.cargar_configuracion()
        self.ventana.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1c1c1c", foreground="white", font=("Segoe UI", 10))
        style.configure("TFrame", background="#1c1c1c")
        style.configure("TLabelframe", background="#2a2a2a", foreground="#00bcd4", font=('Segoe UI', 10, 'bold'))

        self.crear_interfaz()

    def cargar_configuracion(self):
        if os.path.exists(self.archivo_config):
            try:
                with open(self.archivo_config, 'r') as f:
                    config = json.load(f)
                    self.precios_material = config.get('materiales', self.precios_material)
            except:
                pass

    def guardar_configuracion(self):
        try:
            with open(self.archivo_config, 'w') as f:
                json.dump({'materiales': self.precios_material}, f, indent=2)
        except:
            pass

    def al_cerrar(self):
        self.guardar_configuracion()
        self.ventana.destroy()

    def crear_interfaz(self):
        header = ttk.Frame(self.ventana, padding=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="🧠 Cortex Studio 3D", font=("Segoe UI", 20, "bold"),
                 fg="#00bcd4", bg="#1c1c1c").pack()
        tk.Label(header, text="Calculadora de Costos de Impresión 3D",
                 font=("Segoe UI", 12), fg="white", bg="#1c1c1c").pack(pady=5)

        main_frame = ttk.Frame(self.ventana, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        frame_datos = ttk.Labelframe(main_frame, text="Datos de Impresión", padding=15)
        frame_datos.pack(fill=tk.X, pady=10)
        ttk.Label(frame_datos, text="Material:").grid(row=0, column=0, sticky=tk.W)
        self.combo_material = ttk.Combobox(frame_datos, values=list(self.precios_material.keys()),
                                           width=20, state="readonly")
        self.combo_material.grid(row=0, column=1, padx=5, pady=5)
        self.combo_material.current(0)

        tk.Button(frame_datos, text="➕ Agregar material", command=self.agregar_material,
                  bg="#00bcd4", fg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5)

        ttk.Label(frame_datos, text="Peso (gramos):").grid(row=1, column=0, sticky=tk.W)
        self.entry_peso = ttk.Entry(frame_datos, width=20)
        self.entry_peso.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_datos, text="Tiempo (horas):").grid(row=2, column=0, sticky=tk.W)
        self.entry_tiempo = ttk.Entry(frame_datos, width=20)
        self.entry_tiempo.grid(row=2, column=1, padx=5, pady=5)

        frame_costos = ttk.Labelframe(main_frame, text="Costos Adicionales", padding=15)
        frame_costos.pack(fill=tk.X, pady=10)
        etiquetas = ["Costo electricidad ($/kWh):", "Consumo impresora (W):", "Margen de ganancia (%):"]
        valores = ["5", "200", "50"]
        self.entries = []
        for i, (etq, val) in enumerate(zip(etiquetas, valores)):
            ttk.Label(frame_costos, text=etq).grid(row=i, column=0, sticky=tk.W)
            entry = ttk.Entry(frame_costos, width=20)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, val)
            self.entries.append(entry)
        self.entry_electricidad, self.entry_consumo, self.entry_margen = self.entries

        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(fill=tk.X, pady=15)
        botones = [
            ("🔢 Calcular Costo", self.calcular_costo, "#0078d7"),
            ("💾 Guardar PDF", self.exportar_pdf, "#9C27B0"),
            ("🧾 Generar Nota", self.exportar_nota, "#FFC107"),
            ("📊 Ver Gráfico", self.mostrar_grafico, "#4CAF50"),
            ("🗑️ Limpiar", self.limpiar_campos, "#f44336")
        ]
        for texto, comando, color in botones:
            btn = tk.Button(frame_botones, text=texto, command=comando,
                            bg=color, fg="white", font=("Segoe UI", 11, "bold"),
                            padx=20, pady=8, relief="flat")
            btn.pack(side=tk.LEFT, expand=True, padx=5)

        frame_resultado = ttk.Labelframe(main_frame, text="Resultados", padding=15)
        frame_resultado.pack(fill=tk.BOTH, expand=True, pady=10)
        self.text_resultado = tk.Text(frame_resultado, height=15, width=70,
                                      bg="#000000", fg="#00FF41", insertbackground="white",
                                      font=("Consolas", 10))
        self.text_resultado.pack(fill=tk.BOTH, expand=True)

    def agregar_material(self):
        nombre = simpledialog.askstring("Nuevo Material", "Nombre del material:", parent=self.ventana)
        if nombre:
            precio = simpledialog.askfloat("Precio por kg", f"Precio por kg de {nombre} ($):",
                                           parent=self.ventana, minvalue=0.1)
            if precio:
                self.precios_material[nombre] = precio
                self.combo_material['values'] = list(self.precios_material.keys())
                self.combo_material.set(nombre)
                messagebox.showinfo("Material agregado", f"{nombre} añadido con ${precio}/kg")

    def calcular_costo(self):
        try:
            material = self.combo_material.get()
            peso = float(self.entry_peso.get())
            horas = float(self.entry_tiempo.get())
            kwh = float(self.entry_electricidad.get())
            consumo = float(self.entry_consumo.get())
            margen = float(self.entry_margen.get())

            precio_kg = self.precios_material[material]
            costo_material = (peso / 1000) * precio_kg
            consumo_kwh = (consumo / 1000) * horas
            costo_electricidad = consumo_kwh * kwh
            costo_base = costo_material + costo_electricidad
            ganancia = costo_base * (margen / 100)
            precio_final = costo_base + ganancia

            self.resultados = {
                "material": material, "peso": peso, "horas": horas,
                "costo_material": costo_material, "costo_electricidad": costo_electricidad,
                "costo_base": costo_base, "ganancia": ganancia, "precio_final": precio_final
            }

            texto = f"""
================= REPORTE CORTEX =================
Material: {material}
Peso: {peso} g ({peso / 1000:.3f} kg)
Tiempo: {horas} h
----------------------------------------------
Costo material: ${costo_material:.2f}
Costo electricidad: ${costo_electricidad:.2f}
----------------------------------------------
Costo base: ${costo_base:.2f}
Ganancia ({margen}%): ${ganancia:.2f}
💰 PRECIO FINAL SUGERIDO: ${precio_final:.2f}
==================================================
"""
            self.text_resultado.delete(1.0, tk.END)
            self.text_resultado.insert(tk.END, texto)
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {e}")

    def exportar_pdf(self):
        if not hasattr(self, "resultados"):
            messagebox.showwarning("Atención", "Calcula primero el costo.")
            return
        cliente = simpledialog.askstring("Cliente", "Nombre del cliente:")
        if cliente:
            generar_pdf(cliente, self.resultados)
            messagebox.showinfo("PDF generado", f"Se creó la cotización para {cliente}")

    def exportar_nota(self):
        if not hasattr(self, "resultados"):
            messagebox.showwarning("Atención", "Calcula primero el costo.")
            return

        cliente = simpledialog.askstring("Cliente", "Nombre del cliente:")
        if cliente:
            try:
                from nota_pdf import generar_nota_pdf
                generar_nota_pdf(cliente, self.resultados)
                messagebox.showinfo("Nota generada", f"Se creó la nota de cobro para {cliente}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar la nota: {e}")

    def mostrar_grafico(self):
        if not hasattr(self, "resultados"):
            messagebox.showwarning("Atención", "Calcula primero el costo.")
            return
        mostrar_grafico_costos(self.resultados)

    def limpiar_campos(self):
        for e, val in zip(self.entries, ["5", "200", "50"]):
            e.delete(0, tk.END)
            e.insert(0, val)
        self.entry_peso.delete(0, tk.END)
        self.entry_tiempo.delete(0, tk.END)
        self.text_resultado.delete(1.0, tk.END)
        self.combo_material.current(0)

    def ejecutar(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    app = CalculadoraImpresion3D()
    app.ejecutar()
