"""
Motor de reglas lógicas para control de acceso e inspección.
Implementa lógica proposicional con tablas de verdad.
"""

import itertools
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ReglaLogica:
    """Representa una regla lógica del sistema."""
    nombre: str
    formula: str  # Representación en texto (ej: "P ∧ S ∧ ¬Q")
    variables: List[str]  # Lista de variables usadas
    descripcion: str
    resultado: bool  # Resultado de evaluar la regla
    explicacion: str  # Explicación paso a paso


class MotorReglas:
    """
    Motor de reglas para evaluar el acceso de camiones.

    Variables:
    - P: Vehículo con autorización previa
    - Q: El peso excede el límite
    - R: Carga con materiales peligrosos
    - S: Conductor con certificación vigente
    - V: Certificación del conductor vigente (extra)
    - H: Horario permitido para materiales peligrosos (extra)
    """

    def __init__(self):
        """Inicializa el motor de reglas."""
        self.reglas_activas = []
        self.historial_evaluaciones = []

    def evaluar_camion(self, P: bool, Q: bool, R: bool, S: bool,
                       V: bool = True, H: bool = True) -> Dict[str, any]:
        """
        Evalúa todas las reglas para un camión.

        Parámetros:
        - P: ¿Tiene autorización previa?
        - Q: ¿El peso excede el límite?
        - R: ¿Lleva materiales peligrosos?
        - S: ¿El conductor tiene certificación vigente?
        - V: ¿La certificación está vigente? (extra)
        - H: ¿Es horario permitido para materiales peligrosos? (extra)

        Retorna:
        - Dict con resultados de todas las reglas y explicaciones
        """
        # Validación de tipos
        for nombre, valor in [("P", P), ("Q", Q), ("R", R), ("S", S), ("V", V), ("H", H)]:
            if not isinstance(valor, bool):
                raise TypeError(f"La premisa {nombre} debe ser bool, se recibió {type(valor).__name__}")

        # Regla 1: Acceso Estándar (A) = P ∧ S ∧ ¬Q
        no_Q = not Q
        P_y_S = P and S
        acceso_estandar = P and S and not Q

        # Regla 2: Inspección Especial (E) = P ∧ (R ∨ Q)
        R_o_Q = R or Q
        inspeccion_especial = P and (R or Q)

        # Regla 3 (NUEVA): Restricción por Certificación (C) = P ∧ S ∧ ¬V
        # Si tiene autorización y conductor pero certificación NO vigente
        restriccion_certificacion = P and S and not V

        # Regla 4 (NUEVA): Restricción Horaria (T) = R ∧ ¬H
        # Si lleva materiales peligrosos fuera de horario permitido
        restriccion_horaria = R and not H

        # Guardar reglas activas
        self.reglas_activas = [
            ReglaLogica(
                nombre="Acceso Estándar (A)",
                formula="P ∧ S ∧ ¬Q",
                variables=["P", "S", "Q"],
                descripcion="Permite acceso estándar cuando hay autorización, "
                           "conductor certificado y sin exceso de peso",
                resultado=acceso_estandar,
                explicacion=self._explicar_acceso_estandar(P, S, no_Q, P_y_S)
            ),
            ReglaLogica(
                nombre="Inspección Especial (E)",
                formula="P ∧ (R ∨ Q)",
                variables=["P", "R", "Q"],
                descripcion="Activa inspección especial cuando hay autorización "
                           "y (carga peligrosa o exceso de peso)",
                resultado=inspeccion_especial,
                explicacion=self._explicar_inspeccion_especial(P, R_o_Q)
            ),
            ReglaLogica(
                nombre="Restricción por Certificación (C)",
                formula="P ∧ S ∧ ¬V",
                variables=["P", "S", "V"],
                descripcion="Bloquea acceso si el conductor tiene autorización "
                           "pero su certificación no está vigente",
                resultado=restriccion_certificacion,
                explicacion=self._explicar_restriccion_certificacion(P, S, V)
            ),
            ReglaLogica(
                nombre="Restricción Horaria (T)",
                formula="R ∧ ¬H",
                variables=["R", "H"],
                descripcion="Restringe entrada de materiales peligrosos "
                           "fuera del horario permitido",
                resultado=restriccion_horaria,
                explicacion=self._explicar_restriccion_horaria(R, H)
            )
        ]

        # Guardar en historial
        evaluacion = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "premisas": {"P": P, "Q": Q, "R": R, "S": S, "V": V, "H": H},
            "resultados": {
                "acceso_estandar": acceso_estandar,
                "inspeccion_especial": inspeccion_especial,
                "restriccion_certificacion": restriccion_certificacion,
                "restriccion_horaria": restriccion_horaria
            },
            "explicaciones": [r.explicacion for r in self.reglas_activas]
        }
        self.historial_evaluaciones.append(evaluacion)

        return {
            "acceso_estandar": acceso_estandar,
            "inspeccion_especial": inspeccion_especial,
            "restriccion_certificacion": restriccion_certificacion,
            "restriccion_horaria": restriccion_horaria,
            "decision_final": self._determinar_decision_final(
                acceso_estandar, inspeccion_especial,
                restriccion_certificacion, restriccion_horaria
            ),
            "reglas_aplicadas": [r for r in self.reglas_activas if r.resultado],
            "explicacion_detallada": evaluacion["explicaciones"]
        }

    def _explicar_acceso_estandar(self, P: bool, S: bool, no_Q: bool, P_y_S: bool) -> str:
        """Genera explicación paso a paso para acceso estándar."""
        pasos = []
        pasos.append(f"Premisa P (autorización): {P}")
        pasos.append(f"Premisa S (conductor certificado): {S}")
        pasos.append(f"¬Q (sin exceso de peso): {no_Q}")
        pasos.append(f"P ∧ S (autorización Y conductor): {P_y_S}")
        pasos.append(f"Resultado (P ∧ S ∧ ¬Q): {P and S and no_Q}")
        return " | ".join(pasos)

    def _explicar_inspeccion_especial(self, P: bool, R_o_Q: bool) -> str:
        """Genera explicación paso a paso para inspección especial."""
        pasos = []
        pasos.append(f"Premisa P (autorización): {P}")
        pasos.append(f"R ∨ Q (peligrosos O exceso peso): {R_o_Q}")
        pasos.append(f"Resultado (P ∧ (R ∨ Q)): {P and R_o_Q}")
        return " | ".join(pasos)

    def _explicar_restriccion_certificacion(self, P: bool, S: bool, V: bool) -> str:
        """Genera explicación para restricción por certificación."""
        pasos = []
        pasos.append(f"Premisa P (autorización): {P}")
        pasos.append(f"Premisa S (conductor certificado): {S}")
        pasos.append(f"¬V (certificación NO vigente): {not V}")
        pasos.append(f"Resultado (P ∧ S ∧ ¬V): {P and S and not V}")
        return " | ".join(pasos)

    def _explicar_restriccion_horaria(self, R: bool, H: bool) -> str:
        """Genera explicación para restricción horaria."""
        pasos = []
        pasos.append(f"Premisa R (materiales peligrosos): {R}")
        pasos.append(f"¬H (fuera de horario permitido): {not H}")
        pasos.append(f"Resultado (R ∧ ¬H): {R and not H}")
        return " | ".join(pasos)

    def _determinar_decision_final(self, A: bool, E: bool, C: bool, T: bool) -> str:
        """
        Determina la decisión final basada en todas las reglas.

        Prioridades:
        1. Restricciones (C, T) tienen prioridad sobre acceso
        2. Inspección especial (E) se aplica cuando no hay restricciones
        3. Acceso estándar (A) solo si no hay restricciones ni inspección
        """
        if C or T:
            return "DENEGADO" if C else "RESTRINGIDO_HORARIO"
        if E:
            return "INSPECCION_ESPECIAL"
        if A:
            return "ACCESO_ESTANDAR"
        return "DENEGADO"

    def generar_tabla_verdad(self) -> List[Dict[str, bool]]:
        """
        Genera la tabla de verdad completa para las reglas principales A y E.
        2^4 = 16 combinaciones de (P, Q, R, S).
        """
        filas = []
        for P, Q, R, S in itertools.product([True, False], repeat=4):
            resultado = self.evaluar_camion(P, Q, R, S)
            filas.append({
                "P": P, "Q": Q, "R": R, "S": S,
                "no_Q": not Q,
                "P_y_S": P and S,
                "R_o_Q": R or Q,
                "A": resultado["acceso_estandar"],
                "E": resultado["inspeccion_especial"]
            })
        return filas

    def generar_tabla_verdad_completa(self) -> List[Dict[str, bool]]:
        """
        Genera tabla de verdad completa para todas las reglas.
        2^6 = 64 combinaciones de (P, Q, R, S, V, H).
        """
        filas = []
        for P, Q, R, S, V, H in itertools.product([True, False], repeat=6):
            resultado = self.evaluar_camion(P, Q, R, S, V, H)
            filas.append({
                "P": P, "Q": Q, "R": R, "S": S, "V": V, "H": H,
                "A": resultado["acceso_estandar"],
                "E": resultado["inspeccion_especial"],
                "C": resultado["restriccion_certificacion"],
                "T": resultado["restriccion_horaria"],
                "decision": resultado["decision_final"]
            })
        return filas

    def detectar_contradicciones(self) -> List[str]:
        """
        Detecta contradicciones o redundancias entre reglas.
        Retorna lista de mensajes describiendo problemas encontrados.
        """
        problemas = []

        # Verificar si ambas reglas de restricción pueden ser verdaderas simultáneamente
        # sin conflicto lógico
        tabla = self.generar_tabla_verdad_completa()
        restricciones_simultaneas = [f for f in tabla if f["C"] and f["T"]]

        if restricciones_simultaneas:
            problemas.append(
                f"Se encontraron {len(restricciones_simultaneas)} casos donde ambas "
                "restricciones (C y T) están activas. Esto es normal: puede haber "
                "certificación vencida Y horario restringido simultáneamente."
            )

        # Verificar casos donde A (acceso estándar) es verdadero pero hay restricciones
        acceso_con_restriccion = [f for f in tabla if f["A"] and (f["C"] or f["T"])]
        if acceso_con_restriccion:
            problemas.append(
                f"ADVERTENCIA: Se encontraron {len(acceso_con_restriccion)} casos donde "
                "el acceso estándar (A) es verdadero pero hay restricciones activas. "
                "Esto indica un posible conflicto en la lógica de decisión final."
            )

        if not problemas:
            problemas.append("No se detectaron contradicciones o redundancias evidentes.")

        return problemas

    def obtener_historial(self) -> List[Dict]:
        """Retorna el historial de evaluaciones."""
        return self.historial_evaluaciones

    def limpiar_historial(self):
        """Limpia el historial de evaluaciones."""
        self.historial_evaluaciones = []
