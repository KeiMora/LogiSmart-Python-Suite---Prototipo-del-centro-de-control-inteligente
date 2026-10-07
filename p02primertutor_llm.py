# ============================================================
# PRACTICA 2
# TUTOR INTELIGENTE CON LLM - VERSIÓN CON GUI
# ============================================================
#
# Objetivo:
# Crear un asistente especializado utilizando
# un modelo de lenguaje LLM ejecutado mediante Ollama.
#
# Modelo:
# llama3.2
#
# ============================================================


# ------------------------------------------------------------
# 1. IMPORTAR LAS BIBLIOTECAS
# ------------------------------------------------------------

import ollama
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime


# ------------------------------------------------------------
# 2. CONFIGURACIÓN DEL MODELO
# ------------------------------------------------------------

MODELO = "llama3.2"


# ------------------------------------------------------------
# 3. CONFIGURACIÓN DEL SISTEMA
# ------------------------------------------------------------
#
# El mensaje "system" establece el comportamiento general
# que queremos que tenga nuestro asistente.
#
# ------------------------------------------------------------

mensaje_sistema = """
Eres un asistente financiero especializado en inversiones
y planificación de presupuesto personal.

Tu función es ayudar a personas a tomar decisiones financieras
informadas.

Debes:

1. Explicar conceptos financieros de manera clara y accesible.
2. Utilizar ejemplos prácticos del día a día.
3. Explicar los cálculos paso a paso cuando sea necesario.
4. Evitar jerga técnica excesiva cuando el usuario sea principiante.
5. Cuando sea posible, proporcionar ejemplos de cálculos simples.
6. Si el usuario comete un error en su razonamiento financiero,
   explicarle cómo corregirlo de forma constructiva.
7. No proporcionar únicamente la respuesta final; guía al usuario
   para que entienda el proceso.
8. Explicar el razonamiento y los conceptos necesarios
   para comprender la situación financiera.
9. Ser prudente: recuerda que tus sugerencias son educativas
   y no sustituyen el consejo de un profesional certificado.
"""


# ------------------------------------------------------------
# 4. CLASE DE LA INTERFAZ GRÁFICA
# ------------------------------------------------------------

class TutorInteligenteGUI:
    """Interfaz gráfica para el asistente financiero con LLM."""

    def __init__(self, root):
        self.root = root
        self.root.title("Asistente Financiero Inteligente")
        self.root.geometry("800x600")

        # Historial de la conversación
        self.mensajes = [
            {
                "role": "system",
                "content": mensaje_sistema
            }
        ]

        # Contador de intercambios
        self.contador_mensajes = 0

        # Configurar la interfaz
        self._configurar_interfaz()

    def _configurar_interfaz(self):
        """Configura todos los componentes de la interfaz gráfica."""

        # ----------------------------------------------------
        # Encabezado
        # ----------------------------------------------------
        encabezado = tk.Frame(self.root, bg="#2c3e50", pady=10)
        encabezado.pack(fill=tk.X)

        titulo = tk.Label(
            encabezado,
            text="Asistente Financiero Inteligente",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        titulo.pack()

        modelo_label = tk.Label(
            encabezado,
            text=f"Modelo: {MODELO}",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#bdc3c7"
        )
        modelo_label.pack()

        # ----------------------------------------------------
        # Área de chat (historial)
        # ----------------------------------------------------
        chat_frame = tk.Frame(self.root, padx=10, pady=10)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            chat_frame,
            text="Historial de conversación:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W)

        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            height=15
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=5)

        # Configurar etiquetas para diferenciar usuario y asistente
        self.chat_area.tag_config("usuario", foreground="#2980b9", font=("Arial", 11, "bold"))
        self.chat_area.tag_config("asistente", foreground="#27ae60", font=("Arial", 11, "bold"))
        self.chat_area.tag_config("sistema", foreground="#7f8c8d", font=("Arial", 9, "italic"))

        # Mostrar mensaje inicial del sistema
        self._agregar_mensaje_chat("Sistema", "¡Hola! Soy tu asistente financiero. ¿En qué puedo ayudarte hoy?", "sistema")

        # ----------------------------------------------------
        # Área de entrada
        # ----------------------------------------------------
        entrada_frame = tk.Frame(self.root, padx=10, pady=10)
        entrada_frame.pack(fill=tk.X)

        tk.Label(
            entrada_frame,
            text="Tu pregunta:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W)

        self.entrada = tk.Entry(
            entrada_frame,
            font=("Arial", 11)
        )
        self.entrada.pack(fill=tk.X, pady=5)
        self.entrada.bind("<Return>", lambda e: self.enviar_pregunta())

        # ----------------------------------------------------
        # Botones
        # ----------------------------------------------------
        botones_frame = tk.Frame(self.root, padx=10, pady=5)
        botones_frame.pack(fill=tk.X)

        tk.Button(
            botones_frame,
            text="Enviar",
            command=self.enviar_pregunta,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            botones_frame,
            text="Resumen del Historial",
            command=self.mostrar_resumen,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=18
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            botones_frame,
            text="Limpiar Chat",
            command=self.limpiar_chat,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            botones_frame,
            text="Salir",
            command=self.salir,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=8
        ).pack(side=tk.RIGHT, padx=5)

        # Barra de estado
        self.barra_estado = tk.Label(
            self.root,
            text="Listo",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.barra_estado.pack(fill=tk.X, side=tk.BOTTOM)

    def _agregar_mensaje_chat(self, rol, contenido, tag):
        """Agrega un mensaje al área de chat con formato."""
        self.chat_area.insert(tk.END, f"{rol}: ", tag)
        self.chat_area.insert(tk.END, f"{contenido}\n\n")
        self.chat_area.see(tk.END)

    def enviar_pregunta(self):
        """Envía la pregunta del usuario al LLM y muestra la respuesta."""
        pregunta = self.entrada.get().strip()

        if not pregunta:
            messagebox.showwarning("Advertencia", "Por favor escribe una pregunta.")
            return

        # Agregar pregunta al historial
        self.mensajes.append({
            "role": "user",
            "content": pregunta
        })

        # Mostrar pregunta en el chat
        self._agregar_mensaje_chat("Tú", pregunta, "usuario")
        self.entrada.delete(0, tk.END)
        self.barra_estado.config(text="Procesando...")
        self.root.update()

        try:
            # Enviar al LLM
            respuesta = ollama.chat(
                model=MODELO,
                messages=self.mensajes
            )

            contenido = respuesta["message"]["content"]

            # Guardar respuesta en el historial
            self.mensajes.append({
                "role": "assistant",
                "content": contenido
            })

            # Mostrar respuesta en el chat
            self._agregar_mensaje_chat("Asistente", contenido, "asistente")
            self.contador_mensajes += 1
            self.barra_estado.config(text=f"Listo - Mensajes: {self.contador_mensajes}")

        except Exception as error:
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar con el LLM:\n{error}\n\nVerifica que Ollama esté ejecutándose."
            )
            # Eliminar la pregunta del historial
            self.mensajes.pop()
            self.barra_estado.config(text="Error de conexión")

    def mostrar_resumen(self):
        """Muestra un resumen del historial de conversación."""
        if self.contador_mensajes == 0:
            messagebox.showinfo("Resumen", "No hay mensajes en el historial aún.")
            return

        # Contar tipos de mensajes
        mensajes_usuario = sum(1 for m in self.mensajes if m["role"] == "user")
        mensajes_asistente = sum(1 for m in self.mensajes if m["role"] == "assistant")

        # Calcular longitud promedio de las respuestas
        longitudes = [len(m["content"]) for m in self.mensajes if m["role"] == "assistant"]
        promedio = sum(longitudes) / len(longitudes) if longitudes else 0

        resumen = f"""
RESUMEN DE LA SESIÓN
{'=' * 40}

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Estadísticas:
- Preguntas realizadas: {mensajes_usuario}
- Respuestas del asistente: {mensajes_asistente}
- Longitud promedio de respuestas: {promedio:.0f} caracteres

Temas principales:
- Esta conversación ha cubrido {mensajes_usuario} intercambios
- El asistente ha proporcionado {mensajes_asistente} respuestas
- Longitud total del historial: {len(str(self.mensajes))} caracteres

Para ver el historial completo, revisa el área de chat.
"""

        # Crear ventana de resumen
        ventana_resumen = tk.Toplevel(self.root)
        ventana_resumen.title("Resumen del Historial")
        ventana_resumen.geometry("500x400")

        texto_resumen = scrolledtext.ScrolledText(
            ventana_resumen,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        texto_resumen.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        texto_resumen.insert(tk.END, resumen)
        texto_resumen.config(state=tk.DISABLED)

    def limpiar_chat(self):
        """Limpia el área de chat pero mantiene el historial en memoria."""
        if messagebox.askyesno("Confirmar", "¿Deseas limpiar el área de chat?"):
            self.chat_area.delete(1.0, tk.END)
            self._agregar_mensaje_chat("Sistema", "Chat limpiado. El historial se mantiene en memoria.", "sistema")

    def salir(self):
        """Cierra la aplicación."""
        if messagebox.askyesno("Salir", "¿Deseas salir del asistente?"):
            self.root.destroy()


# ------------------------------------------------------------
# 5. EJECUCIÓN DE LA APLICACIÓN
# ------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = TutorInteligenteGUI(root)
    root.mainloop()


#       SYSTEM
#         │
#         ▼
#    Comportamiento
#         │
#         ▼
# USER ────────► LLM
#         │
#         ▼
#      ASSISTANT