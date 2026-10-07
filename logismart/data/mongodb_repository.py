"""
Repositorio de MongoDB para la persistencia de datos.
Implementa CRUD para todas las colecciones del sistema.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, errors
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database

from config.settings import config


class MongoDBRepository:
    """Repositorio principal para todas las operaciones de MongoDB."""

    def __init__(self, mongo_config=None):
        """Inicializa la conexión a MongoDB."""
        self.mongo_config = mongo_config or config.mongo
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._conectar()

    def _conectar(self):
        """Establece la conexión con MongoDB."""
        try:
            if self.mongo_config.connection_string:
                # Usar connection string (Atlas)
                self.client = MongoClient(self.mongo_config.connection_string)
            else:
                # Usar host/port local
                self.client = MongoClient(
                    self.mongo_config.host,
                    self.mongo_config.port,
                    username=self.mongo_config.username,
                    password=self.mongo_config.password
                )

            # Probar conexión
            self.client.admin.command('ping')

            self.db = self.client[self.mongo_config.database]
            print(f"✓ Conectado a MongoDB: {self.mongo_config.database}")

        except errors.ConnectionFailure as e:
            print(f"✗ Error de conexión a MongoDB: {e}")
            raise
        except Exception as e:
            print(f"✗ Error al conectar: {e}")
            raise

    # ============================================================
    # COLECCIÓN: camiones
    # ============================================================

    def crear_camion(self, camion: Dict[str, Any]) -> str:
        """Crea un nuevo camión en la base de datos."""
        camion["fecha_registro"] = datetime.now()
        resultado = self.db.camiones.insert_one(camion)
        return str(resultado.inserted_id)

    def obtener_camion(self, camion_id: str) -> Optional[Dict]:
        """Obtiene un camión por su ID."""
        return self.db.camiones.find_one({"camion_id": camion_id})

    def obtener_camion_por_placa(self, placa: str) -> Optional[Dict]:
        """Obtiene un camión por su placa."""
        return self.db.camiones.find_one({"placa": placa})

    def listar_camiones(self, filtro: Dict = None) -> List[Dict]:
        """Lista todos los camiones, opcionalmente con filtro."""
        return list(self.db.camiones.find(filtro or {}))

    def actualizar_camion(self, camion_id: str, actualizacion: Dict) -> bool:
        """Actualiza un camión."""
        resultado = self.db.camiones.update_one(
            {"camion_id": camion_id},
            {"$set": actualizacion}
        )
        return resultado.modified_count > 0

    def eliminar_camion(self, camion_id: str) -> bool:
        """Elimina un camión."""
        resultado = self.db.camiones.delete_one({"camion_id": camion_id})
        return resultado.deleted_count > 0

    # ============================================================
    # COLECCIÓN: accesos
    # ============================================================

    def registrar_acceso(self, acceso: Dict[str, Any]) -> str:
        """Registra un acceso en la bitácora."""
        acceso["marca_tiempo"] = datetime.now()
        resultado = self.db.accesos.insert_one(acceso)
        return str(resultado.inserted_id)

    def obtener_accesos_camion(self, camion_id: str, limite: int = 100) -> List[Dict]:
        """Obtiene el historial de accesos de un camión."""
        return list(
            self.db.accesos.find({"camion_id": camion_id})
            .sort("marca_tiempo", -1)
            .limit(limite)
        )

    def obtener_accesos_por_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict]:
        """Obtiene accesos en un rango de fechas."""
        return list(
            self.db.accesos.find({
                "marca_tiempo": {"$gte": fecha_inicio, "$lte": fecha_fin}
            }).sort("marca_tiempo", -1)
        )

    def obtener_estadisticas_accesos(self, fecha_inicio=None, fecha_fin=None) -> Dict:
        """Obtiene estadísticas de accesos, opcionalmente filtrando por fecha."""
        pipeline = [{"$group": {"_id": "$resultado", "count": {"$sum": 1}}}]

        # Si se proporcionan fechas, agregar filtro
        if fecha_inicio and fecha_fin:
            pipeline.insert(0, {
                "$match": {
                    "marca_tiempo": {"$gte": fecha_inicio, "$lte": fecha_fin}
                }
            })

        resultados = list(self.db.accesos.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in resultados}

    # ============================================================
    # COLECCIÓN: incidentes
    # ============================================================

    def crear_incidente(self, incidente: Dict[str, Any]) -> str:
        """Crea un nuevo incidente."""
        incidente["fecha_creacion"] = datetime.now()
        incidente["estado"] = "nuevo"
        resultado = self.db.incidentes.insert_one(incidente)
        return str(resultado.inserted_id)

    def obtener_incidente(self, incidente_id: str) -> Optional[Dict]:
        """Obtiene un incidente por su ID."""
        return self.db.incidentes.find_one({"_id": incidente_id})

    def listar_incidentes(self, estado: Optional[str] = None) -> List[Dict]:
        """Lista incidentes, opcionalmente filtrando por estado."""
        filtro = {"estado": estado} if estado else {}
        return list(self.db.incidentes.find(filtro).sort("fecha_creacion", -1))

    def actualizar_incidente(self, incidente_id: ObjectId, actualizacion: Dict) -> bool:
        """Actualiza un incidente."""
        resultado = self.db.incidentes.update_one(
            {"_id": incidente_id},
            {"$set": actualizacion}
        )
        return resultado.modified_count > 0

    def eliminar_incidente(self, incidente_id: ObjectId) -> bool:
        """Elimina un incidente."""
        resultado = self.db.incidentes.delete_one({"_id": incidente_id})
        return resultado.deleted_count > 0

    def cambiar_estado_incidente(self, incidente_id: str, nuevo_estado: str) -> bool:
        """Cambia el estado de un incidente."""
        estados_validos = ["nuevo", "en_atencion", "cerrado"]
        if nuevo_estado not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {estados_validos}")
        return self.actualizar_incidente(incidente_id, {"estado": nuevo_estado})

    def agregacion_incidentes_por_categoria_semana(self) -> List[Dict]:
        """Agregación: incidentes por categoría y semana."""
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "categoria": "$clasificacion.categoria",
                        "semana": {"$week": "$fecha_creacion"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id.semana": -1, "count": -1}
            }
        ]
        return list(self.db.incidentes.aggregate(pipeline))

    # ============================================================
    # COLECCIÓN: riesgos_eticos
    # ============================================================

    def crear_riesgo_etico(self, riesgo: Dict[str, Any]) -> str:
        """Crea un nuevo riesgo ético."""
        riesgo["fecha_registro"] = datetime.now()
        resultado = self.db.riesgos_eticos.insert_one(riesgo)
        return str(resultado.inserted_id)

    def obtener_riesgo(self, riesgo_id: str) -> Optional[Dict]:
        """Obtiene un riesgo ético por su ID."""
        return self.db.riesgos_eticos.find_one({"_id": riesgo_id})

    def listar_riesgos(self, categoria: Optional[str] = None) -> List[Dict]:
        """Lista riesgos éticos, opcionalmente por categoría."""
        filtro = {"categoria": categoria} if categoria else {}
        return list(self.db.riesgos_eticos.find(filtro))

    def actualizar_riesgo(self, riesgo_id: str, actualizacion: Dict) -> bool:
        """Actualiza un riesgo ético."""
        resultado = self.db.riesgos_eticos.update_one(
            {"_id": riesgo_id},
            {"$set": actualizacion}
        )
        return resultado.modified_count > 0

    def eliminar_riesgo(self, riesgo_id: str) -> bool:
        """Elimina un riesgo ético."""
        resultado = self.db.riesgos_eticos.delete_one({"_id": riesgo_id})
        return resultado.deleted_count > 0

    def calcular_riesgo_residual(self, riesgo_id: str) -> Dict:
        """Calcula el riesgo residual (antes y después de mitigación)."""
        riesgo = self.obtener_riesgo(riesgo_id)
        if not riesgo:
            return {}

        probabilidad = riesgo.get("probabilidad", 0)
        impacto = riesgo.get("impacto", 0)
        mitigacion = riesgo.get("mitigacion", "")

        # Riesgo inicial
        riesgo_inicial = probabilidad * impacto

        # Si hay mitigación, reducimos la probabilidad (estimación simple)
        if mitigacion:
            probabilidad_reducida = max(1, probabilidad - 1)
            riesgo_residual = probabilidad_reducida * impacto
        else:
            riesgo_residual = riesgo_inicial

        return {
            "riesgo_inicial": riesgo_inicial,
            "riesgo_residual": riesgo_residual,
            "reduccion": riesgo_inicial - riesgo_residual,
            "mitigacion_aplicada": bool(mitigacion)
        }

    # ============================================================
    # COLECCIÓN: evaluaciones_llm
    # ============================================================

    def registrar_evaluacion_llm(self, evaluacion: Dict[str, Any]) -> str:
        """Registra una evaluación del LLM."""
        evaluacion["fecha_registro"] = datetime.now()
        resultado = self.db.evaluaciones_llm.insert_one(evaluacion)
        return str(resultado.inserted_id)

    def obtener_evaluaciones(self, modelo: Optional[str] = None) -> List[Dict]:
        """Obtiene evaluaciones, opcionalmente por modelo."""
        filtro = {"modelo": modelo} if modelo else {}
        return list(self.db.evaluaciones_llm.find(filtro).sort("fecha_registro", -1))

    def obtener_estadisticas_llm(self) -> Dict:
        """Obtiene estadísticas de las evaluaciones del LLM."""
        pipeline = [
            {
                "$group": {
                    "_id": "$modelo",
                    "count": {"$sum": 1},
                    "latencia_promedio": {"$avg": "$latencia"},
                    "coincidencias": {"$sum": {"$cond": [{"$eq": ["$coincidio_con_reglas", True]}, 1, 0]}}
                }
            }
        ]
        resultados = list(self.db.evaluaciones_llm.aggregate(pipeline))
        return {r["_id"]: r for r in resultados}

    # ============================================================
    # MÉTODOS GENERALES
    # ============================================================

    def cerrar(self):
        """Cierra la conexión a MongoDB."""
        if self.client:
            self.client.close()
            print("✓ Conexión a MongoDB cerrada")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cerrar()
