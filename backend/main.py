from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import Document, ChatLog
from ia_models.vision import extract_text, classify_document
from ia_models.nlp import chatbot
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ALDIMI Core AI API")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint API
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Endpoint para cargar documentos y procesarlos con OCR (RF-BE-01, RF-BE-02).
    """
    file_path = f"data/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Procesar con OCR
        text = extract_text(file_path)
        doc_type = classify_document(text)
        
        # Guardar en base de datos
        db_doc = Document(
            filename=file.filename,
            doc_type=doc_type,
            extracted_text=text
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        return {
            "id": db_doc.id,
            "filename": db_doc.filename,
            "doc_type": db_doc.doc_type,
            "extracted_text": db_doc.extracted_text
        }
    except Exception as e:
        import traceback
        print(f"ERROR EN ENDPOINT: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_bot(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint para interactuar con el Chatbot (RF-IAN-01).
    """
    try:
        # Obtener respuesta del chatbot
        response_text = chatbot.get_response(request.message, request.history)
        
        # Análisis de riesgo (si es una observación)
        sentiment = None
        if "observación" in request.message.lower() or "reporte" in request.message.lower():
            sentiment = chatbot.analyze_sentiment(request.message)
        
        # Guardar log en BD
        db_log = ChatLog(
            user_message=request.message,
            bot_response=response_text,
            sentiment=sentiment
        )
        db.add(db_log)
        db.commit()
        
        return {
            "response": response_text,
            "sentiment": sentiment
        }
    except Exception as e:
        import traceback
        print(f"ERROR EN ENDPOINT: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/data")
def get_ml_data(db: Session = Depends(get_db)):
    """
    Endpoint para que el equipo de ML consuma los datos (RF-BE-03).
    """
    documents = db.query(Document).all()
    return documents

# Serve Static Files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
