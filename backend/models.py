from sqlalchemy import Column, Integer, String, Text, DateTime
from .database import Base
import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    doc_type = Column(String)  # DNI, Receta, Boleta, etc.
    extracted_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    sentiment = Column(String, nullable=True) # Para RF-IAN-04
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
