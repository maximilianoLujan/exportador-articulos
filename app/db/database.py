from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _default_sqlite_url() -> str:
    if getattr(sys, "frozen", False):
        # ejecutándose como exe (PyInstaller)
        base = Path(os.getenv("LOCALAPPDATA", Path.home()))
        app_dir = base / "nodexlapp"
    else:
        # modo desarrollo
        app_dir = Path(__file__).resolve().parents[3]

    app_dir.mkdir(parents=True, exist_ok=True)

    db_path = app_dir / "nodexl.db"
    return f"sqlite:///{db_path}"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", _default_sqlite_url())


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(
            url, future=True, pool_pre_ping=True, connect_args=connect_args
        )
    return _engine


def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), class_=Session, autoflush=False, autocommit=False
        )
    return _SessionLocal


def create_all() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def get_db() -> Session:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Session:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
