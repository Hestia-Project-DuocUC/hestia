from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Insumo(Base):
    __tablename__ = "insumos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=0)

    sala_id = Column(Integer, ForeignKey("salas.id"))
    categoria_id = Column(Integer, ForeignKey("categorias.id"))

    sala = relationship("Sala", back_populates="insumos")
    categoria = relationship("Categoria", back_populates="insumos")
    movimientos = relationship("Movimiento", back_populates="insumo")