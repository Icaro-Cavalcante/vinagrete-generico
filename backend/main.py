"""
main.py — Ponto de entrada da aplicação FastAPI.

Execução:
    uvicorn main:app --reload --port 8000
"""

import os
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from crud import (
    UPLOAD_DIR,
    encerrar_lote,
    iniciar_lote,
    obter_dashboard_summary,
    registrar_inspecao,
    registrar_inspecao_com_dados,
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

# Servir pasta de uploads de imagens de defeitos
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
# Rotas — Ingestão de dados (Raspberry Pi / Visão)
# ──────────────────────────────────────
@app.post("/api/inspecao/registrar", response_model=MensagemOut)
def rota_registrar_inspecao(
    payload: InspecaoRegistrar,
    db: Session = Depends(get_db),
):
    """Registra inspeção via JSON (suporta imagem em Base64, URL ou caminho)."""
    resultado = registrar_inspecao(db, payload)
    return MensagemOut(mensagem=resultado["mensagem"])


@app.post("/api/inspecao/registrar-com-foto", response_model=MensagemOut)
async def rota_registrar_inspecao_com_foto(
    possui_defeito: bool = Form(...),
    tipo_defeito: Optional[str] = Form(None),
    grau_confiabilidade: Optional[float] = Form(None),
    foto: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Registra inspeção recebendo arquivo de imagem diretamente (multipart/form-data)."""
    imagem_url = None
    if foto and foto.filename:
        ext = foto.filename.split(".")[-1] if "." in foto.filename else "jpg"
        filename = f"defeito_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        conteudo = await foto.read()
        with open(filepath, "wb") as f:
            f.write(conteudo)
        imagem_url = f"/uploads/{filename}"

    resultado = registrar_inspecao_com_dados(
        db=db,
        possui_defeito=possui_defeito,
        tipo_defeito=tipo_defeito,
        grau_confiabilidade=grau_confiabilidade,
        imagem=imagem_url,
    )
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
