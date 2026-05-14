from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Insumo(Base):
    __tablename__ = "insumos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=0)

    # Soft-delete: un insumo inactivo desaparece de listados, alertas y
    # exportaciones, pero su fila se conserva para no romper la trazabilidad
    # de movimientos historicos (movimientos.insumo_id es FK NOT NULL).
    # Reactivable via PUT activo=true.
    activo = Column(
        Boolean, default=True, nullable=False, server_default="true"
    )

    sala_id = Column(Integer, ForeignKey("salas.id"))
    categoria_id = Column(Integer, ForeignKey("categorias.id"))

    sala = relationship("Sala", back_populates="insumos")
    categoria = relationship("Categoria", back_populates="insumos")
    movimientos = relationship("Movimiento", back_populates="insumo")
