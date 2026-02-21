from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.memories.repository import MemoriesRepository, get_memories_repository


class MemoriesService:
    def __init__(self, repository: MemoriesRepository):
        self.repository = repository

    def list_memories(self):
        return self.repository.list_all()


def get_memories_service(
    db: Session = Depends(get_db),
):
    repository = get_memories_repository(db)
    return MemoriesService(repository)
