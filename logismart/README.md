# LogiSmart - Sistema de Control Logístico Inteligente

Sistema modular para control de acceso de camiones, clasificación de incidentes y evaluación de riesgos éticos, con persistencia en MongoDB y LLM local (Ollama).

## 📋 Características

### 1. Motor de Reglas Lógicas
- Evaluación de acceso e inspección de camiones usando lógica proposicional
- 4 reglas implementadas:
  - **A (Acceso Estándar)** = P ∧ S ∧ ¬Q
  - **E (Inspección Especial)** = P ∧ (R ∨ Q)
  - **C (Restricción Certificación)** = P ∧ S ∧ ¬V (NUEVA)
  - **T (Restricción Horaria)** = R ∧ ¬H (NUEVA)
- Tablas de verdad generadas automáticamente
- Explicación paso a paso de cada decisión

### 2. Clasificador Híbrido de Incidentes
- Combinación de clasificación por reglas + LLM (Ollama)
- Validación de salida del LLM con Pydantic
- Fallback automático a reglas si el LLM falla
- Estrategia de fusión: prevalece prioridad más alta
- Medición de exactitud, latencia y coincidencias

### 3. Asistente LLM Explicativo (RAG)
- Chat con el sistema para hacer preguntas
- Consulta primero a MongoDB, luego pasa contexto al LLM
- Responde solo con datos recuperados (no alucina)
- Historial de conversación

### 4. Matriz de Riesgos Éticos
- Registro de riesgos por módulo del sistema
- Cálculo de puntaje (probabilidad × impacto)
- Riesgo residual antes/después de mitigación
- Visualización gráfica con matplotlib
- Riesgos predefinidos para el sistema

### 5. Persistencia en MongoDB
- Colecciones:
  - `camiones`: Información de camiones
  - `accesos`: Bitácora de accesos
  - `incidentes`: Incidentes clasificados
  - `riesgos_eticos`: Matriz de riesgos
  - `evaluaciones_llm`: Registro de evaluaciones del LLM
- CRUD completo desde la GUI
- Agregaciones (incidentes por categoría y semana)

### 6. Interfaz Gráfica Completa
- Panel de control con indicadores en tiempo real
- Control de acceso con semáforo visual
- Simulador de tablas de verdad interactivo
- Bandeja de incidentes con clasificación
- Chat con asistente LLM
- Gestión de riesgos éticos con gráficas
- Exportación de reportes (JSON, CSV)
- Configuración del sistema

## 🏗️ Arquitectura

```
logismart/
├── config/
│   └── settings.py          # Configuración centralizada
├── data/
│   ├── __init__.py
│   └── mongodb_repository.py # CRUD y operaciones MongoDB
├── logic/
│   ├── __init__.py
│   ├── motor_reglas.py       # Motor de reglas lógicas
│   ├── clasificador_hibrido.py # Clasificador reglas+LLM
│   ├── asistente_llm.py      # Asistente con RAG
│   └── matriz_riesgos.py    # Matriz de riesgos éticos
├── ui/
│   ├── __init__.py
│   └── main_window.py        # Interfaz gráfica principal
├── __init__.py
├── main.py                   # Punto de entrada
└── requirements.txt          # Dependencias
```

## 📦 Instalación

### Prerrequisitos
- Python 3.8+
- MongoDB (local o Atlas)
- Ollama instalado y ejecutándose (`ollama serve`)

### Instalar dependencias
```bash
cd logismart
pip install -r requirements.txt
```

### Instalar modelo de Ollama
```bash
ollama pull llama3.2
```

### Configurar MongoDB
1. **MongoDB Local:**
   - Instalar MongoDB Community
   - Por defecto en `localhost:27017`

2. **MongoDB Atlas:**
   - Crear clúster gratuito
   - Obtener connection string
   - Configurar en `config/settings.py`

## 🚀 Uso

### Iniciar interfaz gráfica
```bash
cd logismart
python main.py
```

### Ejecutar demo por consola
```bash
python main.py --demo
```

### Uso de la GUI

1. **Conectar MongoDB:**
   - Click en "Conectar MongoDB" en el encabezado
   - Verifica que Ollama esté ejecutándose

2. **Panel de Control:**
   - Ver indicadores en tiempo real
   - Filtrar por fecha
   - Click en "Actualizar"

3. **Control de Acceso:**
   - Activar/desactivar checkboxes P, Q, R, S, V, H
   - Click en "Evaluar"
   - Ver semáforo y explicación
   - Buscar por placa

4. **Simulador Reglas:**
   - Activar interruptores
   - Ver tabla de verdad actualizarse en vivo

5. **Bandeja Incidentes:**
   - Ingresar remitente, asunto, cuerpo
   - Click en "Clasificar"
   - Ver resultado (reglas + LLM)
   - Se guarda automáticamente en MongoDB

6. **Asistente LLM:**
   - Escribir pregunta
   - Enter o click en "Enviar"
   - El asistente consulta MongoDB y responde

7. **Riesgos Éticos:**
   - Ver lista de riesgos
   - Ver gráfica de dispersión
   - Agregar/editar/eliminar riesgos

8. **Reportes:**
   - Exportar a JSON
   - Exportar a CSV (pendiente)
   - Exportar a PDF (pendiente)

9. **Configuración:**
   - Cambiar modelo Ollama
   - Configurar MongoDB
   - Activar/desactivar modo simulación

## 🔧 Configuración

Editar `config/settings.py`:

```python
# MongoDB
config.mongo.host = "localhost"
config.mongo.port = 27017
config.mongo.database = "logismart_db"
config.mongo.connection_string = "mongodb+srv://..."  # Para Atlas

# Ollama
config.ollama.model = "llama3.2"
config.ollama.host = "http://localhost:11434"

# Sistema
config.modo_simulacion = True  # Simula envíos de correo
```

## 📊 Riesgos Éticos del Sistema

El sistema incluye evaluación de sus propios riesgos:

1. **Alucinaciones del LLM** - Probabilidad 3, Impacto 4
   - Mitigación: Validación Pydantic, fallback a reglas

2. **Sesgo en ortografía informal** - Probabilidad 3, Impacto 3
   - Mitigación: Dataset diverso, normalización

3. **Privacidad de datos del conductor** - Probabilidad 3, Impacto 5
   - Mitigación: Cifrado, acceso restringido

4. **Dependencia excesiva de automatización** - Probabilidad 2, Impacto 4
   - Mitigación: Revisión humana, auditoría

5. **Alucinación en asistente RAG** - Probabilidad 2, Impacto 3
   - Mitigación: Solo responder con datos en contexto

## 🧪 Pruebas

Ejecutar pruebas unitarias del script original:
```bash
python ../logiuncodigo.py --tests
```

## 📝 Notas

- El sistema requiere Ollama ejecutándose (`ollama serve`)
- MongoDB debe estar accesible antes de conectar
- En modo simulación, los correos no se envían realmente
- La GUI usa matplotlib para visualización de riesgos

## 🤝 Contribuciones

Este es un proyecto educativo. Las mejoras deben mantener:
- Arquitectura modular por capas
- Separación de datos, lógica y UI
- Validación de entradas
- Manejo de errores robusto
