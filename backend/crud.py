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


# ──────────────────────────────────────
# POST /api/inspecao/registrar
# ──────────────────────────────────────
def registrar_inspecao(db: Session, payload: InspecaoRegistrar) -> dict:
    estado = obter_sistema_estado(db)
    lote = obter_lote_ativo(db)

    # 1) Incrementa contador global de cartas
    estado.cartas_totais += 1

    # 2) Incrementa contador do lote ativo (se existir)
    if lote:
        lote.cartas_totais += 1

    # 3) Se a carta tem defeito
    if payload.possui_defeito:
        estado.cartas_defeituosas += 1
        estado.sequencia_atual += 1

        if lote:
            lote.cartas_defeituosas += 1

        defeito = Defeito(
            id_lote=lote.id if lote else None,
            tipo_defeito=payload.tipo_defeito or "Indefinido",
            grau_confiabilidade=payload.grau_confiabilidade,
            imagem=payload.imagem,
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
