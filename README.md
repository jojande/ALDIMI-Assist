# ALDIMI Core AI

Prototipo de sistema OCR y Chatbot para el albergue ALDIMI.

## Requisitos
- Python 3.9+
- Tesseract OCR instalado en el sistema.
- PostgreSQL instalado y configurado.

## Instalación
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`.
3. Activar el entorno virtual: `venv\Scripts\activate`.
4. Instalar dependencias: `pip install -r requirements.txt`.
5. Configurar el archivo `.env` con tus credenciales:
   - `DATABASE_URL`: URL de tu base de datos PostgreSQL.
   - `OPENAI_API_KEY`: Tu clave de API de OpenAI.
   - `TESSERACT_CMD`: Ruta al ejecutable de Tesseract (ej: `C:\Program Files\Tesseract-OCR\tesseract.exe`).

## Ejecución
Ejecutar el servidor desde la raíz del proyecto:
```bash
uvicorn backend.main:app --reload
```
Luego abre `http://localhost:8000` en tu navegador para ver la interfaz.

## Funcionalidades
- **Módulo de Visión**: Sube imágenes de DNI, recetas o boletas para extraer texto y clasificarlas.
- **Asistente Virtual**: Consulta el reglamento de visitas o reporta observaciones diarias. El sistema detectará riesgos psicosociales automáticamente.
- **API para ML**: Los datos extraídos están disponibles en `/api/ml/data` para modelos predictivos.
