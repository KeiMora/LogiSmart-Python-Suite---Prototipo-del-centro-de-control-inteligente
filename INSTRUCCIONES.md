# Instrucciones para los Ejercicios Prácticos

## 📚 Ejercicio 1: p02primertutor_llm.py

### Cambios Realizados

1. **Configuración del Sistema Modificada**
   - Cambié el rol de "profesor de IA" a "asistente financiero especializado"
   - Nuevo enfoque: inversiones y planificación de presupuesto personal
   - Instrucciones adaptadas para contexto financiero

2. **Interfaz Gráfica (tkinter)**
   - Ventana principal con encabezado profesional
   - Área de chat con historial de conversación
   - Campo de entrada para preguntas
   - Botones: Enviar, Resumen del Historial, Limpiar Chat, Salir
   - Colores diferenciados para usuario (azul), asistente (verde) y sistema (gris)
   - Barra de estado con información

3. **Funcionalidad de Resumen del Historial**
   - Botón "Resumen del Historial" abre ventana emergente
   - Muestra estadísticas:
     - Cantidad de preguntas y respuestas
     - Longitud promedio de respuestas
     - Fecha de la sesión
   - Formato legible con monoespaciado

### Cómo Ejecutar

```bash
# Asegúrate de tener Ollama ejecutándose
ollama serve

# Ejecutar el script
python p02primertutor_llm.py
```

### Uso de la GUI

1. Escribe tu pregunta en el campo de entrada
2. Presiona Enter o click en "Enviar"
3. El asistente responderá en el área de chat
4. Click en "Resumen del Historial" para ver estadísticas
5. Click en "Limpiar Chat" para limpiar el área visual (historial se mantiene)
6. Click en "Salir" para cerrar la aplicación

---

## 🏗️ Ejercicio 2: LogiSmart (Transformación Modular de logiuncodigo.py)

### Arquitectura Implementada

```
logismart/
├── config/
│   └── settings.py              # Configuración centralizada
├── data/
│   ├── __init__.py
│   └── mongodb_repository.py    # Capa de datos (MongoDB)
├── logic/
│   ├── __init__.py
│   ├── motor_reglas.py          # Motor de reglas lógicas
│   ├── clasificador_hibrido.py  # Clasificador reglas+LLM
│   ├── asistente_llm.py         # Asistente con RAG
│   └── matriz_riesgos.py        # Matriz de riesgos éticos
├── ui/
│   ├── __init__.py
│   └── main_window.py           # Interfaz gráfica
├── __init__.py
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
└── README.md                    # Documentación
```

### Requerimientos Cumplidos

#### 2.1 MongoDB (Persistencia)
✅ Colecciones implementadas:
- `camiones`: placa, camion_id, empresa, autorización, certificación
- `accesos`: bitácora con P, Q, R, S, resultado A y E, marca de tiempo
- `incidentes`: correo, clasificación, datos extraídos, estado
- `riesgos_eticos`: módulo, descripción, categoría, probabilidad, impacto, mitigación
- `evaluaciones_llm`: prompt, respuesta, modelo, latencia, coincidencia con reglas

✅ CRUD completo implementado en `mongodb_repository.py`
✅ Agregación: incidentes por categoría y semana
✅ Manejo de errores de conexión

#### 2.2 Motor de Reglas (Lógica Proposicional)
✅ Reglas originales conservadas:
- A = P ∧ S ∧ ¬Q
- E = P ∧ (R ∨ Q)

✅ 2 reglas nuevas agregadas:
- C (Restricción Certificación) = P ∧ S ∧ ¬V
  - Bloquea acceso si el conductor tiene autorización pero certificación NO vigente
- T (Restricción Horaria) = R ∧ ¬H
  - Restringe entrada de materiales peligrosos fuera de horario permitido

✅ Tablas de verdad generadas automáticamente
✅ Explicación paso a paso de cada decisión
✅ Detección de contradicciones entre reglas

#### 2.3 Clasificador Híbrido (Reglas + LLM)
✅ LLM recibe correo y devuelve JSON validado con Pydantic
✅ Validación con Pydantic; si inválido, reintentar y luego caer a reglas
✅ Fusión: si LLM y reglas discrepan, prevalece prioridad más alta
✅ Marca `requiere_revision_humana` cuando hay discrepancia
✅ Registro de evaluaciones con latencia y coincidencias

#### 2.4 Asistente LLM Explicativo (RAG)
✅ Chat en la GUI donde el operador puede preguntar
✅ LLM responde solo con datos recuperados de MongoDB
✅ Patrón RAG: consulta primero, contexto después
✅ Cita el registro de origen
✅ Responde "no tengo información" cuando no hay datos

#### 2.5 Matriz de Riesgos Éticos
✅ Cargar y editar riesgos desde la GUI
✅ Gráfica de dispersión (probabilidad vs impacto) con matplotlib
✅ Riesgo residual: puntaje antes y después de mitigación
✅ Riesgos de la propia implementación incluidos:
  - Alucinaciones del LLM
  - Sesgo en correos con ortografía informal
  - Privacidad de datos del conductor
  - Dependencia excesiva de la automatización

#### 3. Interfaz Gráfica
✅ Panel de control con indicadores (camiones atendidos, incidentes abiertos, riesgos críticos)
✅ Filtros por fecha
✅ Control de acceso: formulario P/Q/R/S/V/H, resultado visual (semáforo), explicación
✅ Búsqueda por placa
✅ Simulador de tablas de verdad: interruptores interactivos, tabla en vivo
✅ Bandeja de incidentes: pegar correo, clasificar, ver resultado
✅ Asistente (chat LLM): conversación con historial
✅ Riesgos éticos: gráfica, lista, alta/edición/baja
✅ Reportes: exportar a JSON (CSV y PDF pendientes)
✅ Configuración: modelo Ollama, umbrales, modo simulación
✅ Validación de entradas con mensajes claros
✅ Indicadores de carga mientras responde el LLM
✅ Estados de error amigables

### Instalación y Ejecución

#### 1. Instalar dependencias
```bash
cd logismart
pip install -r requirements.txt
```

Dependencias requeridas:
- `pymongo>=4.0.0` - Cliente MongoDB
- `ollama>=0.1.0` - Cliente para LLM local
- `pydantic>=2.0.0` - Validación de datos
- `matplotlib>=3.5.0` - Gráficas

#### 2. Configurar Ollama
```bash
# Instalar Ollama si no lo tienes
# https://ollama.ai/

# Iniciar Ollama
ollama serve

# Descargar modelo
ollama pull llama3.2
```

#### 3. Configurar MongoDB

**Opción A: MongoDB Local**
```bash
# Instalar MongoDB Community
# https://www.mongodb.com/try/download/community

# Iniciar MongoDB
mongod
```

**Opción B: MongoDB Atlas**
1. Crear cuenta gratuita en https://www.mongodb.com/cloud/atlas
2. Crear clúster
3. Obtener connection string
4. Editar `config/settings.py`:
```python
config.mongo.connection_string = "mongodb+srv://usuario:password@cluster..."
```

#### 4. Ejecutar la aplicación
```bash
cd logismart
python main.py
```

Para demo por consola:
```bash
python main.py --demo
```

### Uso de la GUI

1. **Conectar MongoDB**
   - Click en botón "Conectar MongoDB" (esquina superior izquierda)
   - Verifica que Ollama esté ejecutándose

2. **Panel de Control**
   - Ver indicadores en tiempo real
   - Usar filtros de fecha
   - Click en "Actualizar"

3. **Control de Acceso**
   - Activar checkboxes (P, Q, R, S, V, H)
   - Click en "Evaluar"
   - Ver semáforo (verde/naranja/rojo)
   - Leer explicación paso a paso
   - Buscar camión por placa

4. **Simulador de Reglas**
   - Activar interruptores P, Q, R, S
   - Ver tabla de verdad actualizarse en vivo
   - Entender cómo cambian A y E

5. **Bandeja de Incidentes**
   - Ingresar remitente, asunto, cuerpo del correo
   - Click en "Clasificar"
   - Ver resultado JSON con:
     - Categoría
     - Prioridad
     - Entidades extraídas
     - Método usado (reglas/LLM)
     - Si requiere revisión humana
   - Se guarda automáticamente en MongoDB

6. **Asistente LLM**
   - Escribir pregunta en campo de entrada
   - Presionar Enter
   - El asistente:
     - Consulta MongoDB según la pregunta
     - Pasa contexto al LLM
     - Responde basándose solo en datos
   - Ejemplos de preguntas:
     - "¿Por qué CAM-102 fue enviado a inspección?"
     - "¿Cuántos accesos hubo hoy?"
     - "¿Qué incidentes están abiertos?"
     - "¿Cuáles son los riesgos críticos?"

7. **Riesgos Éticos**
   - Ver lista de riesgos en Treeview
   - Ver gráfica de dispersión (probabilidad vs impacto)
   - Agregar nuevos riesgos (pendiente implementación en GUI)
   - Ver cálculo de riesgo residual

8. **Reportes**
   - Exportar a JSON: guarda matriz de riesgos completa
   - Exportar a CSV: pendiente
   - Exportar a PDF: pendiente

9. **Configuración**
   - Cambiar modelo de Ollama
   - Configurar host de MongoDB
   - Activar/desactivar modo simulación
   - Click en "Guardar Configuración"

### Notas Importantes

1. **Ollama debe estar ejecutándose** antes de usar clasificador LLM
2. **MongoDB debe estar accesible** antes de conectar
3. **En modo simulación**, los correos no se envían realmente
4. **El asistente LLM solo responde** si hay datos en MongoDB
5. **Las gráficas de riesgos** usan matplotlib integrado en tkinter

### Archivo Original

El archivo original `logiuncodigo.py` se mantiene sin modificaciones en el directorio principal como referencia.

### Estructura de Capas

- **Capa de Datos** (`data/`): MongoDBRepository - toda la lógica de persistencia
- **Capa de Lógica** (`logic/`): MotorReglas, ClasificadorHibrido, AsistenteLLM, MatrizRiesgos
- **Capa de UI** (`ui/`): MainWindow - interfaz gráfica completa
- **Configuración** (`config/`): Settings - configuración centralizada

Esta separación permite:
- Fácil testing de cada capa
- Reutilización de componentes
- Mantenimiento simplificado
- Escalabilidad del sistema

---

## 🎯 Competencias Desarrolladas

Al completar estos ejercicios, habrán desarrollado:

1. **Arquitectura por capas** - Separación de datos, lógica y presentación
2. **Persistencia en MongoDB** - CRUD, agregaciones, manejo de errores
3. **Integración de LLM local** - Ollama, validación Pydantic, fallback
4. **RAG (Retrieval-Augmented Generation)** - Consulta a BD + contexto a LLM
5. **Interfaz gráfica completa** - tkinter, matplotlib, manejo de eventos
6. **Evaluación de riesgos éticos** - Matriz, visualización, mitigación
7. **Lógica proposicional** - Tablas de verdad, motor de reglas
8. **Clasificación híbrida** - Fusión de reglas + ML

---

## 📞 Soporte

Para preguntas o problemas:
1. Verificar que Ollama esté ejecutándose (`ollama serve`)
2. Verificar que MongoDB esté accesible
3. Revisar el archivo `logismart/README.md` para más detalles
4. Consultar la documentación de cada módulo en los archivos fuente
