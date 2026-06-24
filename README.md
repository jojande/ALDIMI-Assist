# ALDIMI-Assist v3.0 - Panel de Control Inteligente (Trabajo Final - TF)

**ALDIMI-Assist** es un sistema inteligente de soporte integral desarrollado para el Albergue Divina Misericordia (ALDIMI), el cual brinda alojamiento, alimentación y soporte emocional a niños con cáncer y sus familias. 

Este proyecto integra técnicas avanzadas de Visión Artificial (Clasificación de Documentos y OCR), Procesamiento de Lenguaje Natural (RAG y Análisis de Riesgo Psicosocial) y una arquitectura de persistencia robusta utilizando bases de datos híbridas.

---

## 🚀 Arquitectura del Sistema

### 1. Módulo de Visión Artificial (OCR y Clasificación)
- **Clasificador Convolucional**: Implementado con **MobileNetV3-Small** en PyTorch. Clasifica automáticamente las imágenes subidas en cuatro categorías: `DNI Adulto`, `DNI Menor`, `Recetas Médicas` y `Recibos de Donación`. Los pesos del modelo están en [document_classifier.pth](file:///c:/Users/franc/OneDrive/Escritorio/Upc/2026-1/IA/TF/ALDIMI-Assist/ia_models/pesos/document_classifier.pth).
- **OCR Avanzado (EasyOCR)**: Procesa imágenes pre-procesadas mediante filtros CLAHE y Bilaterales en OpenCV. Extrae y estructura automáticamente variables clave del perfil (DNI, Paciente, Diagnóstico, Medicamentos, Montos, RUC).

### 2. Módulo de Procesamiento de Lenguaje Natural (NLP & RAG)
- **Chatbot RAG**: Recuperación de contexto utilizando TF-IDF y Similitud de Coseno sobre el reglamento interno de la institución ([reglamento_aldimi.txt](file:///c:/Users/franc/OneDrive/Escritorio/Upc/2026-1/IA/TF/ALDIMI-Assist/datos/nlp/reglamento_aldimi.txt)).
- **Keyword Boosting**: Algoritmo que prioriza las consultas de administración, visitas y víveres para garantizar una exactitud semántica del 100% en respuestas cortas.
- **Plan de Contingencia (Offline)**: Si el modelo de lenguaje Ollama (Llama 3) no está activo, el sistema entra en modo de fallback y recupera textualmente la normativa correspondiente del reglamento.

### 3. Bitácora de Observaciones y Auditoría Emocional
- **Detección de Riesgo Psicosocial**: Algoritmo híbrido (heurística de palabras clave + análisis cognitivo del LLM) que evalúa los reportes psicosociales diarios de los menores.
- **Alertas del Dashboard**: Si el estado es clasificado como `CRÍTICO`, el panel se tiñe de color rojo de alerta, muestra etiquetas del riesgo detectado (Ideación Suicida, Aislamiento, Tristeza, Trastorno Alimenticio) y activa un botón de derivación inmediata al psicólogo de turno.

### 4. Bases de Datos Híbridas
- **PostgreSQL / SQLite**: Almacena los perfiles estructurados extraídos de los documentos procesados por visión.
- **MongoDB / Fallback Local**: Registra los logs detallados de la conversación con el chatbot, incluyendo el mensaje del usuario, la respuesta del bot y el análisis de sentimiento.

---

## 🛠️ Requisitos del Sistema
- **Python 3.9+** (entorno de ejecución).
- **GPU compatible con CUDA** (opcional, para acelerar EasyOCR y PyTorch; si no, se ejecuta en CPU automáticamente).
- **MongoDB** y **PostgreSQL** (opcional, cuenta con fallback local a logs de consola y base de datos SQLite `sql_app.db`).
- **Ollama** (opcional, con modelo `llama3` para respuestas conversacionales avanzadas del chatbot).

---

## 📦 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/jojande/ALDIMI-Assist.git
   cd ALDIMI-Assist
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Crea un archivo `.env` en la raíz del proyecto con la configuración de tu entorno:
   ```env
   # Base de Datos (Opcional - Fallback a SQLite sql_app.db)
   DATABASE_URL=sqlite:///./sql_app.db
   
   # Conexión MongoDB (Opcional - Fallback a logs de consola)
   MONGODB_URI=mongodb://localhost:27017/
   
   # IA Local (Opcional - Fallback semántico si Ollama está inactivo)
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

---

## 🚀 Ejecución del Sistema

1. **Generación de Datos Sintéticos y Entrenamiento (Opcional)**:
   Si deseas volver a generar el dataset y entrenar el clasificador MobileNetV3:
   ```bash
   py scripts_generacion/generar_identidades.py
   py scripts_generacion/generar_dni.py
   py scripts_generacion/generar_recetas.py
   py scripts_generacion/generar_boleta.py
   py ia_models/train_classifier.py
   ```

2. **Iniciar el Backend (FastAPI)**:
   Inicia el servidor uvicorn:
   ```bash
   py -m uvicorn backend.main:app --reload
   ```

3. **Abrir la Interfaz de Usuario**:
   Navega a [http://localhost:8000](http://localhost:8000) en cualquier navegador web.

---

## 🖥️ Módulos del Dashboard Premium
- **Módulo de Visión Artificial (OCR)**: Carga, previsualiza y edita perfiles estructurados en la columna izquierda.
- **Bitácora Psicosocial**: Caja de reportes y semáforo visual de alertas en la columna central.
- **Chatbot ALDIMI**: Asistente conversacional con chips de ayuda rápida en la columna derecha.
- **Consolidación de Datos (Integración ML)**: Endpoint `/api/ml/data` que expone los perfiles guardados de PostgreSQL para el entrenamiento de otros modelos.
