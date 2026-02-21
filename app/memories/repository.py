from __future__ import annotations

from sqlalchemy.orm import Session
from app.db.models import Document


class MemoriesRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()


def get_memories_repository(db: Session):
    return MemoriesRepository(db)
