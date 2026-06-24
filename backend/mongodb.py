import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "aldimi_chat_db")

client = None
db = None

try:
    # Intento de conexión con un timeout corto de 2 segundos
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
    db = client[MONGODB_DB]
    # Comprobar si el servidor está activo
    client.server_info()
    print(f"Conectado a MongoDB en {MONGODB_URL}, BD: {MONGODB_DB}")
except Exception as e:
    print(f"Advertencia: No se pudo conectar a MongoDB ({e}).")
    print("Los logs de chat se guardarán en modo de fallback en consola.")
    db = None

def log_chat(user_message: str, bot_response: str, sentiment: str = None):
    """
    Guarda la interacción en MongoDB. Si falla o no está conectado, 
    registra la entrada en la consola como plan de contingencia.
    """
    log_entry = {
        "user_message": user_message,
        "bot_response": bot_response,
        "sentiment": sentiment,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    if db is not None:
        try:
            db.chat_logs.insert_one(log_entry)
            print("Log de chat guardado exitosamente en MongoDB.")
            return True
        except Exception as e:
            print(f"Error al guardar log de chat en MongoDB: {e}")
            
    print(f"[FALLBACK LOG DE CHAT]: {log_entry}")
    return False
