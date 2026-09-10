"""
schemas.py — Schemas Pydantic v2 para validação de entrada e serialização de saída.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ────────────────────────────────────────────
# Entrada  —  POST /api/inspecao/registrar
# ────────────────────────────────────────────
class InspecaoRegistrar(BaseModel):
    possui_defeito: bool
    tipo_defeito: Optional[str] = None
    grau_confiabilidade: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    imagem: Optional[str] = None


# ────────────────────────────────────────────
# Saída  —  Componentes do dashboard-summary
# ────────────────────────────────────────────
class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cartas_totais: int
    cartas_defeituosas: int
    inicio_leitura: Optional[datetime] = None
    fim_leitura: Optional[datetime] = None


class SistemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cartas_totais: int
    cartas_defeituosas: int
    sequencia_atual: int


class DefeitoPorHorario(BaseModel):
    horario: str
    quantidade: int


class DefeitoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: Optional[int] = None
    tipo_defeito: str
    grau_confiabilidade: Optional[float] = None
    imagem: Optional[str] = None
    timestamp: datetime


class DashboardSummary(BaseModel):
    lote: Optional[LoteOut] = None
    sistema: SistemaOut
    defeitos_por_horario: list[DefeitoPorHorario]
    ultimos_defeitos: list[DefeitoOut]


# ────────────────────────────────────────────
# Saída  —  POST /api/lote/iniciar
# ────────────────────────────────────────────
class LoteIniciarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    inicio_leitura: datetime


# ────────────────────────────────────────────
# Saída genérica de confirmação
# ────────────────────────────────────────────
class MensagemOut(BaseModel):
    mensagem: str
