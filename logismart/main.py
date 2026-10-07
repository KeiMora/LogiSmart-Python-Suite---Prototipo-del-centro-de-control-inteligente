#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada principal para la aplicación LogiSmart.

Uso:
    python main.py              - Inicia la interfaz gráfica
    python main.py --demo      - Ejecuta demostración por consola
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Verificar dependencias
try:
    import pymongo
    import ollama
    import pydantic
    import matplotlib
except ImportError as e:
    print(f"Error: Falta dependencia: {e}")
    print("Instale las dependencias con: pip install pymongo ollama pydantic matplotlib")
    sys.exit(1)

from ui.main_window import LogiSmartGUI
from logic.motor_reglas import MotorReglas
from logic.clasificador_hibrido import ClasificadorHibrido
from logic.matriz_riesgos import MatrizRiesgos


def demo_consola():
    """Ejecuta una demostración por consola."""
    print("=" * 60)
    print("LogiSmart - Demostración por Consola")
    print("=" * 60)

    # Demo motor de reglas
    print("\n1. Motor de Reglas")
    print("-" * 40)
    motor = MotorReglas()
    resultado = motor.evaluar_camion(P=True, Q=False, R=False, S=True)
    print(f"Resultado: {resultado['decision_final']}")
    print(f"Explicación: {resultado['explicacion_detallada']}")

    # Demo clasificador
    print("\n2. Clasificador Híbrido")
    print("-" * 40)
    clasificador = ClasificadorHibrido()
    resultado_clas = clasificador.clasificar(
        "URGENTE: derrame en andén 3",
        "El camión CAM-102 tiene una fuga de químico inflamable.",
        usar_llm=False  # Sin LLM para demo rápida
    )
    print(f"Categoría: {resultado_clas['categoria']}")
    print(f"Prioridad: {resultado_clas['prioridad']}")

    # Demo matriz de riesgos
    print("\n3. Matriz de Riesgos Éticos")
    print("-" * 40)
    matriz = MatrizRiesgos("LogiSmart Demo")
    matriz.cargar_riesgos_predefinidos()
    resumen = matriz.resumen()
    print(f"Total riesgos: {resumen['total_riesgos']}")
    print(f"Riesgos críticos: {resumen['riesgos_por_nivel']['crítico']}")
    print(f"Puntaje promedio: {resumen['puntaje_promedio']}")

    print("\n" + "=" * 60)
    print("Demo completada")
    print("=" * 60)


def main():
    """Función principal."""
    if "--demo" in sys.argv:
        demo_consola()
    else:
        try:
            root = tk.Tk()
            app = LogiSmartGUI(root)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la aplicación:\n{e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
