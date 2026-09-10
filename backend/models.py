"""
models.py — Modelos ORM SQLAlchemy para o sistema de inspeção.

Tabelas:
  • lotes           — Lotes de produção
  • sistema_estado  — Registro singleton de métricas globais
  • defeitos        — Histórico de cartas defeituosas
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    """Retorna datetime UTC-aware."""
    return datetime.now(timezone.utc)


class Lote(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cartas_totais = Column(Integer, default=0, nullable=False)
    cartas_defeituosas = Column(Integer, default=0, nullable=False)
    inicio_leitura = Column(DateTime, default=_utcnow, nullable=False)
    fim_leitura = Column(DateTime, nullable=True)
    status = Column(String, default="EM_ANDAMENTO", nullable=False)

    # Relacionamento 1:N com defeitos
    defeitos = relationship("Defeito", back_populates="lote", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Lote id={self.id} status={self.status}>"


class SistemaEstado(Base):
    """Registro único (id=1) com contadores globais da máquina."""

    __tablename__ = "sistema_estado"

    id = Column(Integer, primary_key=True, default=1)
    cartas_totais = Column(Integer, default=0, nullable=False)
    cartas_defeituosas = Column(Integer, default=0, nullable=False)
    sequencia_atual = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<SistemaEstado totais={self.cartas_totais} "
            f"defeituosas={self.cartas_defeituosas} "
            f"seq={self.sequencia_atual}>"
        )


class Defeito(Base):
    __tablename__ = "defeitos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_lote = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    tipo_defeito = Column(String, nullable=False)
    grau_confiabilidade = Column(Float, nullable=True)
    imagem = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_utcnow, nullable=False)

    lote = relationship("Lote", back_populates="defeitos")

    def __repr__(self) -> str:
        return f"<Defeito id={self.id} tipo={self.tipo_defeito}>"
