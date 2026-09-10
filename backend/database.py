"""
database.py — Configuração do engine SQLAlchemy e SessionLocal.

Para trocar de SQLite para PostgreSQL, basta alterar DATABASE_URL:
  postgresql+psycopg2://user:pass@host:5432/dbname
"""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vinagrete.db",
)

# ---------- Engine ----------
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# Habilita WAL e foreign keys para SQLite (melhor concorrência)
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# ---------- Session ----------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------- Base declarativa ----------
Base = declarative_base()


def get_db():
    """Dependency do FastAPI — fornece uma sessão por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
