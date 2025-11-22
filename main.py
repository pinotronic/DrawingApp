import tkinter as tk
from tkinter.simpledialog import askfloat, askstring
from tkinter import scrolledtext, messagebox, ttk
import math
from tkinter import filedialog
from claude_analyzer import ClaudeAnalyzer, load_env_file
from zone_manager import ZoneManager

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawing App - Planos para Avalúos")

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
        
        # Constantes para acotación profesional
        self.DIMENSION_OFFSET = 30  # Separación de la línea de cota respecto a la línea principal
        self.EXTENSION_GAP = 5  # Espacio entre línea y línea de extensión
        self.EXTENSION_OVERSHOOT = 8  # Cuánto sobresalen las líneas de extensión
        self.ARROW_SIZE = 8  # Tamaño de las flechas
        
        # Variables para gestión de zonas
        self.zone_manager = ZoneManager(scale=self.SCALE)
        self.zone_selection_mode = False  # Modo para seleccionar líneas para zonas
        self.selected_lines_for_zone = []  # Líneas seleccionadas para crear una zona
        self.zone_canvas_items = {}  # Items del canvas asociados a zonas (polígonos y etiquetas)
        
        # Variables para orientación y rotación
        self.rotation_angle = 0  # Ángulo de rotación del plano en grados
        self.compass_size = 60  # Tamaño de la rosa de los vientos
        self._last_slider_value = 0  # Rastrear posición previa del slider
        
        # Inicializar Claude Analyzer (con manejo de errores)
        self.claude_analyzer = None
        self._initialize_claude()

        # Configurar la UI primero
        self.setup_ui()

        # Binding de eventos del canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.move_point)
        self.canvas.bind("<ButtonRelease-1>", self.release_point)
        self.canvas.bind("<Button-3>", self.on_label_right_click)

    def setup_ui(self):
        # Barra de herramientas IZQUIERDA
        toolbar = tk.Frame(self.root, bg="#f0f0f0", width=200)
        toolbar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Título de la barra
        title_label = tk.Label(
            toolbar,
            text="🛠️ Herramientas",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=10)
        
        # Separador
        tk.Frame(toolbar, height=2, bg="#ccc").pack(fill=tk.X, padx=10, pady=5)

        # SECCIÓN: DIBUJO
        tk.Label(
            toolbar,
            text="📏 Dibujo",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(pady=(10, 5))

        # Caja de texto para la longitud de la línea
        tk.Label(toolbar, text="Longitud (m):", bg="#f0f0f0", font=("Arial", 9)).pack()
        self.length_var = tk.DoubleVar()
        length_entry = tk.Entry(toolbar, textvariable=self.length_var, width=15)
        length_entry.pack(pady=5)

        # Botón para dibujar la línea
        draw_button = tk.Button(
            toolbar, 
            text="Dibujar Línea", 
            command=self.draw_line,
            width=18
        )
        draw_button.pack(pady=2)

        # Botón para establecer punto de inicio
        set_start_button = tk.Button(
            toolbar, 
            text="Punto de Inicio", 
            command=self.set_start_point,
            width=18
        )
        set_start_button.pack(pady=2)

        # Botón para activar/desactivar modo de movimiento fijo
        self.fixed_movement_button = tk.Button(
            toolbar, 
            text="Movimiento Fijo", 
            command=self.toggle_fixed_movement_mode,
            width=18
        )
        self.fixed_movement_button.pack(pady=2)

        # Separador
        tk.Frame(toolbar, height=2, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # SECCIÓN: ETIQUETAS
        tk.Label(
            toolbar,
            text="🏷️ Etiquetas",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(pady=(5, 5))

        # Campo de texto para la etiqueta adicional
        tk.Label(toolbar, text="Texto:", bg="#f0f0f0", font=("Arial", 9)).pack()
        self.extra_label_var = tk.StringVar()
        extra_label_entry = tk.Entry(toolbar, textvariable=self.extra_label_var, width=15)
        extra_label_entry.pack(pady=5)

        # Botón para agregar la etiqueta adicional
        add_label_button = tk.Button(
            toolbar, 
            text="Agregar Etiqueta", 
            command=self.enable_add_label_mode,
            width=18
        )
        add_label_button.pack(pady=2)

        # Separador
        tk.Frame(toolbar, height=2, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # SECCIÓN: ZONAS
        tk.Label(
            toolbar,
            text="🏠 Zonas",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(pady=(5, 5))
        
        # Botón para crear zona
        self.create_zone_button = tk.Button(
            toolbar,
            text="➕ Crear Zona",
            command=self.start_zone_creation,
            bg="#2196F3",
            fg="white",
            font=("Arial", 9, "bold"),
            width=18
        )
        self.create_zone_button.pack(pady=2)
        
        # Botón para auto-detectar zonas
        self.auto_detect_button = tk.Button(
            toolbar,
            text="🔍 Auto-Detectar",
            command=self.auto_detect_zones,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 9, "bold"),
            width=18
        )
        self.auto_detect_button.pack(pady=2)
        
        # Botón para eliminar zona
        self.delete_zone_button = tk.Button(
            toolbar,
            text="🗑️ Eliminar Zona",
            command=self.delete_selected_zone,
            bg="#F44336",
            fg="white",
            font=("Arial", 9, "bold"),
            state=tk.DISABLED,
            width=18
        )
        self.delete_zone_button.pack(pady=2)

        # Separador
        tk.Frame(toolbar, height=2, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # SECCIÓN: ORIENTACIÓN CARDINAL
        tk.Label(
            toolbar,
            text="🧭 Orientación",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(pady=(5, 5))
        
        # Instrucción
        tk.Label(
            toolbar,
            text="Desliza para rotar:",
            bg="#f0f0f0",
            font=("Arial", 8),
            fg="#666"
        ).pack()
        
        # Frame para el slider
        slider_frame = tk.Frame(toolbar, bg="#f0f0f0")
        slider_frame.pack(pady=5, fill=tk.X, padx=10)
        
        # Label izquierda
        tk.Label(
            slider_frame,
            text="↶",
            bg="#f0f0f0",
            font=("Arial", 14),
            fg="#2196F3"
        ).pack(side=tk.LEFT)
        
        # Slider de rotación (-180 a +180)
        self.rotation_slider = tk.Scale(
            slider_frame,
            from_=-180,
            to=180,
            orient=tk.HORIZONTAL,
            length=120,
            showvalue=False,
            bg="#f0f0f0",
            highlightthickness=0,
            troughcolor="#ddd",
            command=self.on_slider_moved
        )
        self.rotation_slider.set(0)  # Iniciar en centro
        self.rotation_slider.pack(side=tk.LEFT, padx=5)
        
        # Binding para soltar el slider
        self.rotation_slider.bind("<ButtonRelease-1>", self.on_slider_released)
        
        # Label derecha
        tk.Label(
            slider_frame,
            text="↷",
            bg="#f0f0f0",
            font=("Arial", 14),
            fg="#2196F3"
        ).pack(side=tk.LEFT)
        
        # Label mostrando orientación actual
        self.orientation_label = tk.Label(
            toolbar,
            text="Rotación: 0°",
            bg="#f0f0f0",
            font=("Arial", 8),
            fg="#666"
        )
        self.orientation_label.pack(pady=2)
        
        # Botón para centrar el dibujo
        tk.Button(
            toolbar,
            text="🎯 Centrar Dibujo",
            command=self.center_drawing,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 9, "bold"),
            width=18
        ).pack(pady=5)

        # Separador
        tk.Frame(toolbar, height=2, bg="#ccc").pack(fill=tk.X, padx=10, pady=10)

        # SECCIÓN: ANÁLISIS Y EXPORTACIÓN
        tk.Label(
            toolbar,
            text="⚙️ Acciones",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0"
        ).pack(pady=(5, 5))
        
        # Botón para análisis con IA
        self.ai_button = tk.Button(
            toolbar, 
            text="🤖 Análisis IA", 
            command=self.analyze_with_ai,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 9, "bold"),
            width=18
        )
        self.ai_button.pack(pady=2)

        # Botón para exportar a SVG
        export_button = tk.Button(
            toolbar, 
            text="💾 Exportar SVG", 
            command=self.export_to_svg,
            width=18
        )
        export_button.pack(pady=2)

        # Botón para limpiar el canvas
        clear_button = tk.Button(
            toolbar, 
            text="🗑️ Limpiar Todo", 
            command=self.clear_canvas,
            bg="#FF5722",
            fg="white",
            width=18
        )
        clear_button.pack(pady=2)

        # Canvas en el centro
        self.canvas = tk.Canvas(self.root, width=1100, height=700, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel lateral derecho para lista de zonas
        self.create_zone_panel()

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
        # Prioridad 1: Modo de selección de zonas
        if self.zone_selection_mode:
            if self.on_canvas_click_zone_mode(event):
                return
        
        # Prioridad 2: Modo de agregar etiquetas
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
        """Crea acotación profesional con líneas de extensión y cota."""
        # Calcular el ángulo de la línea
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        line_angle = math.atan2(dy, dx)
        
        # Calcular el ángulo perpendicular (90° a la línea)
        perp_angle = line_angle + math.pi / 2
        
        # Determinar el lado de la acotación (arriba/abajo o izq/der)
        # Usar un offset adaptativo para que siempre quede visible
        offset_x = math.cos(perp_angle) * self.DIMENSION_OFFSET
        offset_y = math.sin(perp_angle) * self.DIMENSION_OFFSET
        
        # Punto medio de la línea principal
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # --- LÍNEAS DE EXTENSIÓN ---
        # Calcular puntos para líneas de extensión desde los extremos
        gap_x = math.cos(perp_angle) * self.EXTENSION_GAP
        gap_y = math.sin(perp_angle) * self.EXTENSION_GAP
        overshoot_x = math.cos(perp_angle) * (self.DIMENSION_OFFSET + self.EXTENSION_OVERSHOOT)
        overshoot_y = math.sin(perp_angle) * (self.DIMENSION_OFFSET + self.EXTENSION_OVERSHOOT)
        
        # Línea de extensión 1 (desde start)
        ext1_start_x = start[0] + gap_x
        ext1_start_y = start[1] + gap_y
        ext1_end_x = start[0] + overshoot_x
        ext1_end_y = start[1] + overshoot_y
        
        # Línea de extensión 2 (desde end)
        ext2_start_x = end[0] + gap_x
        ext2_start_y = end[1] + gap_y
        ext2_end_x = end[0] + overshoot_x
        ext2_end_y = end[1] + overshoot_y
        
        # Dibujar líneas de extensión (líneas finas, gris)
        ext_line_1 = self.canvas.create_line(
            ext1_start_x, ext1_start_y, ext1_end_x, ext1_end_y,
            fill="#666", width=1, tags="dimension"
        )
        ext_line_2 = self.canvas.create_line(
            ext2_start_x, ext2_start_y, ext2_end_x, ext2_end_y,
            fill="#666", width=1, tags="dimension"
        )
        
        # --- LÍNEA DE COTA ---
        # Puntos de inicio y fin de la línea de cota
        dim_start_x = start[0] + offset_x
        dim_start_y = start[1] + offset_y
        dim_end_x = end[0] + offset_x
        dim_end_y = end[1] + offset_y
        
        # Dibujar línea de cota
        dim_line = self.canvas.create_line(
            dim_start_x, dim_start_y, dim_end_x, dim_end_y,
            fill="#333", width=1, tags="dimension"
        )
        
        # --- FLECHAS EN LOS EXTREMOS ---
        # Calcular puntos para las flechas
        arrow1 = self._create_arrow_head(dim_start_x, dim_start_y, line_angle + math.pi)
        arrow2 = self._create_arrow_head(dim_end_x, dim_end_y, line_angle)
        
        # --- TEXTO DE DIMENSIÓN ---
        # Colocar texto en el centro de la línea de cota
        text_x = (dim_start_x + dim_end_x) / 2
        text_y = (dim_start_y + dim_end_y) / 2
        
        # Calcular ángulo del texto para que siempre sea legible
        text_angle_deg = math.degrees(line_angle)
        # Normalizar el ángulo para que el texto no aparezca al revés
        if text_angle_deg > 90 or text_angle_deg < -90:
            text_angle_deg += 180
        
        # Crear texto con fondo blanco para mejor legibilidad
        label_bg = self.canvas.create_rectangle(
            text_x - 25, text_y - 10, text_x + 25, text_y + 10,
            fill="white", outline="", tags="dimension"
        )
        
        label = self.canvas.create_text(
            text_x, text_y,
            text=f"{length:.2f} m",
            font=("Arial", 10),
            fill="#000",
            tags="dimension"
        )
        
        # Añadir evento de doble clic para editar
        self.canvas.tag_bind(label, "<Double-1>", 
                           lambda event, idx=len(self.lines) - 1: self.on_label_double_click(idx))
        
        # Guardar referencias de todos los elementos de la acotación
        self.labels.append({
            'text': label,
            'bg': label_bg,
            'dim_line': dim_line,
            'ext_lines': [ext_line_1, ext_line_2],
            'arrows': arrow1 + arrow2,
            'index': len(self.lines) - 1
        })
    
    def _create_arrow_head(self, x, y, angle):
        """Crea una flecha en el punto especificado con el ángulo dado."""
        # Calcular los tres puntos del triángulo de la flecha
        tip_x = x
        tip_y = y
        
        # Base de la flecha
        base_angle1 = angle + math.radians(150)
        base_angle2 = angle + math.radians(-150)
        
        base1_x = tip_x + self.ARROW_SIZE * math.cos(base_angle1)
        base1_y = tip_y + self.ARROW_SIZE * math.sin(base_angle1)
        base2_x = tip_x + self.ARROW_SIZE * math.cos(base_angle2)
        base2_y = tip_y + self.ARROW_SIZE * math.sin(base_angle2)
        
        # Crear polígono de flecha
        arrow = self.canvas.create_polygon(
            tip_x, tip_y, base1_x, base1_y, base2_x, base2_y,
            fill="#333", outline="#333", tags="dimension"
        )
        
        return [arrow]

    def on_label_right_click(self, event):
        clicked_label = None
        for label_data in self.labels:
            label = label_data['text']
            index = label_data['index']
            coords = self.canvas.coords(label)
            if coords:
                x, y = coords
                if abs(event.x - x) < 30 and abs(event.y - y) < 15:
                    clicked_label = index
                    break

        if clicked_label is not None:
            new_length = askfloat("Editar Longitud", "Introduce la nueva longitud (en metros):")
            if new_length is not None:
                self.update_line_length(clicked_label, new_length)

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
        """Actualiza la acotación cuando cambia una línea."""
        # Simplemente redibujar todo es más fácil con el nuevo sistema
        # ya que la acotación es compleja
        self.redraw_canvas()

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
        
        # Redibujar zonas primero (para que queden detrás)
        for zone in self.zone_manager.get_all_zones():
            self.visualize_zone(zone)
        
        # Redibujar líneas
        for i, line in enumerate(self.lines):
            # Color especial para líneas seleccionadas en modo zona
            if self.zone_selection_mode and i in self.selected_lines_for_zone:
                color = "#FF5722"  # Naranja para líneas seleccionadas
                width = 4
            else:
                color = "black"
                width = 2
            
            self.canvas.create_line(*line["start"], *line["end"], fill=color, width=width)
            self.create_label(line["start"], line["end"], line["length"])
            self.draw_anchor_points(line["start"], line["end"])
        
        # Dibujar rosa de los vientos (siempre al final, encima de todo)
        self.draw_compass()

    def draw_compass(self):
        """Dibuja la rosa de los vientos estática en la esquina superior derecha."""
        canvas_width = self.canvas.winfo_width()
        
        # Posición en esquina superior derecha
        cx = canvas_width - self.compass_size - 20
        cy = self.compass_size + 20
        
        # Círculo de fondo
        self.canvas.create_oval(
            cx - self.compass_size//2, cy - self.compass_size//2,
            cx + self.compass_size//2, cy + self.compass_size//2,
            fill="white", outline="#333", width=2
        )
        
        # Líneas de los puntos cardinales
        radius = self.compass_size // 2 - 10
        
        # Norte (arriba) - Rojo
        self.canvas.create_line(
            cx, cy, cx, cy - radius,
            fill="red", width=3, arrow=tk.LAST
        )
        self.canvas.create_text(
            cx, cy - radius - 12,
            text="N", font=("Arial", 12, "bold"), fill="red"
        )
        
        # Sur (abajo)
        self.canvas.create_line(
            cx, cy, cx, cy + radius,
            fill="#666", width=2
        )
        self.canvas.create_text(
            cx, cy + radius + 12,
            text="S", font=("Arial", 10), fill="#666"
        )
        
        # Este (derecha)
        self.canvas.create_line(
            cx, cy, cx + radius, cy,
            fill="#666", width=2
        )
        self.canvas.create_text(
            cx + radius + 12, cy,
            text="E", font=("Arial", 10), fill="#666"
        )
        
        # Oeste (izquierda)
        self.canvas.create_line(
            cx, cy, cx - radius, cy,
            fill="#666", width=2
        )
        self.canvas.create_text(
            cx - radius - 12, cy,
            text="O", font=("Arial", 10), fill="#666"
        )
    
    def rotate_drawing(self, angle_increment):
        """Rota el dibujo completo por un incremento de ángulo."""
        if not self.lines:
            messagebox.showinfo(
                "Sin dibujo",
                "No hay ningún dibujo para rotar."
            )
            return
        
        # Actualizar ángulo de rotación
        self.rotation_angle = (self.rotation_angle + angle_increment) % 360
        
        # Obtener centro del canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Convertir ángulo a radianes
        angle_rad = math.radians(angle_increment)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Rotar todas las líneas
        for line in self.lines:
            # Rotar punto de inicio
            start_x, start_y = line["start"]
            rel_x = start_x - center_x
            rel_y = start_y - center_y
            new_x = rel_x * cos_angle - rel_y * sin_angle + center_x
            new_y = rel_x * sin_angle + rel_y * cos_angle + center_y
            line["start"] = (new_x, new_y)
            
            # Rotar punto final
            end_x, end_y = line["end"]
            rel_x = end_x - center_x
            rel_y = end_y - center_y
            new_x = rel_x * cos_angle - rel_y * sin_angle + center_x
            new_y = rel_x * sin_angle + rel_y * cos_angle + center_y
            line["end"] = (new_x, new_y)
        
        # Actualizar label de orientación
        self.orientation_label.config(text=f"Rotación: {self.rotation_angle}°")
        
        # Redibujar
        self.redraw_canvas()
        
        print(f"Plano rotado {angle_increment}°. Orientación actual: {self.rotation_angle}°")
    
    def on_slider_moved(self, value):
        """Se llama mientras se arrastra el slider."""
        slider_value = int(float(value))
        
        # Solo rotar si hay líneas
        if self.lines:
            # Calcular incremento desde la última posición
            angle_increment = slider_value - getattr(self, '_last_slider_value', 0)
            
            if angle_increment != 0:
                # Obtener centro del canvas
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                center_x = canvas_width / 2
                center_y = canvas_height / 2
                
                # Convertir ángulo a radianes
                angle_rad = math.radians(angle_increment)
                cos_angle = math.cos(angle_rad)
                sin_angle = math.sin(angle_rad)
                
                # Rotar todas las líneas
                for line in self.lines:
                    # Rotar punto de inicio
                    start_x, start_y = line["start"]
                    rel_x = start_x - center_x
                    rel_y = start_y - center_y
                    new_x = rel_x * cos_angle - rel_y * sin_angle + center_x
                    new_y = rel_x * sin_angle + rel_y * cos_angle + center_y
                    line["start"] = (new_x, new_y)
                    
                    # Rotar punto final
                    end_x, end_y = line["end"]
                    rel_x = end_x - center_x
                    rel_y = end_y - center_y
                    new_x = rel_x * cos_angle - rel_y * sin_angle + center_x
                    new_y = rel_x * sin_angle + rel_y * cos_angle + center_y
                    line["end"] = (new_x, new_y)
                
                # Actualizar ángulo de rotación total
                self.rotation_angle = (self.rotation_angle + angle_increment) % 360
                
                # Actualizar label de orientación
                self.orientation_label.config(text=f"Rotación: {self.rotation_angle}°")
                
                # Redibujar
                self.redraw_canvas()
            
            # Guardar valor actual
            self._last_slider_value = slider_value
    
    def on_slider_released(self, event):
        """Se llama al soltar el slider - vuelve al centro."""
        # Resetear el slider al centro
        self.rotation_slider.set(0)
        self._last_slider_value = 0
        
        print(f"Rotación aplicada. Orientación final: {self.rotation_angle}°")
    
    def center_drawing(self):
        """Centra todo el dibujo en el canvas."""
        if not self.lines:
            messagebox.showinfo(
                "Sin dibujo",
                "No hay ningún dibujo para centrar."
            )
            return
        
        # Calcular el bounding box de todas las líneas
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for line in self.lines:
            # Verificar punto de inicio
            start_x, start_y = line["start"]
            min_x = min(min_x, start_x)
            min_y = min(min_y, start_y)
            max_x = max(max_x, start_x)
            max_y = max(max_y, start_y)
            
            # Verificar punto final
            end_x, end_y = line["end"]
            min_x = min(min_x, end_x)
            min_y = min(min_y, end_y)
            max_x = max(max_x, end_x)
            max_y = max(max_y, end_y)
        
        # Calcular centro del dibujo actual
        drawing_center_x = (min_x + max_x) / 2
        drawing_center_y = (min_y + max_y) / 2
        
        # Calcular centro del canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2
        
        # Calcular desplazamiento necesario
        offset_x = canvas_center_x - drawing_center_x
        offset_y = canvas_center_y - drawing_center_y
        
        # Aplicar desplazamiento a todas las líneas
        for line in self.lines:
            start_x, start_y = line["start"]
            line["start"] = (start_x + offset_x, start_y + offset_y)
            
            end_x, end_y = line["end"]
            line["end"] = (end_x + offset_x, end_y + offset_y)
        
        # Redibujar
        self.redraw_canvas()
        
        print(f"Dibujo centrado. Desplazamiento: ({offset_x:.1f}, {offset_y:.1f})")
        messagebox.showinfo(
            "Dibujo Centrado",
            f"✅ El dibujo se ha centrado en el canvas.\n\n"
            f"Dimensiones: {max_x - min_x:.1f} × {max_y - min_y:.1f} px\n"
            f"Ahora puedes rotar con mejores resultados."
        )
    
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

        # Obtener dimensiones del canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Crear el contenido SVG con dimensiones
        svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{canvas_width}" height="{canvas_height}">\n'
        
        # Exportar zonas primero (para que queden detrás de las líneas)
        for zone in self.zone_manager.get_all_zones():
            # Obtener puntos del polígono
            polygon_points = []
            for line_idx in zone.line_indices:
                if line_idx < len(self.lines):
                    line_data = self.lines[line_idx]
                    if not polygon_points:
                        polygon_points.append(f"{line_data['start'][0]},{line_data['start'][1]}")
                    polygon_points.append(f"{line_data['end'][0]},{line_data['end'][1]}")
            
            if len(polygon_points) >= 3:
                points_str = " ".join(polygon_points)
                # Crear polígono con color semitransparente
                svg_content += f'  <polygon points="{points_str}" '
                svg_content += f'fill="{zone.color}" fill-opacity="0.3" '
                svg_content += f'stroke="{zone.color}" stroke-width="2" />\n'
                
                # Agregar etiqueta de la zona
                centroid = self.zone_manager.get_zone_centroid(zone.id, self.lines)
                if centroid:
                    zone_label = self.zone_manager.get_zone_label(zone)
                    # Separar el label en líneas para SVG
                    label_lines = zone_label.split('\n')
                    for i, label_line in enumerate(label_lines):
                        svg_content += f'  <text x="{centroid[0]}" y="{centroid[1] + i * 15}" '
                        svg_content += f'font-family="Arial" font-size="11" font-weight="bold" '
                        svg_content += f'fill="#333" text-anchor="middle">{label_line}</text>\n'
        
        # Exportar líneas
        for line in self.lines:
            start_x, start_y = line["start"]
            end_x, end_y = line["end"]
            svg_content += f'  <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" '
            svg_content += f'style="stroke:black;stroke-width:2" />\n'

        # Agregar etiquetas de dimensiones al SVG
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

        # Exportar rosa de los vientos
        cx = canvas_width - self.compass_size - 20
        cy = self.compass_size + 20
        radius = self.compass_size // 2 - 10
        
        # Círculo de fondo
        svg_content += f'  <circle cx="{cx}" cy="{cy}" r="{self.compass_size//2}" '
        svg_content += f'fill="white" stroke="#333" stroke-width="2" />\n'
        
        # Línea Norte (roja)
        svg_content += f'  <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - radius}" '
        svg_content += f'stroke="red" stroke-width="3" marker-end="url(#arrowRed)" />\n'
        svg_content += f'  <text x="{cx}" y="{cy - radius - 12}" '
        svg_content += f'font-family="Arial" font-size="12" font-weight="bold" '
        svg_content += f'fill="red" text-anchor="middle">N</text>\n'
        
        # Línea Sur
        svg_content += f'  <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy + radius}" '
        svg_content += f'stroke="#666" stroke-width="2" />\n'
        svg_content += f'  <text x="{cx}" y="{cy + radius + 12}" '
        svg_content += f'font-family="Arial" font-size="10" fill="#666" text-anchor="middle">S</text>\n'
        
        # Línea Este
        svg_content += f'  <line x1="{cx}" y1="{cy}" x2="{cx + radius}" y2="{cy}" '
        svg_content += f'stroke="#666" stroke-width="2" />\n'
        svg_content += f'  <text x="{cx + radius + 12}" y="{cy}" '
        svg_content += f'font-family="Arial" font-size="10" fill="#666" '
        svg_content += f'alignment-baseline="middle">E</text>\n'
        
        # Línea Oeste
        svg_content += f'  <line x1="{cx}" y1="{cy}" x2="{cx - radius}" y2="{cy}" '
        svg_content += f'stroke="#666" stroke-width="2" />\n'
        svg_content += f'  <text x="{cx - radius - 12}" y="{cy}" '
        svg_content += f'font-family="Arial" font-size="10" fill="#666" '
        svg_content += f'text-anchor="end" alignment-baseline="middle">O</text>\n'
        
        # Etiqueta de orientación si hay rotación
        if self.rotation_angle != 0:
            svg_content += f'  <text x="{cx}" y="{cy + self.compass_size//2 + 25}" '
            svg_content += f'font-family="Arial" font-size="9" fill="#666" '
            svg_content += f'text-anchor="middle">Rotación: {self.rotation_angle}°</text>\n'

        svg_content += '</svg>'

        # Escribir el contenido SVG en el archivo
        try:
            with open(file_path, "w", encoding="utf-8") as svg_file:
                svg_file.write(svg_content)
            
            messagebox.showinfo(
                "Exportación Exitosa",
                f"✅ Archivo SVG guardado en:\n{file_path}\n\n"
                f"Zonas exportadas: {len(self.zone_manager.get_all_zones())}\n"
                f"Orientación: {self.rotation_angle}°"
            )
            print(f"Archivo SVG guardado correctamente en {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el archivo SVG:\n{e}")
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
            # Obtener zonas en formato para Claude
            zones_data = None
            if self.zone_manager.get_all_zones():
                zones_data = self.zone_manager.export_zones_data()
            
            # Realizar análisis
            analysis = self.claude_analyzer.analyze_floor_plan(
                self.lines, 
                self.SCALE,
                zones_data
            )
            
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
    
    # ============================================================================
    # MÉTODOS PARA GESTIÓN DE ZONAS
    # ============================================================================
    
    def create_zone_panel(self):
        """Crea el panel lateral para gestionar zonas."""
        # Frame lateral derecho
        self.zone_panel = tk.Frame(self.root, width=250, bg="#f0f0f0")
        self.zone_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Título del panel
        title_label = tk.Label(
            self.zone_panel,
            text="📐 Zonas/Habitaciones",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=10)
        
        # Lista de zonas con scrollbar
        list_frame = tk.Frame(self.zone_panel, bg="#f0f0f0")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.zone_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            selectmode=tk.SINGLE
        )
        self.zone_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.zone_listbox.yview)
        
        # Binding para selección de zona
        self.zone_listbox.bind("<<ListboxSelect>>", self.on_zone_select)
        
        # Label de resumen
        self.zone_summary_label = tk.Label(
            self.zone_panel,
            text="Total: 0 zonas | 0.00 m²",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        self.zone_summary_label.pack(pady=5)
    
    def start_zone_creation(self):
        """Inicia el modo de creación de zona."""
        if self.zone_selection_mode:
            # Confirmar y crear zona
            self.confirm_zone_creation()
        else:
            # Iniciar selección
            self.zone_selection_mode = True
            self.selected_lines_for_zone = []
            self.create_zone_button.config(text="✅ Confirmar (0 líneas)", bg="#FF9800")
            messagebox.showinfo(
                "Crear Zona",
                "Modo de selección activado:\n\n"
                "• Haz clic CERCA de las líneas para seleccionarlas\n"
                "• Las líneas seleccionadas se mostrarán en NARANJA\n"
                "• Necesitas mínimo 3 líneas\n"
                "• Clic en una línea naranja para deseleccionarla\n\n"
                "Cuando termines, presiona el botón de confirmar."
            )
    
    def on_canvas_click_zone_mode(self, event):
        """Maneja clics durante el modo de selección de zonas."""
        if not self.zone_selection_mode:
            return False
        
        # Buscar línea cercana al clic (búsqueda mejorada)
        closest_line = None
        min_distance = float('inf')
        tolerance = 20  # Aumentado para facilitar selección
        
        for i, line_data in enumerate(self.lines):
            # Usar las coordenadas directamente del dict line_data
            x1, y1 = line_data["start"]
            x2, y2 = line_data["end"]
            
            # Calcular distancia del punto a la línea
            distance = self._distance_point_to_line(event.x, event.y, x1, y1, x2, y2)
            
            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                closest_line = i
        
        # Si encontramos una línea cercana, seleccionarla/deseleccionarla
        if closest_line is not None:
            if closest_line in self.selected_lines_for_zone:
                # Deseleccionar
                self.selected_lines_for_zone.remove(closest_line)
                print(f"Línea {closest_line} deseleccionada. Total: {len(self.selected_lines_for_zone)}")
            else:
                # Seleccionar
                self.selected_lines_for_zone.append(closest_line)
                print(f"Línea {closest_line} seleccionada. Total: {len(self.selected_lines_for_zone)}")
            
            # Actualizar texto del botón con contador
            self.create_zone_button.config(
                text=f"✅ Confirmar ({len(self.selected_lines_for_zone)} líneas)"
            )
            
            self.redraw_canvas()
            return True
        
        return False
    
    def _distance_point_to_line(self, px, py, x1, y1, x2, y2):
        """Calcula la distancia mínima de un punto a un segmento de línea."""
        # Longitud del segmento al cuadrado
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_length_sq == 0:
            # La línea es un punto
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        
        # Parámetro t del punto más cercano en la línea
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
        
        # Punto más cercano en el segmento
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        
        # Distancia del punto al punto más cercano
        distance = math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)
        
        return distance
    
    def confirm_zone_creation(self):
        """Confirma la creación de una zona con las líneas seleccionadas."""
        if len(self.selected_lines_for_zone) < 3:
            messagebox.showwarning(
                "Zona Incompleta",
                "Debes seleccionar al menos 3 líneas para formar una zona."
            )
            return
        
        # Diálogo para nombrar la zona
        zone_dialog = ZoneDialog(self.root, self.zone_manager.ZONE_TYPES)
        self.root.wait_window(zone_dialog.dialog)
        
        if zone_dialog.result:
            zone_name = zone_dialog.result['name']
            zone_type = zone_dialog.result['type']
            
            # Crear la zona
            zone = self.zone_manager.create_zone(
                zone_name,
                zone_type,
                self.selected_lines_for_zone.copy(),
                self.lines
            )
            
            if zone:
                if zone.is_valid:
                    messagebox.showinfo(
                        "Zona Creada",
                        f"✅ Zona '{zone_name}' creada exitosamente\n"
                        f"Área: {zone.area:.2f} m²"
                    )
                else:
                    messagebox.showwarning(
                        "Zona con Advertencia",
                        f"⚠️ Zona '{zone_name}' creada pero no forma un polígono cerrado.\n"
                        f"Es posible que el cálculo de área no sea preciso."
                    )
                
                # Visualizar la zona
                self.visualize_zone(zone)
                self.update_zone_list()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo crear la zona. Verifica las líneas seleccionadas."
                )
        
        # Salir del modo de selección
        self.zone_selection_mode = False
        self.selected_lines_for_zone = []
        self.create_zone_button.config(text="➕ Crear Zona", bg="#2196F3")
        self.redraw_canvas()
    
    def auto_detect_zones(self):
        """Detecta automáticamente zonas cerradas en el plano."""
        if len(self.lines) < 3:
            messagebox.showwarning(
                "Plano Incompleto",
                "Necesitas al menos 3 líneas para detectar zonas."
            )
            return
        
        detected_zones = self.zone_manager.auto_detect_zones(self.lines)
        
        if detected_zones:
            messagebox.showinfo(
                "Zonas Detectadas",
                f"✅ Se detectaron {len(detected_zones)} zona(s) automáticamente."
            )
            
            # Visualizar todas las zonas detectadas
            for zone in detected_zones:
                self.visualize_zone(zone)
            
            self.update_zone_list()
        else:
            messagebox.showinfo(
                "Sin Zonas",
                "No se detectaron zonas cerradas automáticamente.\n"
                "Puedes crear zonas manualmente con 'Crear Zona'."
            )
    
    def visualize_zone(self, zone):
        """Visualiza una zona en el canvas."""
        # Obtener las coordenadas del polígono
        polygon_points = []
        for line_idx in zone.line_indices:
            if line_idx < len(self.lines):
                line_data = self.lines[line_idx]
                if not polygon_points:
                    polygon_points.extend(line_data["start"])
                polygon_points.extend(line_data["end"])
        
        if len(polygon_points) >= 6:  # Al menos 3 puntos (6 coordenadas)
            # Crear polígono con relleno semitransparente
            polygon = self.canvas.create_polygon(
                polygon_points,
                fill=zone.color,
                stipple="gray50",  # Patrón semitransparente
                outline=zone.color,
                width=2,
                tags=f"zone_{zone.id}"
            )
            
            # Bajar el polígono para que no tape las líneas
            self.canvas.tag_lower(polygon)
            
            # Obtener centroide para la etiqueta
            centroid = self.zone_manager.get_zone_centroid(zone.id, self.lines)
            
            if centroid:
                label_text = self.zone_manager.get_zone_label(zone)
                label = self.canvas.create_text(
                    centroid[0],
                    centroid[1],
                    text=label_text,
                    font=("Arial", 11, "bold"),
                    fill="#333",
                    tags=f"zone_{zone.id}"
                )
                
                # Guardar referencias
                self.zone_canvas_items[zone.id] = {
                    'polygon': polygon,
                    'label': label
                }
    
    def update_zone_list(self):
        """Actualiza la lista de zonas en el panel lateral."""
        self.zone_listbox.delete(0, tk.END)
        
        zones = self.zone_manager.get_all_zones()
        total_area = 0.0
        
        for zone in zones:
            status_icon = "✅" if zone.is_valid else "⚠️"
            type_icon = self.zone_manager.ZONE_TYPES.get(zone.zone_type, {}).get('icon', '📐')
            display_text = f"{status_icon} {type_icon} {zone.name} - {zone.area:.2f} m²"
            
            self.zone_listbox.insert(tk.END, display_text)
            total_area += zone.area
        
        # Actualizar resumen
        self.zone_summary_label.config(
            text=f"Total: {len(zones)} zonas | {total_area:.2f} m²"
        )
    
    def on_zone_select(self, event):
        """Maneja la selección de una zona en la lista."""
        selection = self.zone_listbox.curselection()
        
        if selection:
            self.delete_zone_button.config(state=tk.NORMAL)
        else:
            self.delete_zone_button.config(state=tk.DISABLED)
    
    def delete_selected_zone(self):
        """Elimina la zona seleccionada."""
        selection = self.zone_listbox.curselection()
        
        if not selection:
            return
        
        zone_index = selection[0]
        zones = self.zone_manager.get_all_zones()
        
        if zone_index < len(zones):
            zone = zones[zone_index]
            
            # Confirmar eliminación
            confirm = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Eliminar la zona '{zone.name}'?"
            )
            
            if confirm:
                # Eliminar del canvas
                if zone.id in self.zone_canvas_items:
                    items = self.zone_canvas_items[zone.id]
                    self.canvas.delete(items['polygon'])
                    self.canvas.delete(items['label'])
                    del self.zone_canvas_items[zone.id]
                
                # Eliminar del gestor
                self.zone_manager.delete_zone(zone.id)
                
                # Actualizar lista
                self.update_zone_list()
                self.delete_zone_button.config(state=tk.DISABLED)


class ZoneDialog:
    """Diálogo para crear/editar zonas."""
    
    def __init__(self, parent, zone_types):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Crear Zona")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        # Centrar diálogo
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Nombre de la zona
        tk.Label(
            self.dialog,
            text="Nombre de la zona:",
            font=("Arial", 10, "bold")
        ).pack(pady=(20, 5))
        
        self.name_entry = tk.Entry(self.dialog, font=("Arial", 11), width=30)
        self.name_entry.pack(pady=5)
        self.name_entry.focus()
        
        # Tipo de zona
        tk.Label(
            self.dialog,
            text="Tipo de zona:",
            font=("Arial", 10, "bold")
        ).pack(pady=(15, 5))
        
        # Frame para tipos de zona con scroll
        types_frame = tk.Frame(self.dialog)
        types_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Canvas con scrollbar para tipos
        canvas = tk.Canvas(types_frame, height=120)
        scrollbar = tk.Scrollbar(types_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Variable para tipo seleccionado
        self.zone_type_var = tk.StringVar(value="sala")
        
        # Botones de radio para cada tipo
        for zone_type, info in zone_types.items():
            icon = info.get('icon', '📐')
            text = f"{icon} {zone_type.capitalize()}"
            
            tk.Radiobutton(
                scrollable_frame,
                text=text,
                variable=self.zone_type_var,
                value=zone_type,
                font=("Arial", 10)
            ).pack(anchor="w", padx=10, pady=2)
        
        # Botones
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=15)
        
        tk.Button(
            button_frame,
            text="✅ Crear",
            command=self.on_ok,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="❌ Cancelar",
            command=self.on_cancel,
            font=("Arial", 10),
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Binding para Enter
        self.dialog.bind("<Return>", lambda e: self.on_ok())
    
    def on_ok(self):
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning(
                "Nombre Requerido",
                "Debes ingresar un nombre para la zona."
            )
            return
        
        self.result = {
            'name': name,
            'type': self.zone_type_var.get()
        }
        self.dialog.destroy()
    
    def on_cancel(self):
        self.result = None
        self.dialog.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()
