from __future__ import annotations

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _default_sqlite_url() -> str:
    # Stored in project root by default.
    return "sqlite:///./nodexl.db"


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
