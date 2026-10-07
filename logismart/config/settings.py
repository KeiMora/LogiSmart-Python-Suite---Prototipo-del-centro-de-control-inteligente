"""
Configuración del sistema LogiSmart.
Almacena todas las configuraciones centralizadas.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MongoDBConfig:
    """Configuración de conexión a MongoDB."""
    host: str = "localhost"
    port: int = 27017
    database: str = "agente"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: str = "mongodb://localhost:27017"
    # Para Atlas, usar connection_string en lugar de host/port/user/pass


@dataclass
class OllamaConfig:
    """Configuración del LLM local Ollama."""
    model: str = "llama3.2"
    host: str = "http://localhost:11434"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class SistemaConfig:
    """Configuración general del sistema."""
    mongo: MongoDBConfig = field(default_factory=MongoDBConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    modo_simulacion: bool = True  # Si True, simula envíos de correo


# Instancia global de configuración
config = SistemaConfig()
