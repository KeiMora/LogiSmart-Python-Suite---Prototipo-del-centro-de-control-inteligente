# Guía de Uso - LogiSmart

## Estado del Sistema
✓ MongoDB: Conectado (base de datos: `agente`)
✓ Ollama: Conectado (modelo: llama3.2)
✓ Datos de ejemplo: Cargados (3 camiones, 4 accesos, 2 incidentes, 3 riesgos)

## Pasos para usar la aplicación

### 1. Iniciar la aplicación
```bash
cd logismart
python3 main.py
```

### 2. Conectar a MongoDB
- En la interfaz gráfica, ve a la pestaña "Panel de Control"
- Haz clic en el botón "Conectar MongoDB"
- El botón cambiará a "✓ Conectado" cuando sea exitoso
- El indicador en el asistente cambiará a "🟢 Conectado a MongoDB"

### 3. Gestión de Camiones (NUEVO)
- Ve a la pestaña "🚛 Gestión Camiones"
- **Ver camiones registrados:**
  - La lista de camiones se carga automáticamente desde MongoDB
  - Haz clic en "Refrescar" para recargar
  - Muestra: ID, Placa, Empresa, Autorización, Certificación, Materiales Peligrosos

- **Registrar un nuevo camión:**
  - El ID se genera automáticamente (CAM-001, CAM-002, etc.)
  - Completa el formulario con:
    - Placa (ej: JKL-3456)
    - Empresa (ej: Transportes Rápidos)
    - Peso Máximo (kg)
    - Marca las casillas correspondientes
  - Haz clic en "Agregar"
  - El camión se guarda en MongoDB con el ID generado

- **Editar un camión existente:**
  - Haz clic en un camión de la lista
  - Los datos se cargan en el formulario
  - Modifica los campos necesarios
  - Haz clic en "Editar"

- **Eliminar un camión:**
  - Selecciona el camión de la lista
  - Haz clic en "Eliminar"
  - Confirma la eliminación

- **Limpiar formulario:**
  - Haz clic en "Limpiar" para vaciar todos los campos

### 4. Usar el Asistente de IA (MEJORADO)
- Ve a la pestaña "🤖 Asistente LLM"
- **Nuevo diseño visual con:**
  - Indicador de estado de conexión (🔴 rojo si no conectado, 🟢 verde si conectado)
  - Colores de fondo diferentes para mensajes del usuario y del asistente
  - Indicador de "procesando..." mientras el LLM responde
  - Botones de sugerencias para preguntas rápidas
  - Mejor manejo de errores con mensajes claros

- **Preguntas sugeridas (botones clickeables):**
  - "¿Qué camiones hay registrados?"
  - "¿Cuáles son los accesos de hoy?"
  - "¿Qué incidentes hay registrados?"
  - "¿Qué riesgos éticos existen?"

- **Escribe tu propia pregunta:**
  - Escribe en el campo de texto
  - Presiona Enter o haz clic en "📤 Enviar"
  - El botón se deshabilita mientras procesa
  - Verás "procesando..." mientras el LLM genera la respuesta

- **Limpiar conversación:**
  - Haz clic en "🗑️ Limpiar" para reiniciar el chat
  - Restaura el mensaje de bienvenida

### 4. Guardar nuevos datos

#### Simulador de Reglas (Control de Acceso)
- Ve a la pestaña "🚦 Simulador Reglas"
- Configura las variables (P, Q, R, S, V, H)
- Haz clic en "Evaluar"
- El resultado se guarda automáticamente en MongoDB si está conectado

#### Clasificador de Incidentes
- Ve a la pestaña "⚠️ Incidentes"
- Ingresa remitente, asunto y cuerpo del correo
- Haz clic en "Clasificar"
- El incidente se guarda automáticamente en MongoDB si está conectado

## Mejoras en el Asistente de IA

### Interfaz Mejorada
- ✅ Indicador visual de estado de conexión
- ✅ Colores de fondo diferenciados para mejor legibilidad
- ✅ Feedback visual durante el procesamiento
- ✅ Botones de sugerencias para preguntas rápidas
- ✅ Mejor manejo de errores con mensajes descriptivos
- ✅ Campo de entrada con highlight al enfocar
- ✅ Botones con mejor diseño visual

### Funcionalidad Mejorada
- ✅ Procesamiento asíncrono para no bloquear la UI
- ✅ Indicador de "escribiendo..." mientras el LLM responde
- ✅ Mensajes de error claros cuando no hay conexión
- ✅ Sugerencias de preguntas clickeables
- ✅ Actualización automática del estado al conectar MongoDB

## Colecciones en MongoDB
- `camiones`: Información de camiones registrados
- `accesos`: Bitácora de accesos al terminal
- `incidentes`: Incidentes clasificados
- `riesgos_eticos`: Registro de riesgos éticos del sistema
- `evaluaciones_llm`: Evaluaciones del rendimiento del LLM

## Solución de problemas

### El asistente no responde
- Asegúrate de haber conectado a MongoDB primero (ve a Panel de Control)
- Verifica que el indicador diga "🟢 Conectado a MongoDB"
- Verifica que Ollama esté ejecutándose: `pgrep ollama`

### El botón "Enviar" está deshabilitado
- Significa que está procesando una pregunta
- Espera unos segundos mientras el LLM genera la respuesta

### No se guardan datos
- Verifica que el botón de MongoDB diga "✓ Conectado"
- Revisa la barra de estado para mensajes de error

### Verificar datos en MongoDB
```bash
mongosh --eval "use agente; db.getCollectionNames()"
mongosh --eval "use agente; db.camiones.find().pretty()"
```
