import tkinter as tk
from tkinter.simpledialog import askfloat
from tkinter import scrolledtext, messagebox
import math
from tkinter import filedialog
from claude_analyzer import ClaudeAnalyzer, load_env_file

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawing App - Planos para Avalúos")

        # Configuración del canvas
        self.canvas = tk.Canvas(root, width=1335, height=660, bg="white")
        self.canvas.pack()

        self.start_point = None
        self.lines = []
        self.labels = []
        self.selected_point = None
        self.dragging = False
        self.fixed_movement_mode = False  # Modo para mover extremo en ángulos específicos
        self.SCALE = 50  # 1 metro = 50 píxeles
        self.ANCHOR_THRESHOLD = 10  # Distancia mínima para considerar un punto como anclaje
        self.UNIFY_THRESHOLD = 15  # Distancia mínima para unificar puntos
        self.current_y_offset = 0  # Variable para mantener el desplazamiento vertical de las líneas
        self.adding_label_mode = False  # Modo para agregar etiquetas adicionales
        
        # Inicializar Claude Analyzer (con manejo de errores)
        self.claude_analyzer = None
        self._initialize_claude()

        # Binding de eventos
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.move_point)
        self.canvas.bind("<ButtonRelease-1>", self.release_point)
        self.canvas.bind("<Button-3>", self.on_label_right_click)

        self.setup_ui()

    def setup_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Caja de texto para la longitud de la línea
        self.length_var = tk.DoubleVar()
        length_entry = tk.Entry(toolbar, textvariable=self.length_var)
        length_entry.pack(side=tk.LEFT)

        # Botón para dibujar la línea
        draw_button = tk.Button(toolbar, text="Dibujar Línea", command=self.draw_line)
        draw_button.pack(side=tk.LEFT)

        # Botón para establecer punto de inicio
        set_start_button = tk.Button(toolbar, text="Establecer Punto de Inicio", command=self.set_start_point)
        set_start_button.pack(side=tk.LEFT)

        # Botón para limpiar el canvas
        clear_button = tk.Button(toolbar, text="Limpiar", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT)

        # Botón para exportar a SVG
        export_button = tk.Button(toolbar, text="Exportar a SVG", command=self.export_to_svg)
        export_button.pack(side=tk.LEFT)

        # Botón para activar/desactivar modo de movimiento fijo
        self.fixed_movement_button = tk.Button(toolbar, text="Activar Movimiento Fijo", command=self.toggle_fixed_movement_mode)
        self.fixed_movement_button.pack(side=tk.LEFT)

        # Campo de texto para la etiqueta adicional
        self.extra_label_var = tk.StringVar()
        extra_label_entry = tk.Entry(toolbar, textvariable=self.extra_label_var)
        extra_label_entry.pack(side=tk.LEFT)

        # Botón para agregar la etiqueta adicional
        add_label_button = tk.Button(toolbar, text="Agregar Etiqueta", command=self.enable_add_label_mode)
        add_label_button.pack(side=tk.LEFT)
        
        # Separador visual
        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)
        
        # Botón para análisis con IA
        self.ai_button = tk.Button(
            toolbar, 
            text="🤖 Análisis IA", 
            command=self.analyze_with_ai,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.ai_button.pack(side=tk.LEFT, padx=5)

    def toggle_fixed_movement_mode(self):
        self.fixed_movement_mode = not self.fixed_movement_mode
        if self.fixed_movement_mode:
            self.fixed_movement_button.config(bg="green", text="Movimiento Fijo Activado")
            print("Modo de movimiento fijo activado.")
        else:
            self.fixed_movement_button.config(bg="SystemButtonFace", text="Activar Movimiento Fijo")
            print("Modo de movimiento fijo desactivado.")

    def set_start_point(self):
        self.start_point = None
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def draw_line(self):
        if self.start_point is None:
            self.start_point = (50, self.current_y_offset + 50)  # Inicia en la parte superior con un margen de 50 píxeles
        else:
            length = self.length_var.get()
            scaled_length = length * self.SCALE
            end_point = (self.start_point[0] + scaled_length, self.start_point[1])

            # Crear la línea en el canvas
            line = self.canvas.create_line(self.start_point, end_point, fill="black", width=2)
            self.lines.append({
                "start": self.start_point,
                "end": end_point,
                "line": line,
                "length": length
            })
            self.create_label(self.start_point, end_point, length)
            self.draw_anchor_points(self.start_point, end_point)

            # Ajustar la posición en Y para que la nueva línea se dibuje más abajo
            self.current_y_offset += 30  # Desplazamos las líneas 30 píxeles hacia abajo cada vez
            self.start_point = (50, self.current_y_offset + 50)

    def on_canvas_click(self, event):
        if self.adding_label_mode:
            self.add_extra_label(event)
        else:
            if self.start_point is None:
                self.start_point = (event.x, event.y)
                self.canvas.create_oval(event.x-5, event.y-5, event.x+5, event.y+5, fill="red")
            else:
                for line in self.lines:
                    if self.is_within_point(event.x, event.y, *line["start"]):
                        self.selected_point = ("start", line)
                        self.dragging = True
                    elif self.is_within_point(event.x, event.y, *line["end"]):
                        self.selected_point = ("end", line)
                        self.dragging = True

    def is_within_point(self, click_x, click_y, point_x, point_y):
        return (
            click_x >= point_x - self.ANCHOR_THRESHOLD and
            click_x <= point_x + self.ANCHOR_THRESHOLD and
            click_y >= point_y - self.ANCHOR_THRESHOLD and
            click_y <= point_y + self.ANCHOR_THRESHOLD
        )

    def move_point(self, event):
        if self.dragging and self.selected_point is not None:
            point_type, line = self.selected_point
            new_x, new_y = event.x, event.y

            if self.fixed_movement_mode:
                # Calcular ángulos en múltiplos de 45 grados
                start_x, start_y = line["start"] if point_type == "end" else line["end"]
                angle_radians = math.atan2(new_y - start_y, new_x - start_x)
                angle_degrees = math.degrees(angle_radians)
                snap_angle = round(angle_degrees / 45) * 45
                snap_radians = math.radians(snap_angle)
                length = math.sqrt((new_x - start_x) ** 2 + (new_y - start_y) ** 2)
                new_x = start_x + length * math.cos(snap_radians)
                new_y = start_y + length * math.sin(snap_radians)

            # Unificación de puntos de anclaje cercanos
            for other_line in self.lines:
                if line != other_line:
                    if self.is_within_point(new_x, new_y, *other_line["start"]):
                        new_x, new_y = other_line["start"]
                    elif self.is_within_point(new_x, new_y, *other_line["end"]):
                        new_x, new_y = other_line["end"]

            if point_type == "end":
                line["end"] = (new_x, new_y)
                self.canvas.coords(line["line"], *line["start"], new_x, new_y)
            elif point_type == "start":
                line["start"] = (new_x, new_y)
                self.canvas.coords(line["line"], new_x, new_y, *line["end"])

            # Actualizar la longitud y la etiqueta
            line["length"] = self.calculate_length(line["start"], line["end"])
            self.update_label(line)
            self.redraw_canvas()

    def release_point(self, event):
        self.dragging = False
        self.selected_point = None

    def create_label(self, start, end, length):
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        label = self.canvas.create_text(mid_x, mid_y - 10, text=f"{length:.2f} m", font=("Arial", 12))

        # Añadir evento de doble clic para editar la longitud
        self.canvas.tag_bind(label, "<Double-1>", lambda event, idx=len(self.lines) - 1: self.on_label_double_click(idx))

        self.labels.append((label, len(self.lines) - 1))

    def on_label_right_click(self, event):
        clicked_label = None
        for label, index in self.labels:
            x, y = self.canvas.coords(label)
            if abs(event.x - x) < 20 and abs(event.y - y) < 10:
                clicked_label = (label, index)
                break

        if clicked_label:
            new_length = askfloat("Editar Longitud", "Introduce la nueva longitud (en metros):")
            if new_length is not None:
                self.update_line_length(clicked_label[1], new_length)

    def on_label_double_click(self, index):
        new_length = askfloat("Editar Longitud", "Introduce la nueva longitud (en metros):")
        if new_length is not None:
            self.update_line_length(index, new_length)

    def update_line_length(self, index, new_length):
        line = self.lines[index]
        angle = self.calculate_angle(line["start"], line["end"])
        scaled_length = new_length * self.SCALE
        line["end"] = (
            line["start"][0] + scaled_length * math.cos(angle),
            line["start"][1] + scaled_length * math.sin(angle)
        )
        line["length"] = new_length
        self.canvas.coords(line["line"], *line["start"], *line["end"])
        self.update_label(line)
        self.redraw_canvas()

    def update_label(self, line):
        index = self.lines.index(line)
        start, end = line["start"], line["end"]
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        label_text = f"{line['length']:.2f} m"
        self.canvas.coords(self.labels[index][0], mid_x, mid_y - 10)
        self.canvas.itemconfig(self.labels[index][0], text=label_text)

    def calculate_length(self, start, end):
        dx = (end[0] - start[0]) / self.SCALE
        dy = (end[1] - start[1]) / self.SCALE
        return math.sqrt(dx ** 2 + dy ** 2)

    def calculate_angle(self, start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        return math.atan2(dy, dx)

    def draw_anchor_points(self, start, end):
        self.canvas.create_oval(start[0]-5, start[1]-5, start[0]+5, start[1]+5, fill="red")
        self.canvas.create_oval(end[0]-5, end[1]-5, end[0]+5, end[1]+5, fill="red")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.start_point = None
        self.lines.clear()
        self.labels.clear()
        self.current_y_offset = 0  # Reiniciar el desplazamiento vertical al limpiar el canvas

    def redraw_canvas(self):
        self.canvas.delete("all")
        for line in self.lines:
            self.canvas.create_line(*line["start"], *line["end"], fill="black", width=2)
            self.create_label(line["start"], line["end"], line["length"])
            self.draw_anchor_points(line["start"], line["end"])

    def enable_add_label_mode(self):
        # Activar el modo de agregar etiqueta
        self.adding_label_mode = True
        self.canvas.bind("<Button-1>", self.add_extra_label)
        print("Modo para agregar etiqueta adicional activado. Haga clic en el canvas para colocar la etiqueta.")

    def add_extra_label(self, event):
        # Obtener el texto de la etiqueta desde el campo de texto
        text = self.extra_label_var.get()
        if text:
            # Crear la etiqueta en la posición del click
            self.canvas.create_text(event.x, event.y, text=text, font=("Arial", 12), fill="blue")
            # Restaurar el binding original
            self.canvas.bind("<Button-1>", self.on_canvas_click)
            # Desactivar el modo de agregar etiqueta
            self.adding_label_mode = False
            print(f"Etiqueta '{text}' añadida en ({event.x}, {event.y}).")

    def export_to_svg(self):
        # Abrir un cuadro de diálogo para guardar el archivo
        file_path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG files", "*.svg")])
        if not file_path:
            return

        # Crear el contenido SVG
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n'
        for line in self.lines:
            start_x, start_y = line["start"]
            end_x, end_y = line["end"]
            svg_content += f'  <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" style="stroke:black;stroke-width:2" />\n'

        # Agregar etiquetas al SVG
        for label, index in self.labels:
            coords = self.canvas.coords(label)
            if coords:  # Asegurarse de que las coordenadas se obtienen correctamente
                x, y = coords
                text = self.canvas.itemcget(label, "text")
                svg_content += f'  <text x="{x}" y="{y}" font-family="Arial" font-size="12" fill="black">{text}</text>\n'

        # Exportar etiquetas adicionales
        for item in self.canvas.find_all():
            if self.canvas.type(item) == 'text' and item not in [l[0] for l in self.labels]:
                x, y = self.canvas.coords(item)
                text = self.canvas.itemcget(item, "text")
                svg_content += f'  <text x="{x}" y="{y}" font-family="Arial" font-size="12" fill="blue">{text}</text>\n'

        svg_content += '</svg>'

        # Escribir el contenido SVG en el archivo
        try:
            with open(file_path, "w") as svg_file:
                svg_file.write(svg_content)
            print(f"Archivo SVG guardado correctamente en {file_path}")
        except Exception as e:
            print(f"Error al guardar el archivo SVG: {e}")
    
    def _initialize_claude(self):
        """Inicializa el analizador de Claude cargando las variables de entorno."""
        try:
            # Cargar variables de entorno desde .env
            load_env_file('.env')
            
            # Intentar inicializar Claude
            self.claude_analyzer = ClaudeAnalyzer()
            print("✓ Claude Analyzer inicializado correctamente")
            
        except ValueError as e:
            print(f"⚠️ Claude no disponible: {e}")
            self.claude_analyzer = None
        except Exception as e:
            print(f"❌ Error al inicializar Claude: {e}")
            self.claude_analyzer = None
    
    def analyze_with_ai(self):
        """Ejecuta el análisis del plano con Claude AI."""
        # Verificar si hay líneas dibujadas
        if not self.lines:
            messagebox.showwarning(
                "Sin plano",
                "No hay ningún plano dibujado para analizar.\n\n"
                "Por favor, dibuja algunas líneas primero."
            )
            return
        
        # Verificar si Claude está disponible
        if self.claude_analyzer is None:
            messagebox.showerror(
                "Claude no disponible",
                "El analizador de IA no está configurado.\n\n"
                "Por favor, verifica que:\n"
                "1. El archivo .env existe\n"
                "2. CLAUDE_API_KEY está configurada con tu clave real\n"
                "3. El paquete 'anthropic' está instalado"
            )
            return
        
        # Mostrar ventana de "Analizando..."
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Analizando...")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(
            progress_window, 
            text="🤖 Analizando plano con IA...",
            font=("Arial", 12)
        ).pack(pady=20)
        
        progress_label = tk.Label(progress_window, text="Por favor espera...")
        progress_label.pack()
        
        # Actualizar la interfaz
        self.root.update()
        
        try:
            # Realizar análisis
            analysis = self.claude_analyzer.analyze_floor_plan(self.lines, self.SCALE)
            
            # Cerrar ventana de progreso
            progress_window.destroy()
            
            # Mostrar resultados
            self._show_analysis_results(analysis)
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror(
                "Error en el análisis",
                f"Ocurrió un error durante el análisis:\n\n{str(e)}"
            )
    
    def _show_analysis_results(self, analysis: dict):
        """
        Muestra los resultados del análisis en una ventana emergente.
        
        Args:
            analysis: Diccionario con los resultados del análisis
        """
        # Crear ventana de resultados
        results_window = tk.Toplevel(self.root)
        results_window.title("Reporte de Análisis - Claude AI")
        results_window.geometry("900x700")
        
        # Frame principal con scrollbar
        main_frame = tk.Frame(results_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Área de texto con scroll
        text_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Courier New", 10),
            bg="#f5f5f5"
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        
        # Formatear y mostrar el reporte
        report = self.claude_analyzer.format_report(analysis)
        text_area.insert(tk.END, report)
        text_area.config(state=tk.DISABLED)  # Solo lectura
        
        # Botones de acción
        button_frame = tk.Frame(results_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Botón para copiar al portapapeles
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(report)
            messagebox.showinfo("Copiado", "Reporte copiado al portapapeles")
        
        # Botón para guardar como archivo
        def save_report():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report)
                    messagebox.showinfo("Guardado", f"Reporte guardado en:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar: {e}")
        
        tk.Button(
            button_frame,
            text="📋 Copiar al Portapapeles",
            command=copy_to_clipboard
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="💾 Guardar Reporte",
            command=save_report
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cerrar",
            command=results_window.destroy
        ).pack(side=tk.RIGHT, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
