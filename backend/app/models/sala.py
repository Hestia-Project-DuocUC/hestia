from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Sala(Base):
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String)
    descripcion = Column(String)

    insumos = relationship("Insumo", back_populates="sala")