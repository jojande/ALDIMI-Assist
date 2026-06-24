from sqlalchemy import Column, Integer, String, Text, DateTime
from .database import Base
import datetime

class DniProfile(Base):
    __tablename__ = "dni_profiles"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    nombres = Column(String, nullable=True)
    apellidos = Column(String, nullable=True)
    cui_dni = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RecetaProfile(Base):
    __tablename__ = "receta_profiles"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    paciente = Column(String, nullable=True)
    diagnostico = Column(String, nullable=True)
    medicamentos = Column(Text, nullable=True)  # Guardado como lista formateada en texto
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ReciboProfile(Base):
    __tablename__ = "recibo_profiles"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    nro_recibo = Column(String, nullable=True)
    donante = Column(String, nullable=True)
    dni_ruc = Column(String, nullable=True)
    valoracion = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
