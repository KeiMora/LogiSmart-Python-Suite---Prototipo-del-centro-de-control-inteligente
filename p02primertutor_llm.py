#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
============================================================
PRACTICA 2 - TUTOR INTELIGENTE CON LLM
============================================================

Objetivo:
Crear un asistente educativo especializado utilizando
un modelo de lenguaje LLM ejecutado mediante Ollama.

Modelo:
llama3.2

Características:
- Interfaz gráfica con Tkinter
- Historial de conversación
- Integración con Ollama
- Configuración del comportamiento del tutor
- Indicador de conexión
- Botón para limpiar conversación
- Envío mediante botón o tecla Enter
- Manejo de errores
- Resumen del historial de la sesión
============================================================
"""

# ============================================================
# 1. IMPORTACIONES
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import ollama
import threading


# ============================================================
# 2. CONFIGURACIÓN
# ============================================================

MODELO = "llama3.2"

mensaje_sistema = """
Eres un profesor especializado en Inteligencia Artificial.

Tu función es ayudar a estudiantes universitarios.

Debes:

1. Explicar los conceptos de manera clara.
2. Utilizar ejemplos sencillos.
3. Explicar los procedimientos paso a paso.
4. Evitar respuestas excesivamente técnicas cuando
   el estudiante sea principiante.
5. Cuando sea posible, proporcionar ejemplos en Python.
6. Si el estudiante comete un error, explicarle
   cómo corregirlo.
7. No proporcionar únicamente la respuesta final.
8. Explicar los conceptos necesarios para comprender
   el problema.
9. Mantener un tono amable y educativo.
10. Adaptar la explicación al nivel del estudiante.
"""


# ============================================================
# 3. HISTORIAL
# ============================================================

mensajes = [
    {
        "role": "system",
        "content": mensaje_sistema
    }
]


# ============================================================
# 4. COLORES
# ============================================================

COLOR_FONDO = "#F4F6F8"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARIO = "#2563EB"
COLOR_PRIMARIO_HOVER = "#1D4ED8"
COLOR_TEXTO = "#1F2937"
COLOR_SECUNDARIO = "#6B7280"
COLOR_ESTUDIANTE = "#DBEAFE"
COLOR_TUTOR = "#E8F5E9"
COLOR_ERROR = "#FEE2E2"
COLOR_BORDE = "#E5E7EB"


# ============================================================
# 5. VENTANA PRINCIPAL
# ============================================================

ventana = tk.Tk()

ventana.title("Tutor Inteligente con LLM")
ventana.geometry("1050x700")
ventana.minsize(850, 600)
ventana.configure(bg=COLOR_FONDO)


# ============================================================
# 6. ESTILOS
# ============================================================

estilo = ttk.Style()

try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "TButton",
    font=("Arial", 11),
    padding=(12, 8)
)

estilo.configure(
    "Titulo.TLabel",
    background=COLOR_PANEL,
    foreground=COLOR_TEXTO,
    font=("Arial", 22, "bold")
)

estilo.configure(
    "Subtitulo.TLabel",
    background=COLOR_PANEL,
    foreground=COLOR_SECUNDARIO,
    font=("Arial", 10)
)

estilo.configure(
    "Panel.TFrame",
    background=COLOR_PANEL
)


# ============================================================
# 7. FUNCIONES
# ============================================================

def agregar_mensaje_usuario(texto):
    """
    Muestra el mensaje del estudiante en el área de conversación.
    """

    chat.config(state="normal")

    chat.insert(
        "end",
        "\nESTUDIANTE\n",
        "usuario_titulo"
    )

    chat.insert(
        "end",
        texto + "\n",
        "usuario"
    )

    chat.config(state="disabled")

    chat.see("end")


def agregar_mensaje_tutor(texto):
    """
    Muestra la respuesta del tutor.
    """

    chat.config(state="normal")

    chat.insert(
        "end",
        "\nTUTOR IA\n",
        "tutor_titulo"
    )

    chat.insert(
        "end",
        texto + "\n",
        "tutor"
    )

    chat.config(state="disabled")

    chat.see("end")


def agregar_mensaje_error(texto):
    """
    Muestra un mensaje de error.
    """

    chat.config(state="normal")

    chat.insert(
        "end",
        "\nERROR\n",
        "error_titulo"
    )

    chat.insert(
        "end",
        texto + "\n",
        "error"
    )

    chat.config(state="disabled")

    chat.see("end")


def actualizar_estado(texto, conectado=False):
    """
    Actualiza el indicador de estado de Ollama.
    """

    if conectado:
        estado.config(
            text="● Ollama conectado",
            foreground="#16A34A"
        )
    else:
        estado.config(
            text=texto,
            foreground="#DC2626"
        )


def verificar_ollama():
    """
    Comprueba si Ollama está disponible y si el modelo
    seleccionado está instalado.
    """

    try:

        modelos = ollama.list()

        nombres = []

        for modelo in modelos.get("models", []):
            nombre = modelo.get("name", "")
            nombres.append(nombre)

        modelo_encontrado = any(
            nombre.startswith(MODELO)
            for nombre in nombres
        )

        if modelo_encontrado:

            actualizar_estado(
                "● Ollama conectado",
                True
            )

            estado_modelo.config(
                text=f"Modelo: {MODELO}"
            )

        else:

            actualizar_estado(
                "● Ollama conectado, modelo no encontrado",
                False
            )

            estado_modelo.config(
                text=f"Modelo: {MODELO} no instalado"
            )

    except Exception:

        actualizar_estado(
            "● Ollama no disponible",
            False
        )

        estado_modelo.config(
            text="Verifica que Ollama esté ejecutándose"
        )


def limpiar_conversacion():
    """
    Elimina el historial de conversación y comienza
    una nueva sesión.
    """

    global mensajes

    respuesta = messagebox.askyesno(
        "Nueva conversación",
        "¿Deseas borrar el historial de esta conversación?"
    )

    if not respuesta:
        return

    mensajes = [
        {
            "role": "system",
            "content": mensaje_sistema
        }
    ]

    chat.config(state="normal")
    chat.delete("1.0", "end")
    chat.config(state="disabled")

    chat.config(state="normal")

    chat.insert(
        "end",
        "TUTOR IA\n",
        "tutor_titulo"
    )

    chat.insert(
        "end",
        "¡Hola! Soy tu tutor de Inteligencia Artificial.\n"
        "Puedes preguntarme sobre Python, IA, LLM, "
        "lógica, bases de datos o programación.\n\n",
        "tutor"
    )

    chat.config(state="disabled")

    chat.see("end")


def mostrar_resumen():
    """
    Genera un resumen de la conversación actual utilizando
    el mismo LLM.
    """

    if len(mensajes) <= 1:

        messagebox.showinfo(
            "Historial",
            "Todavía no existe suficiente conversación "
            "para generar un resumen."
        )

        return

    pregunta_resumen = """
Realiza un breve resumen de la sesión de estudio actual.

Indica:

1. Temas que preguntó el estudiante.
2. Conceptos principales explicados.
3. Qué conocimientos debería reforzar.
4. Una recomendación breve para continuar estudiando.

Utiliza únicamente la información contenida en el historial.
"""

    mensajes_resumen = mensajes.copy()

    mensajes_resumen.append(
        {
            "role": "user",
            "content": pregunta_resumen
        }
    )

    boton_resumen.config(
        state="disabled"
    )

    estado.config(
        text="● Generando resumen...",
        foreground="#CA8A04"
    )

    def procesar():

        try:

            respuesta = ollama.chat(
                model=MODELO,
                messages=mensajes_resumen
            )

            contenido = respuesta["message"]["content"]

            ventana.after(
                0,
                lambda: mostrar_resumen_resultado(contenido)
            )

        except Exception as error:

            ventana.after(
                0,
                lambda: mostrar_error_resumen(str(error))
            )

    threading.Thread(
        target=procesar,
        daemon=True
    ).start()


def mostrar_resumen_resultado(texto):
    """
    Muestra el resumen generado.
    """

    boton_resumen.config(
        state="normal"
    )

    actualizar_estado(
        "● Ollama conectado",
        True
    )

    ventana_resumen = tk.Toplevel(ventana)

    ventana_resumen.title("Resumen de la sesión")
    ventana_resumen.geometry("650x500")
    ventana_resumen.configure(
        bg=COLOR_FONDO
    )

    titulo = tk.Label(
        ventana_resumen,
        text=" Resumen de tu sesión",
        bg=COLOR_FONDO,
        fg=COLOR_TEXTO,
        font=("Arial", 18, "bold")
    )

    titulo.pack(
        pady=(20, 10)
    )

    texto_resumen = tk.Text(
        ventana_resumen,
        wrap="word",
        font=("Arial", 11),
        bg=COLOR_PANEL,
        fg=COLOR_TEXTO,
        relief="flat",
        padx=20,
        pady=20
    )

    texto_resumen.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    texto_resumen.insert(
        "1.0",
        texto
    )

    texto_resumen.config(
        state="disabled"
    )


def mostrar_error_resumen(error):
    """
    Muestra un error relacionado con el resumen.
    """

    boton_resumen.config(
        state="normal"
    )

    actualizar_estado(
        "● Error de conexión",
        False
    )

    messagebox.showerror(
        "Error",
        "No fue posible generar el resumen.\n\n"
        + error
    )


def enviar_pregunta(event=None):
    """
    Obtiene la pregunta y la envía al LLM.
    """

    pregunta = entrada.get("1.0", "end").strip()

    if not pregunta:
        return

    # Agregar pregunta al historial
    mensajes.append(
        {
            "role": "user",
            "content": pregunta
        }
    )

    # Mostrar pregunta
    agregar_mensaje_usuario(
        pregunta
    )

    # Limpiar entrada
    entrada.delete(
        "1.0",
        "end"
    )

    # Desactivar controles
    boton_enviar.config(
        state="disabled"
    )

    entrada.config(
        state="disabled"
    )

    boton_resumen.config(
        state="disabled"
    )

    actualizar_estado(
        "● El tutor está pensando...",
        False
    )

    # Mostrar indicador
    indicador.config(
        text="Generando respuesta..."
    )

    # Ejecutar Ollama en segundo plano
    hilo = threading.Thread(
        target=consultar_ollama,
        daemon=True
    )

    hilo.start()


def consultar_ollama():
    """
    Realiza la consulta al modelo Ollama.
    """

    try:

        respuesta = ollama.chat(
            model=MODELO,
            messages=mensajes
        )

        contenido = respuesta["message"]["content"]

        ventana.after(
            0,
            lambda: procesar_respuesta(contenido)
        )

    except Exception as error:

        ventana.after(
            0,
            lambda: procesar_error(str(error))
        )


def procesar_respuesta(contenido):
    """
    Procesa la respuesta recibida.
    """

    mensajes.append(
        {
            "role": "assistant",
            "content": contenido
        }
    )

    agregar_mensaje_tutor(
        contenido
    )

    boton_enviar.config(
        state="normal"
    )

    entrada.config(
        state="normal"
    )

    boton_resumen.config(
        state="normal"
    )

    entrada.focus()

    indicador.config(
        text="Listo para responder"
    )

    actualizar_estado(
        "● Ollama conectado",
        True
    )


def procesar_error(error):
    """
    Procesa errores de comunicación con Ollama.
    """

    # Eliminar pregunta del historial porque no fue procesada
    if len(mensajes) > 1 and mensajes[-1]["role"] == "user":
        mensajes.pop()

    agregar_mensaje_error(
        "No fue posible comunicarse con Ollama.\n\n"
        "Verifica que:\n"
        "• Ollama esté ejecutándose.\n"
        f"• El modelo '{MODELO}' esté instalado.\n"
        "• La conexión local esté disponible.\n\n"
        f"Detalle: {error}"
    )

    boton_enviar.config(
        state="normal"
    )

    entrada.config(
        state="normal"
    )

    boton_resumen.config(
        state="normal"
    )

    entrada.focus()

    indicador.config(
        text="Error al consultar el modelo"
    )

    actualizar_estado(
        "● Ollama no disponible",
        False
    )


def insertar_ejemplo():
    """
    Inserta una pregunta de ejemplo.
    """

    entrada.delete(
        "1.0",
        "end"
    )

    entrada.insert(
        "1.0",
        "¿Qué es un modelo de lenguaje LLM y cómo funciona?"
    )

    entrada.focus()


# ============================================================
# 8. ENCABEZADO
# ============================================================

encabezado = tk.Frame(
    ventana,
    bg=COLOR_PANEL,
    height=90
)

encabezado.pack(
    fill="x"
)

encabezado.pack_propagate(False)


# Icono
icono = tk.Label(
    encabezado,
    bg=COLOR_PANEL,
    fg=COLOR_PRIMARIO,
    font=("Arial", 32)
)

icono.pack(
    side="left",
    padx=(25, 10)
)


# Contenedor del título
contenedor_titulo = tk.Frame(
    encabezado,
    bg=COLOR_PANEL
)

contenedor_titulo.pack(
    side="left",
    pady=15
)


titulo = ttk.Label(
    contenedor_titulo,
    text="Tutor Inteligente con LLM",
    style="Titulo.TLabel"
)

titulo.pack(
    anchor="w"
)


subtitulo = ttk.Label(
    contenedor_titulo,
    text="Asistente educativo basado en inteligencia artificial",
    style="Subtitulo.TLabel"
)

subtitulo.pack(
    anchor="w"
)


# ============================================================
# 9. ESTADO
# ============================================================

panel_estado = tk.Frame(
    encabezado,
    bg=COLOR_PANEL
)

panel_estado.pack(
    side="right",
    padx=25
)


estado = tk.Label(
    panel_estado,
    text="● Comprobando Ollama...",
    bg=COLOR_PANEL,
    fg="#CA8A04",
    font=("Arial", 10, "bold")
)

estado.pack(
    anchor="e"
)


estado_modelo = tk.Label(
    panel_estado,
    text=f"Modelo: {MODELO}",
    bg=COLOR_PANEL,
    fg=COLOR_SECUNDARIO,
    font=("Arial", 9)
)

estado_modelo.pack(
    anchor="e",
    pady=(3, 0)
)


# ============================================================
# 10. CONTENEDOR PRINCIPAL
# ============================================================

contenedor = tk.Frame(
    ventana,
    bg=COLOR_FONDO
)

contenedor.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)


# ============================================================
# 11. PANEL LATERAL
# ============================================================

panel_lateral = tk.Frame(
    contenedor,
    bg=COLOR_PANEL,
    width=220,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)

panel_lateral.pack(
    side="left",
    fill="y",
    padx=(0, 15)
)

panel_lateral.pack_propagate(False)


label_menu = tk.Label(
    panel_lateral,
    text="HERRAMIENTAS",
    bg=COLOR_PANEL,
    fg=COLOR_SECUNDARIO,
    font=("Arial", 9, "bold")
)

label_menu.pack(
    anchor="w",
    padx=20,
    pady=(25, 15)
)


# Botón nueva conversación
boton_nueva = tk.Button(
    panel_lateral,
    text="＋  Nueva conversación",
    bg=COLOR_PRIMARIO,
    fg="white",
    activebackground=COLOR_PRIMARIO_HOVER,
    activeforeground="white",
    font=("Arial", 10, "bold"),
    relief="flat",
    cursor="hand2",
    command=limpiar_conversacion
)

boton_nueva.pack(
    fill="x",
    padx=15,
    pady=5
)


# Botón resumen
boton_resumen = tk.Button(
    panel_lateral,
    text="  Resumen de sesión",
    bg=COLOR_PANEL,
    fg=COLOR_TEXTO,
    activebackground=COLOR_FONDO,
    font=("Arial", 10),
    relief="flat",
    cursor="hand2",
    command=mostrar_resumen
)

boton_resumen.pack(
    fill="x",
    padx=15,
    pady=5
)


# Separador
tk.Frame(
    panel_lateral,
    bg=COLOR_BORDE,
    height=1
).pack(
    fill="x",
    padx=15,
    pady=20
)


label_info = tk.Label(
    panel_lateral,
    text="ACERCA DEL TUTOR",
    bg=COLOR_PANEL,
    fg=COLOR_SECUNDARIO,
    font=("Arial", 9, "bold")
)

label_info.pack(
    anchor="w",
    padx=20,
    pady=(0, 10)
)


info = tk.Label(
    panel_lateral,
    text=(
        "Modelo local:\n"
        f"{MODELO}\n\n"
        "Especialidad:\n"
        "Inteligencia Artificial\n\n"
        "Tecnología:\n"
        "Ollama + Python\n\n"
        "El historial se mantiene\n"
        "durante la sesión."
    ),
    bg=COLOR_PANEL,
    fg=COLOR_TEXTO,
    justify="left",
    font=("Arial", 9),
    wraplength=180
)

info.pack(
    anchor="w",
    padx=20
)


# ============================================================
# 12. PANEL DEL CHAT
# ============================================================

panel_chat = tk.Frame(
    contenedor,
    bg=COLOR_PANEL,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)

panel_chat.pack(
    side="right",
    fill="both",
    expand=True
)


# ============================================================
# 13. TÍTULO DEL CHAT
# ============================================================

cabecera_chat = tk.Frame(
    panel_chat,
    bg=COLOR_PANEL,
    height=50
)

cabecera_chat.pack(
    fill="x"
)

cabecera_chat.pack_propagate(False)


label_chat = tk.Label(
    cabecera_chat,
    text=" Conversación",
    bg=COLOR_PANEL,
    fg=COLOR_TEXTO,
    font=("Arial", 13, "bold")
)

label_chat.pack(
    side="left",
    padx=20,
    pady=12
)


# ============================================================
# 14. ÁREA DE CONVERSACIÓN
# ============================================================

contenedor_chat = tk.Frame(
    panel_chat,
    bg=COLOR_PANEL
)

contenedor_chat.pack(
    fill="both",
    expand=True,
    padx=15
)


scroll = ttk.Scrollbar(
    contenedor_chat,
    orient="vertical"
)

scroll.pack(
    side="right",
    fill="y"
)


chat = tk.Text(
    contenedor_chat,
    wrap="word",
    font=("Arial", 11),
    bg="#FAFAFA",
    fg=COLOR_TEXTO,
    relief="flat",
    padx=20,
    pady=15,
    spacing1=4,
    spacing3=8,
    yscrollcommand=scroll.set
)

chat.pack(
    side="left",
    fill="both",
    expand=True
)

scroll.config(
    command=chat.yview
)


# ============================================================
# 15. CONFIGURAR ETIQUETAS DEL CHAT
# ============================================================

chat.tag_configure(
    "usuario_titulo",
    foreground=COLOR_PRIMARIO,
    font=("Arial", 10, "bold")
)

chat.tag_configure(
    "usuario",
    foreground=COLOR_TEXTO,
    background=COLOR_ESTUDIANTE,
    lmargin1=10,
    lmargin2=10,
    rmargin=10
)

chat.tag_configure(
    "tutor_titulo",
    foreground="#15803D",
    font=("Arial", 10, "bold")
)

chat.tag_configure(
    "tutor",
    foreground=COLOR_TEXTO,
    background=COLOR_TUTOR,
    lmargin1=10,
    lmargin2=10,
    rmargin=10
)

chat.tag_configure(
    "error_titulo",
    foreground="#B91C1C",
    font=("Arial", 10, "bold")
)

chat.tag_configure(
    "error",
    foreground="#7F1D1D",
    background=COLOR_ERROR,
    lmargin1=10,
    lmargin2=10,
    rmargin=10
)


# ============================================================
# 16. MENSAJE INICIAL
# ============================================================

chat.config(
    state="normal"
)

chat.insert(
    "end",
    "TUTOR IA\n",
    "tutor_titulo"
)

chat.insert(
    "end",
    "¡Hola! 👋\n\n"
    "Soy tu tutor de Inteligencia Artificial. "
    "Puedo ayudarte a comprender conceptos, resolver "
    "ejercicios y aprender paso a paso.\n\n"
    "Puedes preguntarme, por ejemplo:\n"
    "• ¿Qué es un LLM?\n"
    "• ¿Cómo funciona una red neuronal?\n"
    "• Explícame Python desde cero.\n"
    "• ¿Qué es la lógica proposicional?\n\n"
    "Escribe tu pregunta en la parte inferior para comenzar.",
    "tutor"
)

chat.config(
    state="disabled"
)


# ============================================================
# 17. ÁREA DE ENTRADA
# ============================================================

panel_entrada = tk.Frame(
    panel_chat,
    bg=COLOR_PANEL
)

panel_entrada.pack(
    fill="x",
    padx=15,
    pady=15
)


# Indicador
indicador = tk.Label(
    panel_entrada,
    text="Listo para responder",
    bg=COLOR_PANEL,
    fg=COLOR_SECUNDARIO,
    font=("Arial", 9)
)

indicador.pack(
    anchor="w",
    padx=5,
    pady=(0, 5)
)


# Contenedor entrada + botón
fila_entrada = tk.Frame(
    panel_entrada,
    bg=COLOR_PANEL
)

fila_entrada.pack(
    fill="x"
)


entrada = tk.Text(
    fila_entrada,
    height=3,
    wrap="word",
    font=("Arial", 11),
    bg="#F9FAFB",
    fg=COLOR_TEXTO,
    relief="flat",
    highlightbackground=COLOR_BORDE,
    highlightthickness=1,
    padx=12,
    pady=10
)

entrada.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 10)
)


boton_enviar = tk.Button(
    fila_entrada,
    text="➤\nEnviar",
    bg=COLOR_PRIMARIO,
    fg="white",
    activebackground=COLOR_PRIMARIO_HOVER,
    activeforeground="white",
    font=("Arial", 10, "bold"),
    relief="flat",
    cursor="hand2",
    width=9,
    command=enviar_pregunta
)

boton_enviar.pack(
    side="right",
    fill="y"
)


# ============================================================
# 18. TEXTO DE AYUDA
# ============================================================

ayuda = tk.Label(
    panel_entrada,
    text="Presiona Enter para enviar • Shift + Enter para una nueva línea",
    bg=COLOR_PANEL,
    fg="black",
    font=("Arial", 8)
)

ayuda.pack(
    anchor="w",
    padx=5,
    pady=(5, 0)
)


# ============================================================
# 19. ATAJOS DEL TECLADO
# ============================================================

def tecla_enter(event):
    """
    Enter envía el mensaje.
    Shift + Enter permite escribir una nueva línea.
    """

    if event.state & 0x0001:
        return

    enviar_pregunta()

    return "break"


entrada.bind(
    "<Return>",
    tecla_enter
)


# ============================================================
# 20. INICIAR
# ============================================================

ventana.after(
    500,
    verificar_ollama
)

entrada.focus()

ventana.mainloop()