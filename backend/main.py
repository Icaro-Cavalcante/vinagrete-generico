"""
main.py — Ponto de entrada da aplicação FastAPI.

Execução:
    uvicorn main:app --reload --port 8000
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from crud import (
    encerrar_lote,
    iniciar_lote,
    obter_dashboard_summary,
    registrar_inspecao,
)
from database import Base, engine, get_db
from schemas import (
    DashboardSummary,
    InspecaoRegistrar,
    LoteIniciarOut,
    MensagemOut,
)

# ──────────────────────────────────────
# Criação das tabelas no startup
# ──────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ──────────────────────────────────────
# App FastAPI
# ──────────────────────────────────────
app = FastAPI(
    title="Vinagrete Genérico — Inspeção de Cartas",
    description="Backend de controle de qualidade e visão computacional para inspeção de cartas/cartões.",
    version="1.0.0",
)

# ──────────────────────────────────────
# CORS — permite todas as origens
# ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────
# Rotas — Ingestão de dados
# ──────────────────────────────────────
@app.post("/api/inspecao/registrar", response_model=MensagemOut)
def rota_registrar_inspecao(
    payload: InspecaoRegistrar,
    db: Session = Depends(get_db),
):
    """Registra o resultado da inspeção de uma carta (chamado pela câmera/robô)."""
    resultado = registrar_inspecao(db, payload)
    return MensagemOut(mensagem=resultado["mensagem"])


@app.post("/api/lote/iniciar", response_model=LoteIniciarOut)
def rota_iniciar_lote(db: Session = Depends(get_db)):
    """Encerra lote ativo (se houver) e inicia um novo lote de produção."""
    novo_lote = iniciar_lote(db)
    return novo_lote


@app.post("/api/lote/encerrar", response_model=MensagemOut)
def rota_encerrar_lote(db: Session = Depends(get_db)):
    """Encerra o lote ativo atual."""
    lote = encerrar_lote(db)
    if lote is None:
        raise HTTPException(status_code=404, detail="Nenhum lote ativo encontrado.")
    return MensagemOut(mensagem=f"Lote {lote.id} encerrado com sucesso.")


# ──────────────────────────────────────
# Rotas — Dashboard
# ──────────────────────────────────────
@app.get("/api/dashboard-summary", response_model=DashboardSummary)
def rota_dashboard_summary(db: Session = Depends(get_db)):
    """Retorna dados agregados para o dashboard web."""
    return obter_dashboard_summary(db)
