"""
crud.py — Lógica de negócio / operações no banco de dados.

Funções puras que recebem uma Session e retornam dados ou efetuam mutações.
"""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Defeito, Lote, SistemaEstado
from schemas import DefeitoPorHorario, InspecaoRegistrar


# ──────────────────────────────────────
# Helpers
# ──────────────────────────────────────
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def obter_sistema_estado(db: Session) -> SistemaEstado:
    """Retorna (ou cria) o registro singleton id=1."""
    estado = db.get(SistemaEstado, 1)
    if estado is None:
        estado = SistemaEstado(id=1, cartas_totais=0, cartas_defeituosas=0, sequencia_atual=0)
        db.add(estado)
        db.commit()
        db.refresh(estado)
    return estado


def obter_lote_ativo(db: Session) -> Lote | None:
    """Retorna o lote com status EM_ANDAMENTO (ou None)."""
    return db.query(Lote).filter(Lote.status == "EM_ANDAMENTO").first()


import base64
import os
import uuid

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def salvar_imagem_base64(imagem_str: str | None) -> str | None:
    """Se a imagem for base64 (data:image/... ou raw), salva em disco e retorna a URL relativa /uploads/..."""
    if not imagem_str:
        return None

    if imagem_str.startswith("data:image"):
        try:
            header, encoded = imagem_str.split(",", 1)
            ext = "png" if "png" in header else "jpg"
            data = base64.b64decode(encoded)
            filename = f"defeito_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(data)
            return f"/uploads/{filename}"
        except Exception:
            return imagem_str

    # Se for raw base64 longo sem header
    if len(imagem_str) > 200 and not imagem_str.startswith("http") and not imagem_str.startswith("/") and not imagem_str.startswith("imagens/"):
        try:
            data = base64.b64decode(imagem_str)
            filename = f"defeito_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(data)
            return f"/uploads/{filename}"
        except Exception:
            return imagem_str

    return imagem_str


# ──────────────────────────────────────
# Lógica de Ingestão de Inspeção
# ──────────────────────────────────────
def registrar_inspecao_com_dados(
    db: Session,
    possui_defeito: bool,
    tipo_defeito: str | None = None,
    grau_confiabilidade: float | None = None,
    imagem: str | None = None,
) -> dict:
    estado = obter_sistema_estado(db)
    lote = obter_lote_ativo(db)

    # 1) Incrementa contador global de cartas
    estado.cartas_totais += 1

    # 2) Incrementa contador do lote ativo (se existir)
    if lote:
        lote.cartas_totais += 1

    # 3) Se a carta tem defeito
    if possui_defeito:
        estado.cartas_defeituosas += 1
        estado.sequencia_atual += 1

        if lote:
            lote.cartas_defeituosas += 1

        imagem_final = salvar_imagem_base64(imagem)

        defeito = Defeito(
            id_lote=lote.id if lote else None,
            tipo_defeito=tipo_defeito or "Indefinido",
            grau_confiabilidade=grau_confiabilidade,
            imagem=imagem_final,
        )
        db.add(defeito)
    else:
        # Zera sequência de falhas consecutivas
        estado.sequencia_atual = 0

    db.commit()
    db.refresh(estado)

    return {
        "mensagem": "Inspeção registrada com sucesso.",
        "cartas_totais_global": estado.cartas_totais,
        "sequencia_atual": estado.sequencia_atual,
    }


def registrar_inspecao(db: Session, payload: InspecaoRegistrar) -> dict:
    return registrar_inspecao_com_dados(
        db=db,
        possui_defeito=payload.possui_defeito,
        tipo_defeito=payload.tipo_defeito,
        grau_confiabilidade=payload.grau_confiabilidade,
        imagem=payload.imagem,
    )


# ──────────────────────────────────────
# POST /api/lote/iniciar
# ──────────────────────────────────────
def iniciar_lote(db: Session) -> Lote:
    # Encerra qualquer lote ativo existente
    lote_ativo = obter_lote_ativo(db)
    if lote_ativo:
        lote_ativo.status = "CONCLUIDO"
        lote_ativo.fim_leitura = _utcnow()

    novo_lote = Lote(
        cartas_totais=0,
        cartas_defeituosas=0,
        status="EM_ANDAMENTO",
    )
    db.add(novo_lote)
    db.commit()
    db.refresh(novo_lote)
    return novo_lote


# ──────────────────────────────────────
# POST /api/lote/encerrar
# ──────────────────────────────────────
def encerrar_lote(db: Session) -> Lote | None:
    lote = obter_lote_ativo(db)
    if lote is None:
        return None

    lote.status = "CONCLUIDO"
    lote.fim_leitura = _utcnow()
    db.commit()
    db.refresh(lote)
    return lote


# ──────────────────────────────────────
# GET /api/dashboard-summary
# ──────────────────────────────────────
def obter_dashboard_summary(db: Session) -> dict:
    estado = obter_sistema_estado(db)
    lote = obter_lote_ativo(db)

    # --- Defeitos por horário (blocos de 10 min do lote ativo) ---
    defeitos_horario: list[DefeitoPorHorario] = []
    if lote:
        # Agrupa defeitos do lote ativo por hora:minuto truncado para intervalo de 10 min
        rows = (
            db.query(Defeito)
            .filter(Defeito.id_lote == lote.id)
            .order_by(Defeito.timestamp)
            .all()
        )
        buckets: dict[str, int] = {}
        for d in rows:
            ts: datetime = d.timestamp
            minuto_truncado = (ts.minute // 10) * 10
            chave = f"{ts.hour:02d}:{minuto_truncado:02d}"
            buckets[chave] = buckets.get(chave, 0) + 1

        defeitos_horario = [
            DefeitoPorHorario(horario=h, quantidade=q)
            for h, q in sorted(buckets.items())
        ]

    # --- Últimos defeitos (10 mais recentes) ---
    ultimos = (
        db.query(Defeito)
        .order_by(Defeito.timestamp.desc())
        .limit(10)
        .all()
    )

    return {
        "lote": lote,
        "sistema": estado,
        "defeitos_por_horario": defeitos_horario,
        "ultimos_defeitos": ultimos,
    }
