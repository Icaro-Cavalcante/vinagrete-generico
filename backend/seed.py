"""
seed.py — Popula o banco de dados com dados iniciais para desenvolvimento.

Execução:
    python seed.py
"""

import random
from datetime import datetime, timedelta, timezone

from database import Base, SessionLocal, engine
from models import Defeito, Lote, SistemaEstado

TIPOS_DEFEITO = [
    "Scratch",
    "Damage",
    "Hole",
    "Corner",
    "Crease",
    "Damaged Corner",
    "Edge Wear",
    "Heavy Wear",
    "Tear",
]


def seed():
    # Cria todas as tabelas (idempotente)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── 1) Singleton sistema_estado ──
        estado = db.get(SistemaEstado, 1)
        if estado is None:
            estado = SistemaEstado(
                id=1,
                cartas_totais=85_400,
                cartas_defeituosas=1_240,
                sequencia_atual=3,
            )
            db.add(estado)
            print("[OK] sistema_estado criado (id=1)")
        else:
            estado.cartas_totais = 85_400
            estado.cartas_defeituosas = 1_240
            estado.sequencia_atual = 3
            print("[OK] sistema_estado atualizado (id=1)")

        # ── 2) Lote concluído de exemplo ──
        lote_antigo = Lote(
            cartas_totais=3_200,
            cartas_defeituosas=45,
            inicio_leitura=datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc),
            fim_leitura=datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc),
            status="CONCLUIDO",
        )
        db.add(lote_antigo)
        db.flush()  # garante ID gerado

        # ── 3) Lote ativo ──
        lote_ativo = Lote(
            cartas_totais=1_450,
            cartas_defeituosas=28,
            inicio_leitura=datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc),
            fim_leitura=None,
            status="EM_ANDAMENTO",
        )
        db.add(lote_ativo)
        db.flush()

        # ── 4) Defeitos do lote ativo ──
        base_time = datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc)
        defeitos = []
        for i in range(28):
            offset_min = random.randint(0, 44)  # até 44 min depois do início
            ts = base_time + timedelta(minutes=offset_min, seconds=random.randint(0, 59))
            defeitos.append(
                Defeito(
                    id_lote=lote_ativo.id,
                    tipo_defeito=random.choice(TIPOS_DEFEITO),
                    grau_confiabilidade=round(random.uniform(0.70, 0.99), 2),
                    imagem=f"imagens/defeito_{i + 1:03d}.png",
                    timestamp=ts,
                )
            )

        # Alguns defeitos do lote antigo
        for i in range(15):
            ts = datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc) + timedelta(
                minutes=random.randint(0, 240)
            )
            defeitos.append(
                Defeito(
                    id_lote=lote_antigo.id,
                    tipo_defeito=random.choice(TIPOS_DEFEITO),
                    grau_confiabilidade=round(random.uniform(0.70, 0.99), 2),
                    imagem=f"imagens/defeito_antigo_{i + 1:03d}.png",
                    timestamp=ts,
                )
            )

        db.add_all(defeitos)
        db.commit()

        print(f"[OK] Lote concluido criado (id={lote_antigo.id})")
        print(f"[OK] Lote ativo criado (id={lote_ativo.id})")
        print(f"[OK] {len(defeitos)} defeitos de teste inseridos")
        print("\n>>> Seed concluido com sucesso!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
