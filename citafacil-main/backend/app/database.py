"""Conexión a la base de datos con SQLAlchemy.

Funciona con SQLite (local) y PostgreSQL (producción) según DATABASE_URL.
"""
from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


def _normalize_url(url: str) -> str:
    # Render/Heroku entregan "postgres://", SQLAlchemy espera "postgresql://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_url(settings.database_url)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Agrega columnas nuevas a bases existentes (sin migraciones externas)."""
    inspector = inspect(engine)
    if "appointments" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("appointments")}
    if "customer_email" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE appointments "
                    "ADD COLUMN customer_email VARCHAR(120) NOT NULL DEFAULT ''"
                )
            )
