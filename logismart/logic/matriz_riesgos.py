"""
Matriz de riesgos éticos con cálculo de riesgo residual.
Incluye visualización gráfica de la información.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json


@dataclass
class RiesgoEtico:
    """Un riesgo ético asociado a un módulo del sistema."""
    modulo: str
    descripcion: str
    categoria: str  # sesgo, privacidad, transparencia, seguridad, responsabilidad, otro
    probabilidad: int  # 1 (muy improbable) a 5 (casi seguro)
    impacto: int  # 1 (insignificante) a 5 (catastrófico)
    mitigacion: str = ""
    fecha_registro: str = ""
    historial_mitigaciones: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.fecha_registro:
            self.fecha_registro = datetime.now().isoformat()

    @property
    def puntaje(self) -> int:
        """Puntaje de la matriz = probabilidad x impacto."""
        return self.probabilidad * self.impacto

    @property
    def nivel(self) -> str:
        """Clasificación cualitativa según el puntaje."""
        p = self.puntaje
        if p >= 17:
            return "crítico"
        if p >= 10:
            return "alto"
        if p >= 5:
            return "medio"
        return "bajo"

    @property
    def riesgo_residual(self) -> int:
        """
        Calcula el riesgo residual después de mitigación.
        Estimación simple: reduce probabilidad en 1 si hay mitigación.
        """
        if self.mitigacion:
            prob_reducida = max(1, self.probabilidad - 1)
            return prob_reducida * self.impacto
        return self.puntaje

    @property
    def reduccion_riesgo(self) -> int:
        """Reducción de riesgo lograda por la mitigación."""
        return self.puntaje - self.riesgo_residual

    def agregar_mitigacion(self, mitigacion: str):
        """Agrega una nueva mitigación al historial."""
        if self.mitigacion:
            self.historial_mitigaciones.append({
                "fecha": datetime.now().isoformat(),
                "mitigacion_anterior": self.mitigacion,
                "puntaje_anterior": self.puntaje
            })
        self.mitigacion = mitigacion


class MatrizRiesgos:
    """
    Gestiona la matriz de riesgos éticos del sistema.
    Permite cargar, editar, calcular y visualizar riesgos.
    """

    CATEGORIAS_VALIDAS = {"sesgo", "privacidad", "transparencia", "seguridad", "responsabilidad", "otro"}

    def __init__(self, nombre_sistema: str = "LogiSmart"):
        """Inicializa la matriz de riesgos."""
        self.nombre_sistema = nombre_sistema
        self.riesgos: Dict[str, RiesgoEtico] = {}  # id -> RiesgoEtico
        self._contador_id = 0

    def registrar_riesgo(self, modulo: str, descripcion: str, categoria: str,
                        probabilidad: int, impacto: int, mitigacion: str = "") -> str:
        """
        Registra un nuevo riesgo ético.

        Returns:
            - ID del riesgo registrado
        """
        if categoria not in self.CATEGORIAS_VALIDAS:
            raise ValueError(f"Categoría inválida '{categoria}'. Usa una de {sorted(self.CATEGORIAS_VALIDAS)}")

        for nombre, valor in (("probabilidad", probabilidad), ("impacto", impacto)):
            if not isinstance(valor, int) or isinstance(valor, bool) or not 1 <= valor <= 5:
                raise ValueError(f"{nombre} debe ser un entero entre 1 y 5")

        self._contador_id += 1
        riesgo_id = f"R{self._contador_id:03d}"

        riesgo = RiesgoEtico(
            modulo=modulo,
            descripcion=descripcion,
            categoria=categoria,
            probabilidad=probabilidad,
            impacto=impacto,
            mitigacion=mitigacion
        )

        self.riesgos[riesgo_id] = riesgo
        return riesgo_id

    def obtener_riesgo(self, riesgo_id: str) -> Optional[RiesgoEtico]:
        """Obtiene un riesgo por su ID."""
        return self.riesgos.get(riesgo_id)

    def listar_riesgos(self, categoria: Optional[str] = None,
                       nivel: Optional[str] = None) -> List[tuple]:
        """
        Lista riesgos, opcionalmente filtrados.

        Returns:
            - Lista de (id, riesgo) ordenados por puntaje descendente
        """
        resultados = [(id, r) for id, r in self.riesgos.items()]

        if categoria:
            resultados = [(id, r) for id, r in resultados if r.categoria == categoria]

        if nivel:
            resultados = [(id, r) for id, r in resultados if r.nivel == nivel]

        return sorted(resultados, key=lambda x: x[1].puntaje, reverse=True)

    def actualizar_riesgo(self, riesgo_id: str, **kwargs) -> bool:
        """Actualiza un riesgo existente."""
        if riesgo_id not in self.riesgos:
            return False

        riesgo = self.riesgos[riesgo_id]

        for key, value in kwargs.items():
            if hasattr(riesgo, key):
                setattr(riesgo, key, value)

        return True

    def eliminar_riesgo(self, riesgo_id: str) -> bool:
        """Elimina un riesgo."""
        if riesgo_id in self.riesgos:
            del self.riesgos[riesgo_id]
            return True
        return False

    def resumen(self) -> Dict[str, any]:
        """Genera un resumen estadístico de los riesgos."""
        if not self.riesgos:
            return {
                "sistema": self.nombre_sistema,
                "total_riesgos": 0,
                "riesgos_por_nivel": {},
                "riesgos_por_categoria": {},
                "puntaje_promedio": 0,
                "riesgo_total": 0
            }

        por_nivel = {"crítico": 0, "alto": 0, "medio": 0, "bajo": 0}
        por_categoria: Dict[str, int] = {}
        puntajes = []
        riesgo_total = 0

        for r in self.riesgos.values():
            por_nivel[r.nivel] += 1
            por_categoria[r.categoria] = por_categoria.get(r.categoria, 0) + 1
            puntajes.append(r.puntaje)
            riesgo_total += r.puntaje

        return {
            "sistema": self.nombre_sistema,
            "total_riesgos": len(self.riesgos),
            "riesgos_por_nivel": por_nivel,
            "riesgos_por_categoria": por_categoria,
            "puntaje_promedio": round(sum(puntajes) / len(puntajes), 2),
            "riesgo_total": riesgo_total,
            "riesgo_residual_total": sum(r.riesgo_residual for r in self.riesgos.values()),
            "reduccion_total": sum(r.reduccion_riesgo for r in self.riesgos.values())
        }

    def obtener_datos_grafica(self) -> Dict[str, any]:
        """
        Genera datos estructurados para visualización gráfica.

        Returns:
            - Dict con datos para diferentes tipos de gráficas
        """
        # Datos para gráfica de dispersión (probabilidad vs impacto)
        dispersión = []
        for id, r in self.riesgos.items():
            dispersión.append({
                "id": id,
                "modulo": r.modulo,
                "descripcion": r.descripcion[:30] + "..." if len(r.descripcion) > 30 else r.descripcion,
                "x": r.probabilidad,
                "y": r.impacto,
                "puntaje": r.puntaje,
                "nivel": r.nivel,
                "categoria": r.categoria
            })

        # Datos para gráfica de barras (por categoría)
        categorias = {}
        for r in self.riesgos.values():
            if r.categoria not in categorias:
                categorias[r.categoria] = {"count": 0, "puntaje_total": 0}
            categorias[r.categoria]["count"] += 1
            categorias[r.categoria]["puntaje_total"] += r.puntaje

        barras_categoria = [
            {
                "categoria": cat,
                "cantidad": data["count"],
                "puntaje_promedio": round(data["puntaje_total"] / data["count"], 2)
            }
            for cat, data in categorias.items()
        ]

        # Datos para gráfica de pastel (por nivel)
        por_nivel = {"crítico": 0, "alto": 0, "medio": 0, "bajo": 0}
        for r in self.riesgos.values():
            por_nivel[r.nivel] += 1

        pastel_nivel = [
            {"nivel": nivel, "cantidad": count}
            for nivel, count in por_nivel.items()
        ]

        # Datos para comparación riesgo inicial vs residual
        comparacion = []
        for id, r in self.riesgos.items():
            comparacion.append({
                "id": id,
                "descripcion": r.descripcion[:20] + "..." if len(r.descripcion) > 20 else r.descripcion,
                "riesgo_inicial": r.puntaje,
                "riesgo_residual": r.riesgo_residual,
                "reduccion": r.reduccion_riesgo
            })

        return {
            "dispersion": dispersión,
            "barras_categoria": barras_categoria,
            "pastel_nivel": pastel_nivel,
            "comparacion_riesgo": comparacion
        }

    def exportar_json(self, ruta: Optional[str] = None) -> str:
        """Exporta la matriz a JSON."""
        datos = {
            "resumen": self.resumen(),
            "datos_grafica": self.obtener_datos_grafica(),
            "riesgos": {
                id: {
                    "modulo": r.modulo,
                    "descripcion": r.descripcion,
                    "categoria": r.categoria,
                    "probabilidad": r.probabilidad,
                    "impacto": r.impacto,
                    "mitigacion": r.mitigacion,
                    "puntaje": r.puntaje,
                    "nivel": r.nivel,
                    "riesgo_residual": r.riesgo_residual,
                    "reduccion_riesgo": r.reduccion_riesgo,
                    "fecha_registro": r.fecha_registro
                }
                for id, r in self.riesgos.items()
            }
        }

        texto = json.dumps(datos, ensure_ascii=False, indent=2)
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto)
        return texto

    def cargar_desde_json(self, ruta: str) -> bool:
        """Carga riesgos desde un archivo JSON."""
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)

            for id, r_data in datos.get("riesgos", {}).items():
                self.registrar_riesgo(
                    modulo=r_data["modulo"],
                    descripcion=r_data["descripcion"],
                    categoria=r_data["categoria"],
                    probabilidad=r_data["probabilidad"],
                    impacto=r_data["impacto"],
                    mitigacion=r_data.get("mitigacion", "")
                )

            return True
        except Exception as e:
            print(f"Error al cargar JSON: {e}")
            return False

    def cargar_riesgos_predefinidos(self):
        """Carga riesgos predefinidos para el sistema LogiSmart."""
        riesgos_data = [
            # Riesgos del sistema original
            ("Cámara de Detección de Somnolencia", "Sesgo en visión nocturna (falsos positivos por tono de piel / poca luz)",
             "sesgo", 4, 4, "Entrenar y auditar con datos nocturnos y diversos; umbral ajustable"),
            ("Cámara de Detección de Somnolencia", "Violación de privacidad (video continuo del conductor)",
             "privacidad", 4, 5, "Procesar en el borde, no almacenar video, aviso y consentimiento"),
            ("Lector de Placas (LPR)", "Lectura errónea que niega acceso injustificadamente",
             "responsabilidad", 3, 3, "Revisión humana y canal de apelación"),
            ("Lector de Placas (LPR)", "Conservación indebida de datos de placas",
             "privacidad", 2, 4, "Política de retención y cifrado"),
            ("Clasificador de Incidentes", "Priorizar mal un incidente crítico (falso negativo)",
             "seguridad", 2, 5, "Palabras críticas siempre escalan; revisión humana de 'otro'"),

            # Riesgos de la nueva implementación
            ("Clasificador Híbrido LLM", "Alucinaciones del LLM generando clasificaciones incorrectas",
             "transparencia", 3, 4, "Validación con Pydantic, fallback a reglas, revisión humana de discrepancias"),
            ("Clasificador Híbrido LLM", "Sesgo en correos con ortografía informal o dialectos regionales",
             "sesgo", 3, 3, "Dataset de entrenamiento diverso, normalización de texto, revisión manual"),
            ("Base de Datos MongoDB", "Privacidad de datos del conductor en la base de datos",
             "privacidad", 3, 5, "Cifrado en reposo, acceso restringido, anonimización de datos sensibles"),
            ("Sistema de Automatización", "Dependencia excesiva de la automatización sin supervisión humana",
             "responsabilidad", 2, 4, "Alertas para revisión humana, logs de auditoría, pruebas periódicas"),
            ("Asistente LLM Explicativo", "El LLM inventa información no respaldada en datos (alucinación RAG)",
             "transparencia", 2, 3, "Validación estricta: solo responder si hay datos en contexto, frase 'no tengo información'"),
        ]

        for modulo, descripcion, categoria, prob, imp, mitig in riesgos_data:
            self.registrar_riesgo(modulo, descripcion, categoria, prob, imp, mitig)
