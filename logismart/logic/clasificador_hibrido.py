"""
Clasificador híbrido de incidentes (reglas + LLM).
Combina clasificación por reglas con clasificación por LLM local (Ollama).
"""

import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import ollama
from pydantic import BaseModel, Field, validator


# ============================================================
# MODELOS PYDANTIC PARA VALIDACIÓN
# ============================================================

class PrioridadEnum(str, Enum):
    """Prioridades válidas para incidentes."""
    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class CategoriaEnum(str, Enum):
    """Categorías válidas para incidentes."""
    materiales_peligrosos = "materiales_peligrosos"
    sobrepeso = "sobrepeso"
    acceso_no_autorizado = "acceso_no_autorizado"
    falla_hardware = "falla_hardware"
    falla_software = "falla_software"
    somnolencia_conductor = "somnolencia_conductor"
    otro = "otro"


class ClasificacionLLM(BaseModel):
    """Esquema para la salida del LLM."""
    categoria: CategoriaEnum = Field(description="Categoría del incidente")
    prioridad: PrioridadEnum = Field(description="Nivel de prioridad")
    entidades: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Entidades extraídas (placa, camion_id, peso, ubicacion)"
    )
    resumen: str = Field(description="Resumen breve del incidente")

    @validator('entidades')
    def validar_entidades(cls, v):
        """Valida que las entidades tengan las claves esperadas."""
        claves_permitidas = {"placa", "camion_id", "peso", "ubicacion"}
        for key in v:
            if key not in claves_permitidas:
                raise ValueError(f"Clave de entidad no permitida: {key}")
        return v


# ============================================================
# CLASIFICADOR POR REGLAS
# ============================================================

class ClasificadorReglas:
    """Clasificador basado en reglas (palabras clave)."""

    CATEGORIAS: Dict[str, List[str]] = {
        "materiales_peligrosos": ["peligroso", "derrame", "fuga", "quimico", "inflamable", "toxico", "corrosivo"],
        "sobrepeso": ["sobrepeso", "excede", "bascula", "exceso de peso", "sobrecarga"],
        "acceso_no_autorizado": ["sin autorizacion", "no autorizado", "acceso denegado", "barrera", "intruso"],
        "falla_hardware": ["camara", "sensor", "lector", "rfid", "no enciende", "apagado", "danado", "falla electrica"],
        "falla_software": ["sistema", "error", "pantalla", "caido", "no carga", "lento", "software", "aplicacion"],
        "somnolencia_conductor": ["somnolencia", "dormido", "cansancio", "fatiga", "sueno"],
    }

    PALABRAS_URGENTES = ["urgente", "emergencia", "accidente", "incendio", "herido", "critico", "inmediato"]

    PRIORIDAD_BASE: Dict[str, str] = {
        "materiales_peligrosos": "critica",
        "somnolencia_conductor": "alta",
        "acceso_no_autorizado": "alta",
        "sobrepeso": "media",
        "falla_hardware": "media",
        "falla_software": "baja",
        "otro": "baja",
    }

    ORDEN_PRIORIDAD = ["baja", "media", "alta", "critica"]

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Normaliza texto para comparación."""
        tabla = str.maketrans("áéíóúüñ", "aeiouun")
        return texto.lower().translate(tabla)

    def clasificar(self, asunto: str, cuerpo: str) -> Dict[str, any]:
        """Clasifica el incidente usando reglas."""
        texto = self._normalizar(f"{asunto} {cuerpo}")

        # Puntuación por categoría
        puntajes = {
            cat: [kw for kw in kws if kw in texto]
            for cat, kws in self.CATEGORIAS.items()
        }

        # Elegir categoría con más coincidencias
        mejor_cat = max(puntajes, key=lambda c: len(puntajes[c]))
        if not puntajes[mejor_cat]:
            mejor_cat = "otro"
            coincidencias = []
        else:
            coincidencias = puntajes[mejor_cat]

        # Determinar prioridad
        prioridad = self.PRIORIDAD_BASE[mejor_cat]
        urgentes = [p for p in self.PALABRAS_URGENTES if p in texto]
        if urgentes:
            idx = min(self.ORDEN_PRIORIDAD.index(prioridad) + 1, len(self.ORDEN_PRIORIDAD) - 1)
            prioridad = self.ORDEN_PRIORIDAD[idx]

        return {
            "categoria": mejor_cat,
            "prioridad": prioridad,
            "palabras_clave": coincidencias + urgentes,
            "metodo": "reglas"
        }

    def extraer_entidades(self, asunto: str, cuerpo: str) -> Dict[str, Optional[str]]:
        """Extrae entidades usando expresiones regulares."""
        texto = f"{asunto}\n{cuerpo}"

        # Placa
        m_placa = re.search(r"\b[A-Z0-9]{2,3}-\d{2,3}-[A-Z0-9]{1,2}\b", texto.upper())
        placa = m_placa.group(0) if m_placa else None

        # ID de camión
        m_camion = re.search(r"\bCAM-\d+\b", texto.upper())
        camion_id = m_camion.group(0) if m_camion else None

        # Peso
        m_peso = re.search(r"(\d+(?:[.,]\d+)?)\s*(toneladas|tonelada|ton|t|kg)\b", texto.lower())
        peso = None
        if m_peso:
            valor = float(m_peso.group(1).replace(",", "."))
            peso = f"{valor} {m_peso.group(2)}"

        # Ubicación
        m_ubic = re.search(r"\b(and[eé]n|puerta|muelle|caseta|dock)\s+([A-Za-z0-9]+)", texto, re.IGNORECASE)
        ubicacion = f"{m_ubic.group(1)} {m_ubic.group(2)}".lower() if m_ubic else None

        return {
            "placa": placa,
            "camion_id": camion_id,
            "peso": peso,
            "ubicacion": ubicacion
        }


# ============================================================
# CLASIFICADOR CON LLM
# ============================================================

class ClasificadorLLM:
    """Clasificador usando LLM local (Ollama)."""

    def __init__(self, modelo: str = "llama3.2"):
        """Inicializa el clasificador LLM."""
        self.modelo = modelo
        self.clasificador_reglas = ClasificadorReglas()

    def _construir_prompt(self, asunto: str, cuerpo: str) -> str:
        """Construye el prompt para el LLM."""
        prompt = f"""
Clasifica el siguiente incidente de soporte logístico.

ASUNTO: {asunto}
CUERPO: {cuerpo}

Categorías válidas:
- materiales_peligrosos
- sobrepeso
- acceso_no_autorizado
- falla_hardware
- falla_software
- somnolencia_conductor
- otro

Prioridades válidas: baja, media, alta, critica

Extrae las siguientes entidades si están presentes:
- placa (formato: ABC-123-D)
- camion_id (formato: CAM-XXX)
- peso (con unidad)
- ubicación (andén, puerta, muelle, caseta)

Responde SOLAMENTE con un JSON válido con este esquema:
{{
    "categoria": "categoria",
    "prioridad": "prioridad",
    "entidades": {{
        "placa": "valor o null",
        "camion_id": "valor o null",
        "peso": "valor o null",
        "ubicacion": "valor o null"
    }},
    "resumen": "resumen breve en una frase"
}}
"""
        return prompt

    def clasificar(self, asunto: str, cuerpo: str,
                   max_retries: int = 3) -> Tuple[Optional[ClasificacionLLM], float, str]:
        """
        Clasifica usando el LLM.

        Retorna:
        - (Clasificación validada, latencia en segundos, estado)
        """
        prompt = self._construir_prompt(asunto, cuerpo)
        latencia = 0.0

        for intento in range(max_retries):
            try:
                inicio = time.time()
                respuesta = ollama.chat(
                    model=self.modelo,
                    messages=[{"role": "user", "content": prompt}]
                )
                latencia = time.time() - inicio

                contenido = respuesta["message"]["content"]

                # Intentar extraer JSON del contenido
                # El LLM podría agregar texto alrededor del JSON
                json_match = re.search(r'\{.*\}', contenido, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        datos = json.loads(json_str)
                        clasificacion = ClasificacionLLM(**datos)
                        return clasificacion, latencia, "exito"
                    except Exception as e:
                        print(f"Intento {intento + 1}: JSON inválido - {e}")
                        continue
                else:
                    print(f"Intento {intento + 1}: No se encontró JSON en la respuesta")
                    continue

            except Exception as e:
                print(f"Intento {intento + 1}: Error al llamar al LLM - {e}")
                continue

        # Si fallan todos los intentos
        return None, latencia, "fallo"


# ============================================================
# CLASIFICADOR HÍBRIDO
# ============================================================

class ClasificadorHibrido:
    """Clasificador que combina reglas y LLM."""

    def __init__(self, modelo_llm: str = "llama3.2"):
        """Inicializa el clasificador híbrido."""
        self.clasificador_reglas = ClasificadorReglas()
        self.clasificador_llm = ClasificadorLLM(modelo_llm)
        self.modelo_llm = modelo_llm
        self.historial_evaluaciones = []

    def clasificar(self, asunto: str, cuerpo: str,
                   usar_llm: bool = True) -> Dict[str, any]:
        """
        Clasifica el incidente usando el método híbrido.

        Estrategia:
        1. Clasificar con reglas (siempre)
        2. Clasificar con LLM (si usar_llm=True)
        3. Si ambos discrepan, prevalece la prioridad más alta
        4. Marcar como requiere_revision_humana si hay discrepancia

        Retorna:
        - Dict con clasificación final y metadatos
        """
        resultado_reglas = self.clasificador_reglas.clasificar(asunto, cuerpo)
        entidades_reglas = self.clasificador_reglas.extraer_entidades(asunto, cuerpo)

        resultado_llm = None
        latencia_llm = 0.0
        estado_llm = "no_usado"

        if usar_llm:
            clasificacion_llm, latencia_llm, estado_llm = self.clasificador_llm.clasificar(asunto, cuerpo)
            if clasificacion_llm:
                resultado_llm = {
                    "categoria": clasificacion_llm.categoria.value,
                    "prioridad": clasificacion_llm.prioridad.value,
                    "entidades": clasificacion_llm.entidades,
                    "resumen": clasificacion_llm.resumen
                }

        # Determinar clasificación final
        if resultado_llm and estado_llm == "exito":
            # Comparar prioridades
            prioridad_reglas = self.clasificador_reglas.ORDEN_PRIORIDAD.index(resultado_reglas["prioridad"])
            prioridad_llm = self.clasificador_reglas.ORDEN_PRIORIDAD.index(resultado_llm["prioridad"])

            discrepancia = (
                resultado_reglas["categoria"] != resultado_llm["categoria"] or
                resultado_reglas["prioridad"] != resultado_llm["prioridad"]
            )

            if discrepancia:
                # Prevalece la prioridad más alta (ante la duda, seguridad)
                if prioridad_llm >= prioridad_reglas:
                    clasificacion_final = resultado_llm
                    metodo_final = "llm"
                else:
                    clasificacion_final = resultado_reglas
                    metodo_final = "reglas"
                requiere_revision = True
            else:
                clasificacion_final = resultado_llm  # Prefiero LLM si coinciden
                metodo_final = "llm"
                requiere_revision = False
        else:
            clasificacion_final = resultado_reglas
            metodo_final = "reglas"
            requiere_revision = False

        # Guardar en historial
        evaluacion = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "asunto": asunto,
            "clasificacion_reglas": resultado_reglas,
            "clasificacion_llm": resultado_llm,
            "clasificacion_final": clasificacion_final,
            "metodo_final": metodo_final,
            "latencia_llm": latencia_llm,
            "estado_llm": estado_llm,
            "requiere_revision_humana": requiere_revision,
            "entidades": entidades_reglas
        }
        self.historial_evaluaciones.append(evaluacion)

        return {
            "categoria": clasificacion_final["categoria"],
            "prioridad": clasificacion_final["prioridad"],
            "entidades": entidades_reglas,
            "resumen": clasificacion_final.get("resumen", ""),
            "metodo": metodo_final,
            "requiere_revision_humana": requiere_revision,
            "latencia_llm": latencia_llm,
            "coincidio_con_reglas": (resultado_reglas["categoria"] == clasificacion_final["categoria"] and
                                     resultado_reglas["prioridad"] == clasificacion_final["prioridad"])
        }

    def obtener_historial(self) -> List[Dict]:
        """Retorna el historial de evaluaciones."""
        return self.historial_evaluaciones

    def calcular_estadisticas(self) -> Dict[str, any]:
        """Calcula estadísticas de rendimiento del clasificador híbrido."""
        if not self.historial_evaluaciones:
            return {}

        total = len(self.historial_evaluaciones)
        exitos_llm = sum(1 for e in self.historial_evaluaciones if e["estado_llm"] == "exito")
        fallos_llm = sum(1 for e in self.historial_evaluaciones if e["estado_llm"] == "fallo")
        revisiones = sum(1 for e in self.historial_evaluaciones if e["requiere_revision_humana"])
        coincidencias = sum(1 for e in self.historial_evaluaciones if e.get("coincidio_con_reglas", False))

        latencias = [e["latencia_llm"] for e in self.historial_evaluaciones if e["latencia_llm"] > 0]
        latencia_promedio = sum(latencias) / len(latencias) if latencias else 0

        return {
            "total_evaluaciones": total,
            "exitos_llm": exitos_llm,
            "fallos_llm": fallos_llm,
            "tasa_exito_llm": exitos_llm / total if total > 0 else 0,
            "revisiones_humanas": revisiones,
            "tasa_revision": revisiones / total if total > 0 else 0,
            "coincidencias_con_reglas": coincidencias,
            "tasa_coincidencia": coincidencias / total if total > 0 else 0,
            "latencia_promedio_llm": latencia_promedio
        }
