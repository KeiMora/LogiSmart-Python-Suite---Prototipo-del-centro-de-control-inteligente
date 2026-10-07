"""
Interfaz gráfica principal del sistema LogiSmart.
Implementa todas las funcionalidades requeridas en una GUI con tkinter.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from data.mongodb_repository import MongoDBRepository
from bson import ObjectId
from logic.motor_reglas import MotorReglas
from logic.clasificador_hibrido import ClasificadorHibrido
from logic.asistente_llm import AsistenteLLM
from logic.matriz_riesgos import MatrizRiesgos
from config.settings import config


class LogiSmartGUI:
    """Interfaz gráfica principal del sistema LogiSmart."""

    def __init__(self, root):
        """Inicializa la interfaz gráfica."""
        self.root = root
        self.root.title("LogiSmart - Sistema de Control Logístico Inteligente")
        self.root.geometry("1200x800")

        # Inicializar componentes
        self.mongo_repo = None
        self.motor_reglas = MotorReglas()
        self.clasificador = ClasificadorHibrido(config.ollama.model)
        self.asistente = None  # Se inicializa cuando se conecte a MongoDB
        self.matriz_riesgos = MatrizRiesgos("LogiSmart")

        # NO cargar riesgos predefinidos - se cargarán de MongoDB si están disponibles

        # Configurar estilo
        self._configurar_estilo()

        # Crear interfaz
        self._crear_interfaz()

        # Actualizar estado inicial del asistente
        self.root.after(100, self._actualizar_estado_asistente_inicial)

        # Estado de conexión
        self.conectado_mongodb = False

    def _configurar_estilo(self):
        """Configura el estilo de la interfaz."""
        style = ttk.Style()
        style.theme_use('clam')

        # Colores personalizados
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', padding=[10, 5], font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10), padding=5)
        style.configure('TLabel', font=('Arial', 10), background='#f0f0f0')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), background='#2c3e50', foreground='white')

    def _crear_interfaz(self):
        """Crea todos los componentes de la interfaz."""
        # Encabezado
        self._crear_encabezado()

        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear pestañas
        self._crear_pestana_panel_control()
        self._crear_pestana_control_acceso()
        self._crear_pestana_gestion_camiones()
        self._crear_pestana_simulador_reglas()
        self._crear_pestana_incidentes()
        self._crear_pestana_asistente()
        self._crear_pestana_riesgos()
        self._crear_pestana_configuracion()

        # Barra de estado
        self._crear_barra_estado()

    def _crear_encabezado(self):
        """Crea el encabezado de la aplicación."""
        encabezado = tk.Frame(self.root, bg="#2c3e50", height=60)
        encabezado.pack(fill=tk.X)

        titulo = tk.Label(
            encabezado,
            text="LogiSmart - Sistema de Control Logístico Inteligente",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        titulo.pack(pady=10)

        # Botón de conexión MongoDB
        self.btn_conectar = tk.Button(
            encabezado,
            text="Conectar MongoDB",
            command=self.conectar_mongodb,
            bg="#27ae60",
            fg="black",
            font=("Arial", 9),
            padx=10
        )
        self.btn_conectar.place(x=10, y=15)

    def _crear_pestana_panel_control(self):
        """Crea la pestaña de panel de control."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Panel de Control")

        # Indicadores
        indicadores_frame = tk.LabelFrame(frame, text="Indicadores en tiempo real", font=('Arial', 12, 'bold'))
        indicadores_frame.pack(fill=tk.X, padx=10, pady=10)

        # Grid de indicadores
        self.indicadores = {}
        self.indicadores_frames = {}
        indicadores_data = [
            ("Camiones atendidos hoy", "0", "camiones"),
            ("Incidentes abiertos", "0", "incidentes"),
            ("Riesgos críticos", "0", "riesgos"),
            ("Evaluaciones LLM", "0", "evaluaciones")
        ]

        for i, (label, valor, tipo) in enumerate(indicadores_data):
            lbl_frame = tk.Frame(indicadores_frame, bg="#ecf0f1", relief=tk.RAISED, bd=2, cursor="hand2")
            lbl_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

            # Hover effect
            def on_enter(e, frame=lbl_frame):
                frame.config(bg="#d5dbdb")
            def on_leave(e, frame=lbl_frame):
                frame.config(bg="#ecf0f1")

            lbl_frame.bind("<Enter>", on_enter)
            lbl_frame.bind("<Leave>", on_leave)
            lbl_frame.bind("<Button-1>", lambda e, t=tipo: self.mostrar_detalle_indicador(t))

            tk.Label(lbl_frame, text=label, font=('Arial', 9), bg="#ecf0f1", fg="black").pack(pady=5)
            self.indicadores[label] = tk.Label(lbl_frame, text=valor, font=('Arial', 18, 'bold'),
                                                bg="#ecf0f1", fg="black", cursor="hand2")
            self.indicadores[label].pack(pady=5)
            self.indicadores[label].bind("<Button-1>", lambda e, t=tipo: self.mostrar_detalle_indicador(t))
            self.indicadores_frames[tipo] = lbl_frame

        indicadores_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # Filtros por fecha
        filtros_frame = tk.LabelFrame(frame, text="Filtros", font=('Arial', 12, 'bold'))
        filtros_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(filtros_frame, text="Fecha inicio:").grid(row=0, column=0, padx=5, pady=5)
        self.fecha_inicio = tk.Entry(filtros_frame)
        self.fecha_inicio.grid(row=0, column=1, padx=5, pady=5)
        self.fecha_inicio.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(filtros_frame, text="Fecha fin:").grid(row=0, column=2, padx=5, pady=5)
        self.fecha_fin = tk.Entry(filtros_frame)
        self.fecha_fin.grid(row=0, column=3, padx=5, pady=5)
        self.fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Button(filtros_frame, text="Actualizar", command=self.actualizar_panel).grid(row=0, column=4, padx=10, pady=5)

        # Panel de visualización de detalles
        self.detalle_frame = tk.LabelFrame(frame, text="Detalles (clic en un indicador)", font=('Arial', 12, 'bold'))
        self.detalle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview para mostrar detalles
        columnas = ("Fecha", "Detalle", "Resultado")
        self.tree_detalle = ttk.Treeview(self.detalle_frame, columns=columnas, show="headings", height=10)

        self.tree_detalle.heading("Fecha", text="Fecha")
        self.tree_detalle.heading("Detalle", text="Detalle")
        self.tree_detalle.heading("Resultado", text="Resultado")

        self.tree_detalle.column("Fecha", width=150)
        self.tree_detalle.column("Detalle", width=300)
        self.tree_detalle.column("Resultado", width=150)

        self.tree_detalle.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.detalle_frame, orient=tk.VERTICAL, command=self.tree_detalle.yview)
        self.tree_detalle.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _crear_pestana_control_acceso(self):
        """Crea la pestaña de control de acceso con diseño mejorado."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚛 Control de Acceso")

        # Panel principal
        main_panel = tk.Frame(frame, bg="#f0f0f0")
        main_panel.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Panel izquierdo: formulario de evaluación
        izquierda = tk.Frame(main_panel, bg="#f0f0f0")
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Título e instrucciones
        titulo_frame = tk.Frame(izquierda, bg="#f0f0f0")
        titulo_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            titulo_frame,
            text="📋 Evaluación de Acceso de Camiones",
            font=('Arial', 14, 'bold'),
            bg="#f0f0f0",
            fg="#2c3e50"
        ).pack(anchor=tk.W)

        tk.Label(
            titulo_frame,
            text="Configure las condiciones del camión para evaluar su acceso al terminal",
            font=('Arial', 10),
            bg="#f0f0f0",
            fg="#7f8c8d"
        ).pack(anchor=tk.W, pady=(5, 0))

        # Formulario de condiciones
        formulario_frame = tk.LabelFrame(
            izquierda,
            text="Condiciones del Camión",
            font=('Arial', 11, 'bold'),
            bg="#ffffff",
            fg="#2c3e50"
        )
        formulario_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Variables
        self.var_P = tk.BooleanVar()
        self.var_Q = tk.BooleanVar()
        self.var_R = tk.BooleanVar()
        self.var_S = tk.BooleanVar()
        self.var_V = tk.BooleanVar(value=True)
        self.var_H = tk.BooleanVar(value=True)

        # Agrupación de condiciones con descripciones claras
        # Campo de ID del camión
        tk.Label(
            formulario_frame,
            text="ID del Camion:",
            font=('Arial', 10, 'bold'),
            bg="#ffffff",
            fg="#2c3e50"
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky=tk.W)

        self.entry_camion_acceso = tk.Entry(
            formulario_frame,
            font=('Arial', 10),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.entry_camion_acceso.grid(row=0, column=1, padx=10, pady=(10, 5), sticky=tk.EW)

        # Grupo 1: Documentación y Autorización
        tk.Label(
            formulario_frame,
            text="Documentación y Autorización",
            font=('Arial', 10, 'bold'),
            bg="#ffffff",
            fg="#34495e"
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 5), sticky=tk.W)

        frame_doc = tk.Frame(formulario_frame, bg="#e8f4f8")
        frame_doc.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)

        tk.Checkbutton(
            frame_doc,
            text="Tiene autorización oficial",
            variable=self.var_P,
            bg="#e8f4f8",
            fg="#2c3e50",
            selectcolor="#e8f4f8",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        tk.Checkbutton(
            frame_doc,
            text="Conductor con certificacion",
            variable=self.var_S,
            bg="#e8f4f8",
            fg="#2c3e50",
            selectcolor="#e8f4f8",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        tk.Checkbutton(
            frame_doc,
            text="Certificacion vigente",
            variable=self.var_V,
            bg="#e8f4f8",
            fg="#2c3e50",
            selectcolor="#e8f4f8",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        # Grupo 2: Carga y Seguridad
        tk.Label(
            formulario_frame,
            text="Carga y Seguridad",
            font=('Arial', 10, 'bold'),
            bg="#ffffff",
            fg="#34495e"
        ).grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 5), sticky=tk.W)

        frame_carga = tk.Frame(formulario_frame, bg="#fef9e7")
        frame_carga.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)

        tk.Checkbutton(
            frame_carga,
            text="Peso excede el limite permitido",
            variable=self.var_Q,
            bg="#fef9e7",
            fg="#2c3e50",
            selectcolor="#fef9e7",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        tk.Checkbutton(
            frame_carga,
            text="Transporta materiales peligrosos",
            variable=self.var_R,
            bg="#fef9e7",
            fg="#2c3e50",
            selectcolor="#fef9e7",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        # Grupo 3: Horario
        tk.Label(
            formulario_frame,
            text="Horario",
            font=('Arial', 10, 'bold'),
            bg="#ffffff",
            fg="#34495e"
        ).grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 5), sticky=tk.W)

        frame_horario = tk.Frame(formulario_frame, bg="#e8f8f5")
        frame_horario.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)

        tk.Checkbutton(
            frame_horario,
            text="Esta dentro del horario permitido",
            variable=self.var_H,
            bg="#e8f8f5",
            fg="#2c3e50",
            selectcolor="#e8f8f5",
            font=('Arial', 10)
        ).pack(anchor=tk.W, padx=5, pady=2)

        # Botones de acción
        botones_frame = tk.Frame(formulario_frame, bg="#ffffff")
        botones_frame.grid(row=7, column=0, columnspan=2, pady=15)

        tk.Button(
            botones_frame,
            text="Evaluar Acceso",
            command=self.evaluar_acceso,
            bg="#3498db",
            fg="white",
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            botones_frame,
            text="Limpiar",
            command=self.limpiar_formulario_acceso,
            bg="#95a5a6",
            fg="white",
            font=('Arial', 11),
            padx=15,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=5)

        # Panel derecho: resultado y búsqueda
        derecha = tk.Frame(main_panel, bg="#f0f0f0")
        derecha.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Resultado visual
        resultado_frame = tk.LabelFrame(
            derecha,
            text="Resultado de Evaluación",
            font=('Arial', 11, 'bold'),
            bg="#ffffff",
            fg="#2c3e50"
        )
        resultado_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas para semáforo mejorado
        self.canvas_semaforo = tk.Canvas(resultado_frame, width=250, height=180, bg="white")
        self.canvas_semaforo.pack(pady=10)

        self.lbl_resultado = tk.Label(
            resultado_frame,
            text="Configure las condiciones y haga clic en Evaluar",
            font=('Arial', 12, 'bold'),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        self.lbl_resultado.pack(pady=5)

        self.txt_explicacion = scrolledtext.ScrolledText(
            resultado_frame,
            height=10,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg="#f8f9fa"
        )
        self.txt_explicacion.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configurar estilos para el texto de explicación
        self.txt_explicacion.tag_config("titulo", font=('Arial', 11, 'bold'), foreground="#2c3e50")

        # Búsqueda por placa mejorada
        busqueda_frame = tk.LabelFrame(
            derecha,
            text="Busqueda Rapida por Placa",
            font=('Arial', 11, 'bold'),
            bg="#ffffff",
            fg="#2c3e50"
        )
        busqueda_frame.pack(fill=tk.X)

        busqueda_input = tk.Frame(busqueda_frame, bg="#ffffff")
        busqueda_input.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(busqueda_input, text="Placa:", font=('Arial', 10), bg="#ffffff").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_placa = tk.Entry(
            busqueda_input,
            font=('Arial', 10),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.entry_placa.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_placa.bind("<Return>", lambda e: self.buscar_por_placa())

        tk.Button(
            busqueda_input,
            text="Buscar",
            command=self.buscar_por_placa,
            bg="#27ae60",
            fg="white",
            font=('Arial', 10, 'bold'),
            padx=15,
            cursor="hand2",
            relief=tk.FLAT
        ).pack(side=tk.LEFT)

    def _crear_pestana_gestion_camiones(self):
        """Crea la pestaña de gestión de camiones."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚛 Gestión Camiones")

        # Panel izquierdo: formulario de registro
        izquierda = tk.Frame(frame)
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        formulario_frame = tk.LabelFrame(izquierda, text="Registrar/Editar Camión", font=('Arial', 12, 'bold'))
        formulario_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Campos del formulario
        campos = [
            ("ID Camión (Auto):", "entry_camion_id"),
            ("Placa:", "entry_placa"),
            ("Empresa:", "entry_empresa"),
            ("Peso Máximo (kg):", "entry_peso_max")
        ]

        self.camiones_entries = {}
        for i, (label, attr) in enumerate(campos):
            tk.Label(formulario_frame, text=label, font=('Arial', 10)).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entry = tk.Entry(formulario_frame, font=('Arial', 10))
            entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)
            self.camiones_entries[attr] = entry

        # El campo ID es de solo lectura
        self.camiones_entries["entry_camion_id"].config(state=tk.DISABLED, bg="#ecf0f1")

        # Checkboxes
        self.var_autorizacion = tk.BooleanVar()
        self.var_certificacion = tk.BooleanVar()
        self.var_materiales_peligrosos = tk.BooleanVar()

        row_idx = len(campos)
        tk.Checkbutton(formulario_frame, text="Autorización", variable=self.var_autorizacion).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        tk.Checkbutton(formulario_frame, text="Conductor Certificado", variable=self.var_certificacion).grid(row=row_idx+1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        tk.Checkbutton(formulario_frame, text="Materiales Peligrosos", variable=self.var_materiales_peligrosos).grid(row=row_idx+2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Botones
        botones_frame = tk.Frame(formulario_frame)
        botones_frame.grid(row=row_idx+3, column=0, columnspan=2, pady=10)

        tk.Button(botones_frame, text="Agregar", command=self.registrar_camion, bg="#27ae60", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Editar", command=self.actualizar_camion, bg="#3498db", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Eliminar", command=self.eliminar_camion, bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Limpiar", command=self.limpiar_formulario_camion, bg="#95a5a6", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)

        # Panel derecho: lista de camiones
        derecha = tk.Frame(frame)
        derecha.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        lista_frame = tk.LabelFrame(derecha, text="Camiones Registrados", font=('Arial', 12, 'bold'))
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview para camiones
        columnas = ("camion_id", "placa", "empresa", "autorizacion", "certificacion", "materiales_peligrosos")
        self.tree_camiones = ttk.Treeview(lista_frame, columns=columnas, show="headings", height=15)

        self.tree_camiones.heading("camion_id", text="ID")
        self.tree_camiones.heading("placa", text="Placa")
        self.tree_camiones.heading("empresa", text="Empresa")
        self.tree_camiones.heading("autorizacion", text="Autorizado")
        self.tree_camiones.heading("certificacion", text="Certificado")
        self.tree_camiones.heading("materiales_peligrosos", text="Peligrosos")

        self.tree_camiones.column("camion_id", width=100)
        self.tree_camiones.column("placa", width=100)
        self.tree_camiones.column("empresa", width=150)
        self.tree_camiones.column("autorizacion", width=80)
        self.tree_camiones.column("certificacion", width=80)
        self.tree_camiones.column("materiales_peligrosos", width=80)

        self.tree_camiones.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree_camiones.yview)
        self.tree_camiones.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Evento de selección
        self.tree_camiones.bind("<<TreeviewSelect>>", self.on_camion_seleccionado)

        # Botón actualizar lista
        tk.Button(lista_frame, text="Refrescar", command=self.cargar_lista_camiones, bg="#f39c12", fg="white", font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=5, pady=5)

        # Cargar camiones iniciales
        self.root.after(500, self.cargar_lista_camiones)

    def _crear_pestana_simulador_reglas(self):
        """Crea la pestaña de simulador de tablas de verdad con mejor experiencia."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔬 Simulador Reglas")

        # Panel principal dividido
        main_panel = tk.Frame(frame, bg="#f0f0f0")
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel izquierdo: Interruptores y explicación
        izquierda = tk.Frame(main_panel, bg="#f0f0f0")
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Interruptores interactivos
        interruptores_frame = tk.LabelFrame(izquierda, text="Variables de Entrada", font=('Arial', 12, 'bold'), bg="#ffffff", fg="#2c3e50")
        interruptores_frame.pack(fill=tk.X, pady=(0, 10))

        # Variables
        self.sim_P = tk.BooleanVar()
        self.sim_Q = tk.BooleanVar()
        self.sim_R = tk.BooleanVar()
        self.sim_S = tk.BooleanVar()

        def actualizar_simulacion(*args):
            self.actualizar_tabla_verdad()

        # Descripciones detalladas
        var_info = [
            (self.sim_P, "P", "Autorización Oficial", "El camión tiene autorización oficial"),
            (self.sim_Q, "Q", "Exceso de Peso", "El camión excede el peso permitido"),
            (self.sim_R, "R", "Materiales Peligrosos", "Transporta materiales peligrosos"),
            (self.sim_S, "S", "Certificación", "El conductor tiene certificación vigente")
        ]

        for i, (var, abrev, titulo, desc) in enumerate(var_info):
            frame_var = tk.Frame(interruptores_frame, bg="#ffffff")
            frame_var.grid(row=i, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)

            chk = tk.Checkbutton(
                frame_var,
                text=f"{abrev}: {titulo}",
                variable=var,
                command=actualizar_simulacion,
                font=('Arial', 10, 'bold'),
                bg="#ffffff",
                fg="#2c3e50",
                selectcolor="#ffffff"
            )
            chk.pack(anchor=tk.W)

            tk.Label(
                frame_var,
                text=desc,
                font=('Arial', 9),
                bg="#ffffff",
                fg="#7f8c8d"
            ).pack(anchor=tk.W, padx=(20, 0))

            var.trace_add('write', actualizar_simulacion)

        interruptores_frame.columnconfigure(0, weight=1)

        # Panel de resultado visual
        resultado_frame = tk.LabelFrame(izquierda, text="Resultado de Evaluación", font=('Arial', 12, 'bold'), bg="#ffffff", fg="#2c3e50")
        resultado_frame.pack(fill=tk.X, pady=(0, 10))

        # Canvas para resultado
        self.canvas_simulador = tk.Canvas(resultado_frame, width=300, height=100, bg="white")
        self.canvas_simulador.pack(pady=10)

        self.lbl_resultado_simulador = tk.Label(
            resultado_frame,
            text="Ajuste las variables para ver el resultado",
            font=('Arial', 11, 'bold'),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        self.lbl_resultado_simulador.pack(pady=5)

        # Explicación de fórmulas
        formulas_frame = tk.LabelFrame(izquierda, text="Fórmulas Utilizadas", font=('Arial', 12, 'bold'), bg="#ffffff", fg="#2c3e50")
        formulas_frame.pack(fill=tk.BOTH, expand=True)

        formulas_text = """
¬Q = NOT Q (No exceso de peso)
P∧S = P AND S (Autorización Y Certificación)
R∨Q = R OR Q (Peligrosos O Exceso de peso)
A = P∧S∧¬Q (Acceso estándar)
E = P∧(R∨Q) (Inspección especial)
        """
        tk.Label(
            formulas_frame,
            text=formulas_text,
            font=('Arial', 9),
            bg="#ffffff",
            fg="#34495e",
            justify=tk.LEFT
        ).pack(padx=10, pady=10, anchor=tk.W)

        # Panel derecho: Tabla de verdad
        derecha = tk.Frame(main_panel, bg="#f0f0f0")
        derecha.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tabla_frame = tk.LabelFrame(derecha, text="Tabla de Verdad en Vivo", font=('Arial', 12, 'bold'), bg="#ffffff", fg="#2c3e50")
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("P", "Q", "R", "S", "¬Q", "P∧S", "R∨Q", "A", "E")
        self.tree_tabla = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree_tabla.heading(col, text=col)
            self.tree_tabla.column(col, width=60, anchor=tk.CENTER)

        self.tree_tabla.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tree_tabla.yview)
        self.tree_tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Inicializar tabla
        self.actualizar_tabla_verdad()

    def _crear_pestana_incidentes(self):
        """Crea la pestaña de bandeja de incidentes con gestión completa."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📧 Bandeja Incidentes")

        # Panel izquierdo: formulario
        izquierda = tk.Frame(frame)
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        formulario_frame = tk.LabelFrame(izquierda, text="Nuevo/Editar Incidente", font=('Arial', 12, 'bold'))
        formulario_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(formulario_frame, text="ID Incidente:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_incidente_id = tk.Entry(formulario_frame)
        self.entry_incidente_id.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.entry_incidente_id.config(state=tk.DISABLED, bg="#ecf0f1")

        tk.Label(formulario_frame, text="Remitente:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_remitente = tk.Entry(formulario_frame)
        self.entry_remitente.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        tk.Label(formulario_frame, text="Asunto:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_asunto = tk.Entry(formulario_frame)
        self.entry_asunto.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        tk.Label(formulario_frame, text="Cuerpo:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.NW)
        self.txt_cuerpo = scrolledtext.ScrolledText(formulario_frame, height=8)
        self.txt_cuerpo.grid(row=3, column=1, padx=5, pady=5, sticky=tk.NSEW)

        tk.Label(formulario_frame, text="Estado:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.combo_estado = ttk.Combobox(formulario_frame, values=["nuevo", "en_proceso", "resuelto", "cerrado"], width=30)
        self.combo_estado.grid(row=4, column=1, padx=5, pady=5, sticky=tk.EW)
        self.combo_estado.set("nuevo")

        # Botones
        botones_frame = tk.Frame(formulario_frame)
        botones_frame.grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(botones_frame, text="Agregar", command=self.agregar_incidente, bg="#27ae60", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Editar", command=self.editar_incidente, bg="#3498db", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Eliminar", command=self.eliminar_incidente, bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Limpiar", command=self.limpiar_formulario_incidente, bg="#95a5a6", fg="white", font=('Arial', 10, 'bold'), padx=10).pack(side=tk.LEFT, padx=5)

        formulario_frame.columnconfigure(1, weight=1)
        formulario_frame.rowconfigure(3, weight=1)

        # Panel derecho: lista de incidentes
        derecha = tk.Frame(frame)
        derecha.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        lista_frame = tk.LabelFrame(derecha, text="Incidentes Registrados", font=('Arial', 12, 'bold'))
        lista_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview para incidentes
        columnas = ("ID", "Remitente", "Asunto", "Estado", "Fecha")
        self.tree_incidentes = ttk.Treeview(lista_frame, columns=columnas, show="headings", height=20)

        self.tree_incidentes.heading("ID", text="ID")
        self.tree_incidentes.heading("Remitente", text="Remitente")
        self.tree_incidentes.heading("Asunto", text="Asunto")
        self.tree_incidentes.heading("Estado", text="Estado")
        self.tree_incidentes.heading("Fecha", text="Fecha")

        self.tree_incidentes.column("ID", width=80)
        self.tree_incidentes.column("Remitente", width=120)
        self.tree_incidentes.column("Asunto", width=200)
        self.tree_incidentes.column("Estado", width=100)
        self.tree_incidentes.column("Fecha", width=150)

        self.tree_incidentes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree_incidentes.yview)
        self.tree_incidentes.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Evento de selección
        self.tree_incidentes.bind("<<TreeviewSelect>>", self.on_incidente_seleccionado)

        # Botón refrescar
        tk.Button(lista_frame, text="Refrescar", command=self.cargar_lista_incidentes, bg="#f39c12", fg="white", font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=5, pady=5)

        # Cargar incidentes iniciales
        self.root.after(500, self.cargar_lista_incidentes)

    def _crear_pestana_asistente(self):
        """Crea la pestaña del asistente LLM con diseño mejorado."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🤖 Asistente LLM")

        # Panel principal
        main_panel = tk.Frame(frame, bg="#f0f0f0")
        main_panel.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header con estado de conexión
        header_frame = tk.Frame(main_panel, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_estado_asistente = tk.Label(
            header_frame,
            text="🔴 No conectado a MongoDB",
            font=('Arial', 10, 'bold'),
            bg="#f0f0f0",
            fg="#e74c3c"
        )
        self.lbl_estado_asistente.pack(side=tk.LEFT)

        # Área de chat con mejor diseño
        chat_frame = tk.LabelFrame(
            main_panel,
            text="💬 Conversación",
            font=('Arial', 12, 'bold'),
            bg="#ffffff",
            fg="#2c3e50"
        )
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_asistente = scrolledtext.ScrolledText(
            chat_frame,
            height=18,
            wrap=tk.WORD,
            font=('Arial', 11),
            bg="#ffffff",
            fg="#2c3e50",
            insertbackground="#3498db"
        )
        self.chat_asistente.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Estilos de chat mejorados
        self.chat_asistente.tag_config("usuario", foreground="#2980b9", font=("Arial", 11, "bold"), background="#e8f4f8")
        self.chat_asistente.tag_config("asistente", foreground="#27ae60", font=("Arial", 11), background="#e8f8f0")
        self.chat_asistente.tag_config("sistema", foreground="#7f8c8d", font=("Arial", 9, "italic"))
        self.chat_asistente.tag_config("error", foreground="#e74c3c", font=("Arial", 10, "bold"))
        self.chat_asistente.tag_config("escribiendo", foreground="#f39c12", font=("Arial", 10, "italic"))

        # Panel de sugerencias
        sugerencias_frame = tk.Frame(main_panel, bg="#f0f0f0")
        sugerencias_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            sugerencias_frame,
            text="💡 Preguntas sugeridas:",
            font=('Arial', 9, 'bold'),
            bg="#f0f0f0",
            fg="#7f8c8d"
        ).pack(side=tk.LEFT, padx=(0, 5))

        sugerencias = [
            "¿Qué camiones hay registrados?",
            "¿Cuáles son los accesos de hoy?",
            "¿Qué incidentes hay registrados?",
            "¿Qué riesgos éticos existen?"
        ]

        for i, sugerencia in enumerate(sugerencias):
            btn = tk.Button(
                sugerencias_frame,
                text=sugerencia,
                font=('Arial', 8),
                bg="#ecf0f1",
                fg="#34495e",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda s=sugerencia: self.usar_sugerencia(s)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Área de entrada mejorada
        entrada_frame = tk.Frame(main_panel, bg="#f0f0f0")
        entrada_frame.pack(fill=tk.X)

        self.entry_pregunta_asistente = tk.Entry(
            entrada_frame,
            font=('Arial', 11),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db"
        )
        self.entry_pregunta_asistente.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry_pregunta_asistente.bind("<Return>", lambda e: self.enviar_pregunta_asistente())
        self.entry_pregunta_asistente.bind("<FocusIn>", lambda e: self.entry_pregunta_asistente.config(highlightbackground="#3498db"))
        self.entry_pregunta_asistente.bind("<FocusOut>", lambda e: self.entry_pregunta_asistente.config(highlightbackground="#bdc3c7"))

        # Botón enviar mejorado
        self.btn_enviar_asistente = tk.Button(
            entrada_frame,
            text="Enviar",
            font=('Arial', 10, 'bold'),
            bg="#3498db",
            fg="black",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.enviar_pregunta_asistente,
            padx=15,
            pady=5
        )
        self.btn_enviar_asistente.pack(side=tk.LEFT, padx=(0, 5))

        # Botón limpiar
        tk.Button(
            entrada_frame,
            text="Limpiar",
            font=('Arial', 10),
            bg="#95a5a6",
            fg="black",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.limpiar_chat_asistente,
            padx=10,
            pady=5
        ).pack(side=tk.LEFT)

        # Mensaje inicial mejorado
        self.chat_asistente.insert(tk.END, "🤖 Sistema: ¡Hola! Soy tu asistente inteligente de LogiSmart.\n\n", "sistema")
        self.chat_asistente.insert(tk.END, "📍 Puedo ayudarte con:\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Información sobre camiones registrados\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Historial de accesos al terminal\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Incidentes y su estado\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Riesgos éticos del sistema\n\n", "sistema")
        self.chat_asistente.insert(tk.END, "⚠️ Primero conecta a MongoDB para que pueda acceder a los datos.\n\n", "sistema")

    def _crear_pestana_riesgos(self):
        """Crea la pestaña de riesgos éticos."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚠️ Riesgos Éticos")

        # Panel izquierdo: lista de riesgos
        izquierda = tk.Frame(frame)
        izquierda.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        lista_frame = tk.LabelFrame(izquierda, text="Riesgos Registrados", font=('Arial', 12, 'bold'))
        lista_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Módulo", "Categoría", "Nivel", "Puntaje")
        self.tree_riesgos = ttk.Treeview(lista_frame, columns=columns, show="headings")

        for col in columns:
            self.tree_riesgos.heading(col, text=col)
            self.tree_riesgos.column(col, width=100)

        self.tree_riesgos.pack(fill=tk.BOTH, expand=True)

        # Botones
        botones_frame = tk.Frame(izquierda)
        botones_frame.pack(fill=tk.X, pady=5)

        tk.Button(botones_frame, text="Agregar Riesgo", command=self.agregar_riesgo).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Editar", command=self.editar_riesgo).pack(side=tk.LEFT, padx=5)
        tk.Button(botones_frame, text="Eliminar", command=self.eliminar_riesgo).pack(side=tk.LEFT, padx=5)

        # Panel derecho: gráfica
        derecha = tk.Frame(frame)
        derecha.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        grafica_frame = tk.LabelFrame(derecha, text="Visualización de Riesgos", font=('Arial', 12, 'bold'))
        grafica_frame.pack(fill=tk.BOTH, expand=True)

        self.fig_riesgos, self.ax_riesgos = plt.subplots(figsize=(6, 5))
        self.canvas_riesgos = FigureCanvasTkAgg(self.fig_riesgos, grafica_frame)
        self.canvas_riesgos.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Cargar riesgos iniciales
        self.actualizar_lista_riesgos()
        self.actualizar_grafica_riesgos()

    def _crear_pestana_configuracion(self):
        """Crea la pestaña de configuración."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Configuración")

        config_frame = tk.LabelFrame(frame, text="Configuración del Sistema", font=('Arial', 12, 'bold'))
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # Modelo Ollama
        tk.Label(config_frame, text="Modelo Ollama:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_modelo_ollama = tk.Entry(config_frame)
        self.entry_modelo_ollama.grid(row=0, column=1, padx=5, pady=5)
        self.entry_modelo_ollama.insert(0, config.ollama.model)

        # Host Ollama
        tk.Label(config_frame, text="Host Ollama:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_host_ollama = tk.Entry(config_frame)
        self.entry_host_ollama.grid(row=1, column=1, padx=5, pady=5)
        self.entry_host_ollama.insert(0, config.ollama.host)

        # MongoDB
        tk.Label(config_frame, text="MongoDB Host:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_mongo_host = tk.Entry(config_frame)
        self.entry_mongo_host.grid(row=2, column=1, padx=5, pady=5)
        self.entry_mongo_host.insert(0, config.mongo.host)

        tk.Label(config_frame, text="MongoDB Port:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_mongo_port = tk.Entry(config_frame)
        self.entry_mongo_port.grid(row=3, column=1, padx=5, pady=5)
        self.entry_mongo_port.insert(0, str(config.mongo.port))

        tk.Label(config_frame, text="MongoDB Database:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.entry_mongo_db = tk.Entry(config_frame)
        self.entry_mongo_db.grid(row=4, column=1, padx=5, pady=5)
        self.entry_mongo_db.insert(0, config.mongo.database)

        # Modo simulación
        self.var_simulacion = tk.BooleanVar(value=config.modo_simulacion)
        tk.Checkbutton(config_frame, text="Modo simulación (correo)", variable=self.var_simulacion).grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(config_frame, text="Guardar Configuración", command=self.guardar_configuracion).grid(row=6, column=0, columnspan=2, pady=10)

    def _crear_barra_estado(self):
        """Crea la barra de estado."""
        self.barra_estado = tk.Label(
            self.root,
            text="Listo",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Arial', 9)
        )
        self.barra_estado.pack(fill=tk.X, side=tk.BOTTOM)

    # ============================================================
    # MÉTODOS DE EVENTOS
    # ============================================================

    def conectar_mongodb(self):
        """Conecta a MongoDB y actualiza el estado del asistente."""
        try:
            self.mongo_repo = MongoDBRepository()
            self.asistente = AsistenteLLM(config.ollama.model, self.mongo_repo, self.matriz_riesgos)
            self.conectado_mongodb = True
            self.btn_conectar.config(text="✓ Conectado", bg="#27ae60")
            self.barra_estado.config(text="Conectado a MongoDB")

            # Sincronizar riesgos desde MongoDB
            self._sincronizar_riesgos_desde_mongodb()

            # Actualizar estado del asistente
            if hasattr(self, 'lbl_estado_asistente'):
                self.lbl_estado_asistente.config(text="🟢 Conectado a MongoDB", fg="#27ae60")

            messagebox.showinfo("Éxito", "Conectado a MongoDB exitosamente\n\nEl asistente de IA ahora puede responder preguntas sobre los datos.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a MongoDB:\n{e}")
            self.barra_estado.config(text=f"Error de conexión: {e}")

    def _sincronizar_riesgos_desde_mongodb(self):
        """Sincroniza los riesgos desde MongoDB con la matriz de riesgos en memoria."""
        try:
            # Limpiar riesgos existentes
            self.matriz_riesgos.riesgos = {}
            self.matriz_riesgos._contador_id = 0

            # Cargar riesgos desde MongoDB
            riesgos_mongo = self.mongo_repo.listar_riesgos()

            if riesgos_mongo:
                # Recrear riesgos en memoria desde MongoDB
                for r in riesgos_mongo:
                    self.matriz_riesgos.registrar_riesgo(
                        modulo=r.get('modulo', 'N/A'),
                        descripcion=r.get('descripcion', ''),
                        categoria=r.get('categoria', 'otro'),
                        probabilidad=r.get('probabilidad', 1),
                        impacto=r.get('impacto', 1),
                        mitigacion=r.get('mitigacion', '')
                    )
            else:
                # Si no hay riesgos en MongoDB, cargar predefinidos
                self.matriz_riesgos.cargar_riesgos_predefinidos()

            # Actualizar la lista y gráfica
            if hasattr(self, 'tree_riesgos'):
                self.actualizar_lista_riesgos()
            if hasattr(self, 'ax_riesgos'):
                self.actualizar_grafica_riesgos()

        except Exception as e:
            # En caso de error, cargar predefinidos
            self.matriz_riesgos.cargar_riesgos_predefinidos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a MongoDB:\n{e}")
            self.barra_estado.config(text=f"Error de conexión: {e}")

    def actualizar_panel(self):
        """Actualiza los indicadores del panel de control."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        try:
            # Actualizar indicadores con filtro de fecha del día actual
            fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = datetime.now()

            stats = self.mongo_repo.obtener_estadisticas_accesos(fecha_inicio, fecha_fin)

            incidentes = self.mongo_repo.listar_incidentes(estado="nuevo")
            riesgos = self.matriz_riesgos.listar_riesgos(nivel="crítico")

            # Obtener evaluaciones LLM desde MongoDB
            try:
                evaluaciones = self.mongo_repo.obtener_evaluaciones()
                num_eval = len(evaluaciones)
            except:
                num_eval = 0

            # Sumar todos los resultados (no filtrar por tipo específico)
            total_accesos = sum(stats.values())

            self.indicadores["Camiones atendidos hoy"].config(text=str(total_accesos))
            self.indicadores["Incidentes abiertos"].config(text=str(len(incidentes)))
            self.indicadores["Riesgos críticos"].config(text=str(len(riesgos)))
            self.indicadores["Evaluaciones LLM"].config(text=str(num_eval))

            self.barra_estado.config(text="Panel actualizado")
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar panel:\n{e}")

    def mostrar_detalle_indicador(self, tipo):
        """Muestra los detalles del indicador seleccionado."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        # Limpiar treeview
        for item in self.tree_detalle.get_children():
            self.tree_detalle.delete(item)

        try:
            if tipo == "camiones":
                # Mostrar accesos del día
                accesos = self.mongo_repo.obtener_accesos_por_fecha(
                    datetime.now().replace(hour=0, minute=0, second=0),
                    datetime.now()
                )
                for acc in accesos[:20]:
                    fecha = acc.get('marca_tiempo', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime("%Y-%m-%d %H:%M")
                    self.tree_detalle.insert("", "end", values=(
                        fecha,
                        f"Camión: {acc.get('camion_id', 'N/A')}",
                        acc.get('resultado', 'N/A')
                    ))

            elif tipo == "incidentes":
                # Mostrar incidentes abiertos
                incidentes = self.mongo_repo.listar_incidentes(estado="nuevo")
                for inc in incidentes[:20]:
                    fecha = inc.get('fecha_creacion', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime("%Y-%m-%d %H:%M")
                    categoria = inc.get('clasificacion', {}).get('categoria', 'N/A')
                    asunto = inc.get('asunto_original', 'N/A')[:40]
                    self.tree_detalle.insert("", "end", values=(
                        fecha,
                        f"{categoria}: {asunto}",
                        inc.get('estado', 'N/A')
                    ))

            elif tipo == "riesgos":
                # Mostrar riesgos críticos
                riesgos = self.matriz_riesgos.listar_riesgos(nivel="crítico")
                for id_riesgo, r in riesgos[:20]:
                    self.tree_detalle.insert("", "end", values=(
                        r.fecha_registro[:10] if r.fecha_registro else 'N/A',
                        f"{r.categoria}: {r.descripcion[:40]}",
                        f"Puntaje: {r.puntaje}"
                    ))

            elif tipo == "evaluaciones":
                # Mostrar evaluaciones LLM
                try:
                    evaluaciones = self.mongo_repo.obtener_evaluaciones()
                    for eval in evaluaciones[:20]:
                        fecha = eval.get('fecha_registro', 'N/A')
                        if hasattr(fecha, 'strftime'):
                            fecha = fecha.strftime("%Y-%m-%d %H:%M")
                        modelo = eval.get('modelo', 'N/A')
                        confianza = eval.get('confianza', 'N/A')
                        self.tree_detalle.insert("", "end", values=(
                            fecha,
                            f"Modelo: {modelo}",
                            f"Confianza: {confianza}"
                        ))
                except Exception as e:
                    self.tree_detalle.insert("", "end", values=(
                        "Error",
                        f"No se pudieron cargar evaluaciones: {e}",
                        "N/A"
                    ))

            self.barra_estado.config(text=f"Mostrando detalles de {tipo}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar detalles: {e}")

    def evaluar_acceso(self):
        """Evalúa el acceso de un camión usando el motor de reglas con mejor feedback visual."""
        P = self.var_P.get()
        Q = self.var_Q.get()
        R = self.var_R.get()
        S = self.var_S.get()
        V = self.var_V.get()
        H = self.var_H.get()

        resultado = self.motor_reglas.evaluar_camion(P, Q, R, S, V, H)

        # Dibujar semáforo mejorado
        self.canvas_semaforo.delete("all")
        decision = resultado["decision_final"]

        if decision == "ACCESO_ESTANDAR":
            color = "#27ae60"  # Verde
            icono = "✓"
            texto_estado = "ACCESO PERMITIDO"
            texto_color = "#27ae60"
        elif decision == "INSPECCION_ESPECIAL":
            color = "#f39c12"  # Naranja
            icono = "⚠"
            texto_estado = "INSPECCIÓN REQUERIDA"
            texto_color = "#f39c12"
        else:
            color = "#e74c3c"  # Rojo
            icono = "✗"
            texto_estado = "ACCESO DENEGADO"
            texto_color = "#e74c3c"

        # Dibujar círculo grande con borde
        self.canvas_semaforo.create_oval(75, 40, 175, 140, fill=color, outline="black", width=3)
        self.canvas_semaforo.create_text(125, 90, text=icono, fill="white", font=("Arial", 40, "bold"))

        # Etiqueta de resultado
        self.lbl_resultado.config(text=texto_estado, fg=texto_color, font=('Arial', 13, 'bold'))

        # Mostrar explicación mejorada
        self.txt_explicacion.delete(1.0, tk.END)
        self.txt_explicacion.insert(tk.END, "📋 ANÁLISIS DE DECISIÓN:\n\n", "titulo")
        self.txt_explicacion.insert(tk.END, f"Resultado final: {texto_estado}\n\n", "titulo")
        self.txt_explicacion.insert(tk.END, "—" * 40 + "\n\n")
        self.txt_explicacion.insert(tk.END, "EVALUACIÓN DE REGLAS:\n\n", "titulo")

        for i, exp in enumerate(resultado["explicacion_detallada"], 1):
            self.txt_explicacion.insert(tk.END, f"{i}. {exp}\n\n", "titulo")

        # Guardar en MongoDB si está conectado
        if self.mongo_repo:
            try:
                self.mongo_repo.registrar_acceso({
                    "camion_id": "MANUAL",
                    "P": P, "Q": Q, "R": R, "S": S, "V": V, "H": H,
                    "resultado": decision,
                    "explicacion": resultado["explicacion_detallada"]
                })
                self.barra_estado.config(text=f"Evaluación completada: {texto_estado} (Guardado en MongoDB)")
            except Exception as e:
                print(f"Error al guardar acceso: {e}")
                self.barra_estado.config(text=f"Evaluación completada: {texto_estado}")
        else:
            self.barra_estado.config(text=f"Evaluación completada: {texto_estado}")

    def limpiar_formulario_acceso(self):
        """Limpia el formulario de control de acceso."""
        self.var_P.set(False)
        self.var_Q.set(False)
        self.var_R.set(False)
        self.var_S.set(False)
        self.var_V.set(True)
        self.var_H.set(True)

        # Limpiar resultado
        self.canvas_semaforo.delete("all")
        self.lbl_resultado.config(
            text="Configure las condiciones y haga clic en Evaluar",
            fg="#7f8c8d",
            font=('Arial', 12, 'bold')
        )
        self.txt_explicacion.delete(1.0, tk.END)
        self.barra_estado.config(text="Formulario limpiado")

    def buscar_por_placa(self):
        """Busca un camión por su placa."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        placa = self.entry_placa.get().strip()
        if not placa:
            messagebox.showwarning("Advertencia", "Ingrese una placa")
            return

        camion = self.mongo_repo.obtener_camion_por_placa(placa)
        if camion:
            messagebox.showinfo("Camión encontrado", f"ID: {camion.get('camion_id')}\nEmpresa: {camion.get('empresa')}")
        else:
            messagebox.showinfo("Resultado", "No se encontró el camión")

    def actualizar_tabla_verdad(self):
        """Actualiza la tabla de verdad en vivo y el resultado visual."""
        P = self.sim_P.get()
        Q = self.sim_Q.get()
        R = self.sim_R.get()
        S = self.sim_S.get()

        # Calcular valores intermedios
        not_Q = not Q
        P_and_S = P and S
        R_or_Q = R or Q
        A = P and S and not Q  # Acceso estándar
        E = P and (R or Q)  # Inspección especial

        # Limpiar tabla
        for item in self.tree_tabla.get_children():
            self.tree_tabla.delete(item)

        # Agregar fila actual
        v = lambda b: "V" if b else "F"
        self.tree_tabla.insert("", "end", values=(
            v(P), v(Q), v(R), v(S),
            v(not_Q), v(P_and_S), v(R_or_Q),
            v(A), v(E)
        ))

        # Actualizar resultado visual
        self.canvas_simulador.delete("all")

        if A:
            color = "#27ae60"  # Verde
            icono = "✓"
            texto = "ACCESO ESTÁNDAR"
            texto_color = "#27ae60"
        elif E:
            color = "#f39c12"  # Naranja
            icono = "⚠"
            texto = "INSPECCIÓN ESPECIAL"
            texto_color = "#f39c12"
        else:
            color = "#e74c3c"  # Rojo
            icono = "✗"
            texto = "ACCESO DENEGADO"
            texto_color = "#e74c3c"

        # Dibujar círculo con resultado
        self.canvas_simulador.create_oval(100, 20, 200, 80, fill=color, outline="black", width=2)
        self.canvas_simulador.create_text(150, 50, text=icono, fill="white", font=("Arial", 30, "bold"))

        # Actualizar etiqueta de resultado
        self.lbl_resultado_simulador.config(text=texto, fg=texto_color)

    def cargar_lista_incidentes(self):
        """Carga la lista de incidentes desde MongoDB."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        try:
            # Limpiar lista actual
            for item in self.tree_incidentes.get_children():
                self.tree_incidentes.delete(item)

            # Obtener incidentes
            incidentes = self.mongo_repo.listar_incidentes()

            # Agregar al treeview
            for incidente in incidentes:
                # Formatear fecha
                fecha = incidente.get('fecha_creacion', 'N/A')
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime("%Y-%m-%d %H:%M")
                elif isinstance(fecha, str):
                    fecha = fecha[:19]  # Truncar si es string ISO

                # Truncar asunto si es muy largo
                asunto = incidente.get('asunto_original', 'N/A')
                if len(asunto) > 30:
                    asunto = asunto[:30] + '...'

                self.tree_incidentes.insert("", "end", values=(
                    str(incidente.get('_id', 'N/A')),
                    incidente.get('remitente', 'N/A'),
                    asunto,
                    incidente.get('estado', 'nuevo'),
                    fecha
                ))

            self.barra_estado.config(text=f"Cargados {len(incidentes)} incidentes")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar incidentes: {e}")

    def agregar_incidente(self):
        """Agrega un nuevo incidente."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        remitente = self.entry_remitente.get().strip()
        asunto = self.entry_asunto.get().strip()
        cuerpo = self.txt_cuerpo.get(1.0, tk.END).strip()
        estado = self.combo_estado.get().strip()

        if not asunto or not cuerpo:
            messagebox.showwarning("Advertencia", "Asunto y Cuerpo son obligatorios")
            return

        try:
            # Clasificar el incidente
            resultado = self.clasificador.clasificar(asunto, cuerpo, usar_llm=True)

            # Crear incidente en MongoDB
            self.mongo_repo.crear_incidente({
                "remitente": remitente,
                "asunto_original": asunto,
                "cuerpo_original": cuerpo,
                "clasificacion": resultado,
                "estado": estado
            })

            messagebox.showinfo("Éxito", "Incidente agregado exitosamente")
            self.limpiar_formulario_incidente()
            self.cargar_lista_incidentes()

        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar incidente: {e}")

    def editar_incidente(self):
        """Edita un incidente existente."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        incidente_id = self.entry_incidente_id.get().strip()
        if not incidente_id:
            messagebox.showwarning("Advertencia", "Seleccione un incidente para editar")
            return

        try:
            # Convertir a ObjectId
            obj_id = ObjectId(incidente_id)

            # Obtener el incidente actual
            incidentes = self.mongo_repo.listar_incidentes()
            incidente_actual = None
            for inc in incidentes:
                if str(inc.get('_id')) == incidente_id:
                    incidente_actual = inc
                    break

            if not incidente_actual:
                messagebox.showwarning("Advertencia", "No se encontró el incidente")
                return

            # Actualizar datos
            remitente = self.entry_remitente.get().strip()
            asunto = self.entry_asunto.get().strip()
            cuerpo = self.txt_cuerpo.get(1.0, tk.END).strip()
            estado = self.combo_estado.get().strip()

            # Reclasificar si cambió asunto o cuerpo
            resultado = incidente_actual.get('clasificacion', {})
            if asunto != incidente_actual.get('asunto_original', '') or cuerpo != incidente_actual.get('cuerpo_original', ''):
                resultado = self.clasificador.clasificar(asunto, cuerpo, usar_llm=True)

            # Actualizar en MongoDB
            self.mongo_repo.actualizar_incidente(obj_id, {
                "remitente": remitente,
                "asunto_original": asunto,
                "cuerpo_original": cuerpo,
                "clasificacion": resultado,
                "estado": estado
            })

            messagebox.showinfo("Éxito", "Incidente actualizado exitosamente")
            self.limpiar_formulario_incidente()
            self.cargar_lista_incidentes()

        except Exception as e:
            messagebox.showerror("Error", f"Error al editar incidente: {e}")

    def eliminar_incidente(self):
        """Elimina un incidente."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        incidente_id = self.entry_incidente_id.get().strip()
        if not incidente_id:
            messagebox.showwarning("Advertencia", "Seleccione un incidente para eliminar")
            return

        # Confirmar
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el incidente {incidente_id}?"):
            return

        try:
            # Convertir a ObjectId
            obj_id = ObjectId(incidente_id)
            eliminado = self.mongo_repo.eliminar_incidente(obj_id)
            if eliminado:
                messagebox.showinfo("Éxito", "Incidente eliminado exitosamente")
                self.limpiar_formulario_incidente()
                self.cargar_lista_incidentes()
            else:
                messagebox.showwarning("Advertencia", "No se pudo eliminar el incidente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar incidente: {e}")

    def limpiar_formulario_incidente(self):
        """Limpia el formulario de incidentes."""
        self.entry_incidente_id.config(state=tk.NORMAL)
        self.entry_incidente_id.delete(0, tk.END)
        self.entry_incidente_id.config(state=tk.DISABLED, bg="#ecf0f1")

        self.entry_remitente.delete(0, tk.END)
        self.entry_asunto.delete(0, tk.END)
        self.txt_cuerpo.delete(1.0, tk.END)
        self.combo_estado.set("nuevo")

    def on_incidente_seleccionado(self, event):
        """Carga los datos del incidente seleccionado en el formulario."""
        seleccion = self.tree_incidentes.selection()
        if not seleccion:
            return

        item = self.tree_incidentes.item(seleccion[0])
        valores = item['values']
        incidente_id = valores[0]

        if not self.mongo_repo:
            return

        try:
            # Convertir a ObjectId para búsqueda
            obj_id = ObjectId(incidente_id)

            incidentes = self.mongo_repo.listar_incidentes()
            incidente = None
            for inc in incidentes:
                if str(inc.get('_id')) == incidente_id:
                    incidente = inc
                    break

            if incidente:
                # Habilitar temporalmente el campo ID
                self.entry_incidente_id.config(state=tk.NORMAL, bg="white")
                self.entry_incidente_id.delete(0, tk.END)
                self.entry_incidente_id.insert(0, str(incidente.get('_id', '')))
                self.entry_incidente_id.config(state=tk.DISABLED, bg="#ecf0f1")

                self.entry_remitente.delete(0, tk.END)
                self.entry_remitente.insert(0, incidente.get('remitente', ''))

                self.entry_asunto.delete(0, tk.END)
                self.entry_asunto.insert(0, incidente.get('asunto_original', ''))

                self.txt_cuerpo.delete(1.0, tk.END)
                self.txt_cuerpo.insert(1.0, incidente.get('cuerpo_original', ''))

                self.combo_estado.set(incidente.get('estado', 'nuevo'))

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar incidente: {e}")

    def enviar_pregunta_asistente(self):
        """Envía una pregunta al asistente LLM con mejor manejo de errores y feedback visual."""
        pregunta = self.entry_pregunta_asistente.get().strip()
        if not pregunta:
            return

        # Deshabilitar botón durante el procesamiento
        self.btn_enviar_asistente.config(state=tk.DISABLED, text="⏳ Procesando...")

        # Mostrar pregunta del usuario
        self.chat_asistente.insert(tk.END, f"👤 Tú: {pregunta}\n\n", "usuario")
        self.entry_pregunta_asistente.delete(0, tk.END)
        self.chat_asistente.see(tk.END)

        # Actualizar barra de estado
        self.barra_estado.config(text="Procesando pregunta con LLM...")

        # Usar after para permitir que la UI se actualice antes de procesar
        self.root.after(100, lambda: self._procesar_pregunta_asistente(pregunta))

    def _procesar_pregunta_asistente(self, pregunta):
        """Procesa la pregunta en segundo plano."""
        try:
            if not self.asistente:
                respuesta = "⚠️ Primero debes conectar a MongoDB. Ve a la pestaña 'Panel de Control' y haz clic en 'Conectar MongoDB'."
                self.chat_asistente.insert(tk.END, f"🤖 Asistente: {respuesta}\n\n", "error")
            else:
                # Mostrar indicador de "escribiendo"
                self.chat_asistente.insert(tk.END, "🤖 Asistente: ", "asistente")
                self.chat_asistente.insert(tk.END, "procesando...", "escribiendo")
                self.chat_asistente.see(tk.END)
                self.root.update()

                # Procesar pregunta
                resultado = self.asistente.preguntar(pregunta)

                # Eliminar indicador de "escribiendo"
                self.chat_asistente.delete("end-3l linestart", "end-1l")

                if resultado['exito']:
                    self.chat_asistente.insert(tk.END, resultado['respuesta'] + "\n\n", "asistente")
                else:
                    self.chat_asistente.insert(tk.END, f"❌ Error: {resultado['respuesta']}\n\n", "error")

        except Exception as e:
            self.chat_asistente.insert(tk.END, f"❌ Error inesperado: {str(e)}\n\n", "error")
        finally:
            # Rehabilitar botón
            self.btn_enviar_asistente.config(state=tk.NORMAL, text="📤 Enviar")
            self.chat_asistente.see(tk.END)
            self.barra_estado.config(text="Listo")

    def usar_sugerencia(self, sugerencia):
        """Usa una sugerencia de pregunta."""
        self.entry_pregunta_asistente.delete(0, tk.END)
        self.entry_pregunta_asistente.insert(0, sugerencia)
        self.entry_pregunta_asistente.focus()

    def limpiar_chat_asistente(self):
        """Limpia el chat del asistente y restaura el mensaje inicial."""
        self.chat_asistente.delete(1.0, tk.END)

        # Mensaje inicial
        self.chat_asistente.insert(tk.END, "🤖 Sistema: ¡Hola! Soy tu asistente inteligente de LogiSmart.\n\n", "sistema")
        self.chat_asistente.insert(tk.END, "📍 Puedo ayudarte con:\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Información sobre camiones registrados\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Historial de accesos al terminal\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Incidentes y su estado\n", "sistema")
        self.chat_asistente.insert(tk.END, "   • Riesgos éticos del sistema\n\n", "sistema")

        if self.asistente:
            self.chat_asistente.insert(tk.END, "✅ Conectado a MongoDB - Puedo responder preguntas.\n\n", "sistema")
            self.asistente.limpiar_historial()
        else:
            self.chat_asistente.insert(tk.END, "⚠️ Primero conecta a MongoDB para que pueda acceder a los datos.\n\n", "sistema")

    def _actualizar_estado_asistente_inicial(self):
        """Actualiza el estado inicial del asistente."""
        if hasattr(self, 'lbl_estado_asistente'):
            if self.asistente:
                self.lbl_estado_asistente.config(text="🟢 Conectado a MongoDB", fg="#27ae60")
            else:
                self.lbl_estado_asistente.config(text="🔴 No conectado a MongoDB", fg="#e74c3c")

    # ============================================================
    # MÉTODOS DE GESTIÓN DE CAMIONES
    # ============================================================

    def generar_siguiente_id_camion(self):
        """Genera el siguiente ID de camión automáticamente."""
        if not self.mongo_repo:
            return "CAM-001"

        try:
            camiones = self.mongo_repo.listar_camiones()
            if not camiones:
                return "CAM-001"

            # Extraer números de IDs existentes
            numeros = []
            for camion in camiones:
                camion_id = camion.get('camion_id', '')
                if camion_id.startswith('CAM-'):
                    try:
                        num = int(camion_id[4:])
                        numeros.append(num)
                    except ValueError:
                        pass

            if not numeros:
                return "CAM-001"

            # Encontrar el máximo y sumar 1
            siguiente = max(numeros) + 1
            return f"CAM-{siguiente:03d}"

        except Exception as e:
            print(f"Error generando ID: {e}")
            return "CAM-001"

    def cargar_lista_camiones(self):
        """Carga la lista de camiones desde MongoDB."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        try:
            # Limpiar lista actual
            for item in self.tree_camiones.get_children():
                self.tree_camiones.delete(item)

            # Obtener camiones
            camiones = self.mongo_repo.listar_camiones()

            # Agregar al treeview
            for camion in camiones:
                self.tree_camiones.insert("", "end", values=(
                    camion.get('camion_id', 'N/A'),
                    camion.get('placa', 'N/A'),
                    camion.get('empresa', 'N/A'),
                    "✓" if camion.get('autorizacion', False) else "✗",
                    "✓" if camion.get('certificacion_conductor', False) else "✗",
                    "✓" if camion.get('materiales_peligrosos', False) else "✗"
                ))

            self.barra_estado.config(text=f"Cargados {len(camiones)} camiones")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar camiones: {e}")

    def registrar_camion(self):
        """Registra un nuevo camión en MongoDB con ID automático."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        # Generar ID automático
        camion_id = self.generar_siguiente_id_camion()

        # Validar campos
        placa = self.camiones_entries["entry_placa"].get().strip()
        empresa = self.camiones_entries["entry_empresa"].get().strip()
        peso_max = self.camiones_entries["entry_peso_max"].get().strip()

        if not placa or not empresa:
            messagebox.showwarning("Advertencia", "Placa y Empresa son obligatorios")
            return

        try:
            # Verificar si ya existe
            existente = self.mongo_repo.obtener_camion(camion_id)
            if existente:
                messagebox.showwarning("Advertencia", f"El camión {camion_id} ya existe")
                return

            # Crear camión
            camion = {
                "camion_id": camion_id,
                "placa": placa,
                "empresa": empresa,
                "autorizacion": self.var_autorizacion.get(),
                "certificacion_conductor": self.var_certificacion.get(),
                "materiales_peligrosos": self.var_materiales_peligrosos.get(),
                "peso_maximo": int(peso_max) if peso_max else 5000
            }

            self.mongo_repo.crear_camion(camion)
            messagebox.showinfo("Éxito", f"Camión {camion_id} registrado exitosamente")
            self.limpiar_formulario_camion()
            self.cargar_lista_camiones()

        except ValueError:
            messagebox.showerror("Error", "El peso máximo debe ser un número")
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar camión: {e}")

    def actualizar_camion(self):
        """Actualiza un camión existente."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        camion_id = self.camiones_entries["entry_camion_id"].get().strip()
        if not camion_id:
            messagebox.showwarning("Advertencia", "Seleccione un camión para actualizar")
            return

        try:
            # Verificar si existe
            existente = self.mongo_repo.obtener_camion(camion_id)
            if not existente:
                messagebox.showwarning("Advertencia", f"El camión {camion_id} no existe")
                return

            # Actualizar datos
            actualizacion = {
                "placa": self.camiones_entries["entry_placa"].get().strip(),
                "empresa": self.camiones_entries["entry_empresa"].get().strip(),
                "autorizacion": self.var_autorizacion.get(),
                "certificacion_conductor": self.var_certificacion.get(),
                "materiales_peligrosos": self.var_materiales_peligrosos.get(),
                "peso_maximo": int(self.camiones_entries["entry_peso_max"].get().strip()) if self.camiones_entries["entry_peso_max"].get().strip() else 5000
            }

            self.mongo_repo.actualizar_camion(camion_id, actualizacion)
            messagebox.showinfo("Éxito", f"Camión {camion_id} actualizado exitosamente")
            self.limpiar_formulario_camion()
            self.cargar_lista_camiones()

        except ValueError:
            messagebox.showerror("Error", "El peso máximo debe ser un número")
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar camión: {e}")

    def eliminar_camion(self):
        """Elimina un camión."""
        if not self.mongo_repo:
            messagebox.showwarning("Advertencia", "Primero conecte a MongoDB")
            return

        camion_id = self.camiones_entries["entry_camion_id"].get().strip()
        if not camion_id:
            messagebox.showwarning("Advertencia", "Seleccione un camión para eliminar")
            return

        # Confirmar
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el camión {camion_id}?"):
            return

        try:
            eliminado = self.mongo_repo.eliminar_camion(camion_id)
            if eliminado:
                messagebox.showinfo("Éxito", f"Camión {camion_id} eliminado exitosamente")
                self.limpiar_formulario_camion()
                self.cargar_lista_camiones()
            else:
                messagebox.showwarning("Advertencia", f"No se pudo eliminar el camión {camion_id}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar camión: {e}")

    def limpiar_formulario_camion(self):
        """Limpia el formulario de camiones y genera el siguiente ID."""
        for entry in self.camiones_entries.values():
            entry.delete(0, tk.END)

        # Generar y mostrar el siguiente ID
        siguiente_id = self.generar_siguiente_id_camion()
        self.camiones_entries["entry_camion_id"].config(state=tk.NORMAL)
        self.camiones_entries["entry_camion_id"].insert(0, siguiente_id)
        self.camiones_entries["entry_camion_id"].config(state=tk.DISABLED, bg="#ecf0f1")

        self.var_autorizacion.set(False)
        self.var_certificacion.set(False)
        self.var_materiales_peligrosos.set(False)

    def on_camion_seleccionado(self, event):
        """Carga los datos del camión seleccionado en el formulario."""
        seleccion = self.tree_camiones.selection()
        if not seleccion:
            return

        item = self.tree_camiones.item(seleccion[0])
        valores = item['values']
        camion_id = valores[0]

        if not self.mongo_repo:
            return

        try:
            camion = self.mongo_repo.obtener_camion(camion_id)
            if camion:
                # Habilitar temporalmente el campo ID para edición
                self.camiones_entries["entry_camion_id"].config(state=tk.NORMAL, bg="white")
                self.camiones_entries["entry_camion_id"].delete(0, tk.END)
                self.camiones_entries["entry_camion_id"].insert(0, camion.get('camion_id', ''))
                self.camiones_entries["entry_camion_id"].config(state=tk.DISABLED, bg="#ecf0f1")

                self.camiones_entries["entry_placa"].delete(0, tk.END)
                self.camiones_entries["entry_placa"].insert(0, camion.get('placa', ''))
                self.camiones_entries["entry_empresa"].delete(0, tk.END)
                self.camiones_entries["entry_empresa"].insert(0, camion.get('empresa', ''))
                self.camiones_entries["entry_peso_max"].delete(0, tk.END)
                self.camiones_entries["entry_peso_max"].insert(0, str(camion.get('peso_maximo', '')))

                self.var_autorizacion.set(camion.get('autorizacion', False))
                self.var_certificacion.set(camion.get('certificacion_conductor', False))
                self.var_materiales_peligrosos.set(camion.get('materiales_peligrosos', False))

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar camión: {e}")

    # ============================================================
    # MÉTODOS DE RIESGOS
    # ============================================================

    def actualizar_lista_riesgos(self):
        """Actualiza la lista de riesgos en el Treeview."""
        for item in self.tree_riesgos.get_children():
            self.tree_riesgos.delete(item)

        for id, riesgo in self.matriz_riesgos.listar_riesgos():
            self.tree_riesgos.insert("", "end", values=(
                id, riesgo.modulo[:20], riesgo.categoria, riesgo.nivel, riesgo.puntaje
            ))

    def actualizar_grafica_riesgos(self):
        """Actualiza la gráfica de riesgos."""
        datos = self.matriz_riesgos.obtener_datos_grafica()

        self.ax_riesgos.clear()

        # Gráfica de dispersión
        if datos["dispersion"]:
            x = [d["x"] for d in datos["dispersion"]]
            y = [d["y"] for d in datos["dispersion"]]
            colores = {"crítico": "red", "alto": "orange", "medio": "yellow", "bajo": "green"}
            c = [colores[d["nivel"]] for d in datos["dispersion"]]

            self.ax_riesgos.scatter(x, y, c=c, s=100, alpha=0.6)
            self.ax_riesgos.set_xlabel("Probabilidad")
            self.ax_riesgos.set_ylabel("Impacto")
            self.ax_riesgos.set_title("Matriz de Riesgos")
            self.ax_riesgos.set_xlim(0, 6)
            self.ax_riesgos.set_ylim(0, 6)
            self.ax_riesgos.grid(True)

        self.canvas_riesgos.draw()

    def agregar_riesgo(self):
        """Abre diálogo para agregar un nuevo riesgo."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Riesgo")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        # Campos
        tk.Label(dialog, text="Módulo:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        entry_modulo = tk.Entry(dialog, width=40)
        entry_modulo.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Descripción:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        entry_descripcion = tk.Entry(dialog, width=40)
        entry_descripcion.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(dialog, text="Categoría:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        combo_categoria = ttk.Combobox(dialog, values=["sesgo", "privacidad", "transparencia", "seguridad", "responsabilidad", "otro"], width=37)
        combo_categoria.grid(row=2, column=1, padx=10, pady=5)
        combo_categoria.set("sesgo")

        tk.Label(dialog, text="Probabilidad (1-5):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        entry_prob = tk.Entry(dialog, width=40)
        entry_prob.grid(row=3, column=1, padx=10, pady=5)
        entry_prob.insert(0, "3")

        tk.Label(dialog, text="Impacto (1-5):").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        entry_impacto = tk.Entry(dialog, width=40)
        entry_impacto.grid(row=4, column=1, padx=10, pady=5)
        entry_impacto.insert(0, "3")

        tk.Label(dialog, text="Mitigación:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        txt_mitigacion = scrolledtext.ScrolledText(dialog, height=5, width=40)
        txt_mitigacion.grid(row=5, column=1, padx=10, pady=5)

        def guardar():
            try:
                modulo = entry_modulo.get().strip()
                descripcion = entry_descripcion.get().strip()
                categoria = combo_categoria.get().strip()
                prob = int(entry_prob.get().strip())
                impacto = int(entry_impacto.get().strip())
                mitigacion = txt_mitigacion.get(1.0, tk.END).strip()

                if not modulo or not descripcion:
                    messagebox.showwarning("Advertencia", "Módulo y Descripción son obligatorios")
                    return

                if not 1 <= prob <= 5 or not 1 <= impacto <= 5:
                    messagebox.showwarning("Advertencia", "Probabilidad e Impacto deben estar entre 1 y 5")
                    return

                # Guardar en MongoDB primero si está conectado
                mongo_id = None
                if self.mongo_repo:
                    try:
                        riesgo_dict = {
                            "modulo": modulo,
                            "descripcion": descripcion,
                            "categoria": categoria,
                            "probabilidad": prob,
                            "impacto": impacto,
                            "mitigacion": mitigacion
                        }
                        mongo_id = self.mongo_repo.crear_riesgo_etico(riesgo_dict)
                        print(f"Riesgo guardado en MongoDB con ID: {mongo_id}")
                    except Exception as e:
                        print(f"Error al guardar riesgo en MongoDB: {e}")

                # Guardar en matriz de riesgos (memoria)
                riesgo_id = self.matriz_riesgos.registrar_riesgo(
                    modulo, descripcion, categoria, prob, impacto, mitigacion
                )

                messagebox.showinfo("Éxito", f"Riesgo {riesgo_id} agregado exitosamente")
                self.actualizar_lista_riesgos()
                self.actualizar_grafica_riesgos()
                dialog.destroy()

            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar riesgo: {e}")

        tk.Button(dialog, text="Guardar", command=guardar, bg="#27ae60", fg="white").grid(row=6, column=0, columnspan=2, pady=20)

    def editar_riesgo(self):
        """Edita el riesgo seleccionado."""
        seleccion = self.tree_riesgos.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un riesgo para editar")
            return

        item = self.tree_riesgos.item(seleccion[0])
        valores = item['values']
        riesgo_id = valores[0]

        riesgo = self.matriz_riesgos.obtener_riesgo(riesgo_id)
        if not riesgo:
            messagebox.showerror("Error", "No se encontró el riesgo")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar Riesgo {riesgo_id}")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        # Campos con valores actuales
        tk.Label(dialog, text="Módulo:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        entry_modulo = tk.Entry(dialog, width=40)
        entry_modulo.grid(row=0, column=1, padx=10, pady=5)
        entry_modulo.insert(0, riesgo.modulo)

        tk.Label(dialog, text="Descripción:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        entry_descripcion = tk.Entry(dialog, width=40)
        entry_descripcion.grid(row=1, column=1, padx=10, pady=5)
        entry_descripcion.insert(0, riesgo.descripcion)

        tk.Label(dialog, text="Categoría:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        combo_categoria = ttk.Combobox(dialog, values=["sesgo", "privacidad", "transparencia", "seguridad", "responsabilidad", "otro"], width=37)
        combo_categoria.grid(row=2, column=1, padx=10, pady=5)
        combo_categoria.set(riesgo.categoria)

        tk.Label(dialog, text="Probabilidad (1-5):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        entry_prob = tk.Entry(dialog, width=40)
        entry_prob.grid(row=3, column=1, padx=10, pady=5)
        entry_prob.insert(0, str(riesgo.probabilidad))

        tk.Label(dialog, text="Impacto (1-5):").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        entry_impacto = tk.Entry(dialog, width=40)
        entry_impacto.grid(row=4, column=1, padx=10, pady=5)
        entry_impacto.insert(0, str(riesgo.impacto))

        tk.Label(dialog, text="Mitigación:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        txt_mitigacion = scrolledtext.ScrolledText(dialog, height=5, width=40)
        txt_mitigacion.grid(row=5, column=1, padx=10, pady=5)
        txt_mitigacion.insert(1.0, riesgo.mitigacion)

        def guardar():
            try:
                modulo = entry_modulo.get().strip()
                descripcion = entry_descripcion.get().strip()
                categoria = combo_categoria.get().strip()
                prob = int(entry_prob.get().strip())
                impacto = int(entry_impacto.get().strip())
                mitigacion = txt_mitigacion.get(1.0, tk.END).strip()

                if not modulo or not descripcion:
                    messagebox.showwarning("Advertencia", "Módulo y Descripción son obligatorios")
                    return

                if not 1 <= prob <= 5 or not 1 <= impacto <= 5:
                    messagebox.showwarning("Advertencia", "Probabilidad e Impacto deben estar entre 1 y 5")
                    return

                # Actualizar en matriz de riesgos (memoria)
                self.matriz_riesgos.actualizar_riesgo(
                    riesgo_id,
                    modulo=modulo,
                    descripcion=descripcion,
                    categoria=categoria,
                    probabilidad=prob,
                    impacto=impacto,
                    mitigacion=mitigacion
                )

                # Actualizar en MongoDB si está conectado
                if self.mongo_repo:
                    try:
                        # Buscar el riesgo en MongoDB por riesgo_id
                        riesgos_mongo = self.mongo_repo.listar_riesgos()
                        mongo_id = None
                        for r in riesgos_mongo:
                            if r.get('riesgo_id') == riesgo_id:
                                mongo_id = r.get('_id')
                                break

                        if mongo_id:
                            # Actualizar en MongoDB
                            from bson import ObjectId
                            actualizacion = {
                                "modulo": modulo,
                                "descripcion": descripcion,
                                "categoria": categoria,
                                "probabilidad": prob,
                                "impacto": impacto,
                                "mitigacion": mitigacion
                            }
                            self.mongo_repo.actualizar_riesgo(mongo_id, actualizacion)
                    except Exception as e:
                        print(f"Error al actualizar riesgo en MongoDB: {e}")

                messagebox.showinfo("Éxito", f"Riesgo {riesgo_id} actualizado exitosamente")
                self.actualizar_lista_riesgos()
                self.actualizar_grafica_riesgos()
                dialog.destroy()

            except ValueError as e:
                messagebox.showerror("Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar riesgo: {e}")

        tk.Button(dialog, text="Guardar", command=guardar, bg="#3498db", fg="white").grid(row=6, column=0, columnspan=2, pady=20)

    def eliminar_riesgo(self):
        """Elimina el riesgo seleccionado."""
        seleccion = self.tree_riesgos.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un riesgo para eliminar")
            return

        item = self.tree_riesgos.item(seleccion[0])
        valores = item['values']
        riesgo_id = valores[0]

        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el riesgo {riesgo_id}?"):
            return

        # Eliminar de MongoDB si está conectado
        if self.mongo_repo:
            try:
                # Buscar el riesgo en MongoDB por riesgo_id
                riesgos_mongo = self.mongo_repo.listar_riesgos()
                mongo_id = None
                for r in riesgos_mongo:
                    if r.get('riesgo_id') == riesgo_id:
                        mongo_id = r.get('_id')
                        break

                if mongo_id:
                    from bson import ObjectId
                    self.mongo_repo.eliminar_riesgo(mongo_id)
            except Exception as e:
                print(f"Error al eliminar riesgo de MongoDB: {e}")

        # Eliminar de matriz de riesgos (memoria)
        if self.matriz_riesgos.eliminar_riesgo(riesgo_id):
            messagebox.showinfo("Éxito", f"Riesgo {riesgo_id} eliminado exitosamente")
            self.actualizar_lista_riesgos()
            self.actualizar_grafica_riesgos()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el riesgo")

    def guardar_configuracion(self):
        """Guarda la configuración."""
        config.ollama.model = self.entry_modelo_ollama.get()
        config.ollama.host = self.entry_host_ollama.get()
        config.mongo.host = self.entry_mongo_host.get()
        config.mongo.port = int(self.entry_mongo_port.get())
        config.mongo.database = self.entry_mongo_db.get()
        config.modo_simulacion = self.var_simulacion.get()

        messagebox.showinfo("Éxito", "Configuración guardada")
        self.barra_estado.config(text="Configuración guardada")


def main():
    """Punto de entrada principal."""
    root = tk.Tk()
    app = LogiSmartGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
