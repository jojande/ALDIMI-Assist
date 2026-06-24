from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from .database import engine, Base, get_db
from .models import DniProfile, RecetaProfile, ReciboProfile
from .mongodb import log_chat
from ia_models.vision import classify_document, extract_text, extract_document_info, init_vision_models
from ia_models.nlp import chatbot
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import shutil
import os

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- [Lifespan] Inicializando Modelos IA en Memoria ---")
    try:
        init_vision_models()
        print("--- [Lifespan] Modelos cargados exitosamente ---")
    except Exception as e:
        print(f"Error al inicializar modelos en lifespan: {e}")
    yield
    print("--- [Lifespan] Liberando recursos ---")

# Create PostgreSQL tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ALDIMI Core AI API", lifespan=lifespan)

# Ensure data directories exist
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
    Endpoint para cargar documentos, clasificarlos con MobileNetV3, 
    procesarlos con EasyOCR estructurado y guardar perfiles en PostgreSQL.
    """
    file_path = f"data/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 1. Clasificación mediante red convolucional MobileNetV3
        doc_type = classify_document(file_path)
        
        # 2. Extracción de texto plano (OCR)
        raw_text = extract_text(file_path)
        
        # 3. Extracción de información de perfil estructurada
        profile = extract_document_info(file_path, doc_type)
        
        # 4. Guardar perfil correspondiente en PostgreSQL
        db_doc = None
        if doc_type == "DNI":
            db_doc = DniProfile(
                filename=file.filename,
                nombres=profile.get("nombres", ""),
                apellidos=profile.get("apellidos", ""),
                cui_dni=profile.get("cui_dni", "")
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
        elif doc_type == "RECETA":
            meds_list = profile.get("medicamentos", [])
            meds_str = ", ".join(meds_list) if isinstance(meds_list, list) else str(meds_list)
            db_doc = RecetaProfile(
                filename=file.filename,
                paciente=profile.get("paciente", ""),
                diagnostico=profile.get("diagnostico", ""),
                medicamentos=meds_str
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
        elif doc_type == "BOLETA":
            db_doc = ReciboProfile(
                filename=file.filename,
                nro_recibo=profile.get("nro_recibo", ""),
                donante=profile.get("donante", ""),
                dni_ruc=profile.get("dni_ruc", ""),
                valoracion=profile.get("valoracion", "")
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
        else:
            # Fallback en caso de clasificador no mapeado (ej: OTRO)
            # Guardamos un DniProfile genérico vacío
            db_doc = DniProfile(
                filename=file.filename,
                nombres="Desconocido",
                apellidos="Desconocido",
                cui_dni=""
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
            
        return {
            "id": db_doc.id,
            "filename": file.filename,
            "doc_type": doc_type,
            "extracted_text": raw_text
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR EN ENDPOINT UPLOAD: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_with_bot(request: ChatRequest):
    """
    Endpoint para interactuar con el chatbot RAG (NLP). 
    Analiza riesgo psicosocial e inserta logs de conversación en MongoDB.
    """
    try:
        # 1. Obtener respuesta del chatbot (RAG + Ollama/TF-IDF)
        response_text = chatbot.get_response(request.message, request.history)
        
        # 2. Análisis de riesgo psicosocial híbrido en reportes
        sentiment = None
        if "observación" in request.message.lower() or "reporte" in request.message.lower() or "comportamiento" in request.message.lower():
            sentiment = chatbot.analyze_sentiment(request.message)
        
        # 3. Guardar log de conversación en MongoDB (Hito 6)
        log_chat(
            user_message=request.message,
            bot_response=response_text,
            sentiment=sentiment
        )
        
        return {
            "response": response_text,
            "sentiment": sentiment
        }
    except Exception as e:
        import traceback
        print(f"ERROR EN ENDPOINT CHAT: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/data")
def get_ml_data(db: Session = Depends(get_db)):
    """
    Endpoint consolidado para exponer los perfiles de PostgreSQL 
    al equipo de Machine Learning (RF-BE-03).
    """
    try:
        dnis = db.query(DniProfile).all()
        recetas = db.query(RecetaProfile).all()
        recibos = db.query(ReciboProfile).all()
        
        return {
            "dnis": [
                {
                    "id": d.id, "filename": d.filename, "nombres": d.nombres, 
                    "apellidos": d.apellidos, "cui_dni": d.cui_dni, "created_at": d.created_at
                } for d in dnis
            ],
            "recetas": [
                {
                    "id": r.id, "filename": r.filename, "paciente": r.paciente, 
                    "diagnostico": r.diagnostico, "medicamentos": r.medicamentos, "created_at": r.created_at
                } for r in recetas
            ],
            "recibos": [
                {
                    "id": rc.id, "filename": rc.filename, "nro_recibo": rc.nro_recibo, 
                    "donante": rc.donante, "dni_ruc": rc.dni_ruc, "valoracion": rc.valoracion, "created_at": rc.created_at
                } for rc in recibos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve Static Files (Frontend HTML/JS/CSS)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
