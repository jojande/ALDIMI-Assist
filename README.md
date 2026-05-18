# ALDIMI Core AI

Prototipo de sistema OCR y Chatbot para el albergue ALDIMI.

## Requisitos del Sistema
- **Python 3.9+**
- **Tesseract OCR**: Instalado en el sistema (con datos de idioma para español).
- **PostgreSQL**: Instalado y con una base de datos creada (ej. `aldimi_db`).
- **Ollama** (Opcional - Para IA Local): Instalado y con el modelo `llama3` descargado.

## Instalación

1. **Clonar el repositorio** o descargar los archivos.
2. **Crear un entorno virtual**:
   ```bash
   python -m venv venv
   ```
3. **Activar el entorno virtual**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Configurar el archivo `.env`**:
   Crea un archivo llamado `.env` en la raíz del proyecto y configura las siguientes variables:
   ```env
   # Base de Datos
   DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/aldimi_db

   # OCR
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

   # IA (Elegir una opción)
   
   # OPCIÓN A: OpenAI (Nube)
   # OPENAI_API_KEY=tu_clave_de_openai

   # OPCIÓN B: Ollama (Local - Recomendado)
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

## Configuración de Ollama (IA Local)
Si decides usar Ollama:
1. Descarga e instala Ollama desde [ollama.com](https://ollama.com/).
2. Descarga el modelo Llama 3:
   ```bash
   ollama pull llama3
   ```
3. Asegúrate de que Ollama esté ejecutándose antes de iniciar el backend.

## Ejecución
Inicia el servidor desde la raíz del proyecto:
```bash
uvicorn backend.main:app --reload
```
Luego abre [http://localhost:8000](http://localhost:8000) en tu navegador.

## Funcionalidades
- **Módulo de Visión (OCR)**: Carga imágenes de DNI, recetas médicas o boletas para extraer texto y clasificarlas automáticamente.
- **Asistente Virtual (NLP)**: Chatbot que responde consultas sobre el reglamento interno y detecta riesgos psicosociales en reportes de evolución.
- **API para ML**: Endpoint `/api/ml/data` que expone los datos extraídos para integración con modelos predictivos.
