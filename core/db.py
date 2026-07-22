"""SQLAlchemy database engine and session factory."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

_engine = None
_SessionLocal = None


def _db_path() -> str:
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        return db_url
    root = Path(__file__).resolve().parents[1]
    db_dir = root / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_dir / 'callgist.db'}"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_db_path(), echo=False, future=True)
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db() -> None:
    from core.db_models import Base

    Base.metadata.create_all(bind=get_engine())
