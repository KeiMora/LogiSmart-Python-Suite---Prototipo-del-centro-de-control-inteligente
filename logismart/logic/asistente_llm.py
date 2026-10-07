"""
Asistente LLM explicativo con RAG (Retrieval-Augmented Generation).
El LLM responde preguntas basándose en datos recuperados de MongoDB.
"""

import ollama
from typing import Dict, List, Optional
from datetime import datetime


class AsistenteLLM:
    """
    Asistente que usa LLM para explicar decisiones del sistema.
    Implementa RAG: primero consulta MongoDB y matriz de riesgos, luego pasa el contexto al LLM.
    """

    def __init__(self, modelo: str = "llama3.2", mongo_repository=None, matriz_riesgos=None):
        """
        Inicializa el asistente.

        Args:
            modelo: Modelo de Ollama a usar
            mongo_repository: Instancia de MongoDBRepository para consultas
            matriz_riesgos: Instancia de MatrizRiesgos para riesgos éticos
        """
        self.modelo = modelo
        self.mongo_repo = mongo_repository
        self.matriz_riesgos = matriz_riesgos
        self.historial_conversacion = []

    def _construir_contexto(self, pregunta: str) -> str:
        """
        Recupera datos relevantes de MongoDB y matriz de riesgos basándose en la pregunta.

        Retorna:
        - String con el contexto recuperado o mensaje de "no tengo información"
        """
        # Detectar tipo de pregunta
        pregunta_lower = pregunta.lower()

        # Preguntas sobre camiones específicos
        if "cam-" in pregunta_lower or "camion" in pregunta_lower or "camiones" in pregunta_lower or "truck" in pregunta_lower:
            if not self.mongo_repo:
                return "No tengo acceso a la base de datos para consultar camiones."

            # Extraer ID de camión
            import re
            match = re.search(r'CAM-\d+', pregunta.upper())
            if match:
                camion_id = match.group(0)
                camion = self.mongo_repo.obtener_camion(camion_id)
                if camion:
                    try:
                        accesos = self.mongo_repo.obtener_accesos_camion(camion_id, limite=5)
                    except:
                        accesos = []

                    contexto = f"""
DATOS DEL CAMIÓN {camion_id}:
- Placa: {camion.get('placa', 'N/A')}
- Empresa: {camion.get('empresa', 'N/A')}
- Autorización: {'Sí' if camion.get('autorizacion', False) else 'No'}
- Certificación conductor: {'Sí' if camion.get('certificacion_conductor', False) else 'No'}
- Materiales peligrosos: {'Sí' if camion.get('materiales_peligrosos', False) else 'No'}
- Peso máximo: {camion.get('peso_maximo', 'N/A')} kg

ÚLTIMOS ACCESOS ({len(accesos)}):
"""
                    for acc in accesos:
                        fecha = acc.get('marca_tiempo', 'N/A')
                        if hasattr(fecha, 'strftime'):
                            fecha = fecha.strftime("%Y-%m-%d %H:%M")
                        contexto += f"- {fecha}: {acc.get('resultado', 'N/A')}\n"
                    return contexto
                else:
                    return f"No encontré información del camión {camion_id} en la base de datos."
            else:
                # Listar todos los camiones
                try:
                    camiones = self.mongo_repo.listar_camiones()
                except Exception as e:
                    return f"Error al listar camiones: {e}"

                if camiones:
                    contexto = f"CAMIONES REGISTRADOS ({len(camiones)}):\n"
                    for cam in camiones:
                        contexto += f"- {cam.get('camion_id', 'N/A')}: {cam.get('placa', 'N/A')} - {cam.get('empresa', 'N/A')}\n"
                    return contexto
                else:
                    return "No hay camiones registrados en la base de datos."

        # Preguntas sobre accesos recientes
        if "acceso" in pregunta_lower or "bitácora" in pregunta_lower or "historial" in pregunta_lower or "entradas" in pregunta_lower:
            if not self.mongo_repo:
                return "No tengo acceso a la base de datos para consultar accesos."

            try:
                accesos = self.mongo_repo.obtener_accesos_por_fecha(
                    datetime.now().replace(hour=0, minute=0, second=0),
                    datetime.now()
                )
            except Exception as e:
                return f"Error al consultar accesos: {e}"

            if accesos:
                contexto = f"ACCESOS DE HOY ({len(accesos)}):\n"
                for acc in accesos[:10]:
                    fecha = acc.get('marca_tiempo', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime("%Y-%m-%d %H:%M")
                    contexto += f"- {acc.get('camion_id', 'N/A')}: {acc.get('resultado', 'N/A')} - {fecha}\n"
                return contexto
            else:
                return "No hay accesos registrados hoy."

        # Preguntas sobre incidentes
        if "incidente" in pregunta_lower or "problema" in pregunta_lower or "reporte" in pregunta_lower:
            if not self.mongo_repo:
                return "No tengo acceso a la base de datos para consultar incidentes."

            try:
                # Verificar si la colección existe
                if hasattr(self.mongo_repo, 'db') and self.mongo_repo.db is not None:
                    colecciones = self.mongo_repo.db.list_collection_names()
                    print(f"DEBUG: Colecciones en DB: {colecciones}")
                    if 'incidentes' not in colecciones:
                        return "La colección 'incidentes' no existe en la base de datos."

                incidentes = self.mongo_repo.listar_incidentes()
                print(f"DEBUG: Incidentes encontrados: {len(incidentes)}")
                for inc in incidentes:
                    print(f"DEBUG: Incidente ID: {inc.get('_id')}, Estado: {inc.get('estado')}")
            except Exception as e:
                print(f"DEBUG: Error al listar incidentes: {e}")
                import traceback
                traceback.print_exc()
                return f"Error al consultar incidentes: {e}"

            if incidentes:
                contexto = f"INCIDENTES REGISTRADOS ({len(incidentes)}):\n"
                for inc in incidentes[:5]:
                    categoria = inc.get('clasificacion', {}).get('categoria', 'N/A')
                    estado = inc.get('estado', 'N/A')
                    fecha = inc.get('fecha_creacion', 'N/A')
                    if hasattr(fecha, 'strftime'):
                        fecha = fecha.strftime("%Y-%m-%d")
                    asunto = inc.get('asunto_original', 'N/A')[:40]
                    contexto += f"- {categoria}: {estado} - {fecha} - {asunto}\n"
                return contexto
            else:
                return "No hay incidentes registrados."

        # Preguntas sobre riesgos éticos
        if "riesgo" in pregunta_lower or "ético" in pregunta_lower or "etica" in pregunta_lower or "ethics" in pregunta_lower:
            if not self.matriz_riesgos:
                return "No tengo acceso a la matriz de riesgos éticos."

            try:
                riesgos = self.matriz_riesgos.listar_riesgos()
            except Exception as e:
                return f"Error al listar riesgos: {e}"

            if riesgos:
                contexto = f"RIESGOS ÉTICOS REGISTRADOS ({len(riesgos)}):\n"
                for id_riesgo, r in riesgos[:5]:
                    contexto += f"- ID {id_riesgo}: {r.categoria} - {r.descripcion[:50]} (Nivel: {r.nivel}, Puntaje: {r.puntaje})\n"
                return contexto
            else:
                return "No hay riesgos éticos registrados."

        # Si no se detecta un tipo específico
        return "No pude identificar qué información específica necesitas. Puedo responder sobre camiones (usando su ID como CAM-XXX), accesos, incidentes o riesgos éticos."

    def _construir_prompt(self, pregunta: str, contexto: str, historial: List[Dict]) -> str:
        """
        Construye el prompt para el LLM.

        Args:
            pregunta: Pregunta del usuario
            contexto: Datos recuperados de MongoDB
            historial: Historial de la conversación

        Returns:
            - Prompt completo para el LLM
        """
        # Construir historial de conversación
        historial_str = ""
        if historial:
            historial_str = "\nHistorial de la conversación:\n"
            for msg in historial[-5:]:  # Últimos 5 mensajes
                rol = msg.get("role", "unknown")
                contenido = msg.get("content", "")
                historial_str += f"{rol}: {contenido}\n"

        prompt = f"""
Eres un asistente del sistema LogiSmart de control logístico.

TU FUNCIÓN:
Responder preguntas sobre el sistema basándote EXCLUSIVAMENTE en los datos proporcionados en el CONTEXTO.
NO inventes información. Si el CONTEXTO tiene datos, ÚSALOS para responder.

CONTEXTO DE LA BASE DE DATOS:
{contexto}

{historial_str}

PREGUNTA DEL USUARIO:
{pregunta}

INSTRUCCIONES CRÍTICAS:
1. REVISAR EL CONTEXTO ANTES DE RESPONDER: Si el CONTEXTO contiene datos (como "INCIDENTES REGISTRADOS (14):"), DEBES usar esos datos para responder.
2. NO digas "No tengo información" si el CONTEXTO claramente tiene datos.
3. Si el CONTEXTO dice "No hay incidentes registrados" o "No encontré información", ENTONCES puedes decir eso.
4. Si hay datos relevantes en el CONTEXTO, explícalos claramente citando la información.
5. Sé conciso y directo.
6. Usa el mismo idioma que la pregunta (español).
7. Si el CONTEXTO muestra una lista, RESUME la información más importante.
"""
        return prompt

    def preguntar(self, pregunta: str) -> Dict[str, any]:
        """
        Procesa una pregunta del usuario.

        Args:
            pregunta: Pregunta del usuario

        Returns:
            - Dict con respuesta, fuentes consultadas y metadatos
        """
        # Recuperar contexto de MongoDB
        contexto = self._construir_contexto(pregunta)

        # Construir prompt
        prompt = self._construir_prompt(pregunta, contexto, self.historial_conversacion)

        # Agregar pregunta al historial
        self.historial_conversacion.append({
            "role": "user",
            "content": pregunta
        })

        try:
            # Llamar al LLM
            respuesta = ollama.chat(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}]
            )

            contenido_respuesta = respuesta["message"]["content"]

            # Agregar respuesta al historial
            self.historial_conversacion.append({
                "role": "assistant",
                "content": contenido_respuesta
            })

            return {
                "respuesta": contenido_respuesta,
                "contexto_usado": contexto,
                "fuentes": ["MongoDB"] if self.mongo_repo else [],
                "exito": True,
                "error": None
            }

        except Exception as e:
            return {
                "respuesta": f"Error al procesar la pregunta: {e}",
                "contexto_usado": contexto,
                "fuentes": [],
                "exito": False,
                "error": str(e)
            }

    def limpiar_historial(self):
        """Limpia el historial de conversación."""
        self.historial_conversacion = []

    def obtener_historial(self) -> List[Dict]:
        """Retorna el historial de conversación."""
        return self.historial_conversacion
