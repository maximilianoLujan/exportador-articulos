from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.runs.repository import RunsRepository


class RunsService:
    def __init__(self, repo: RunsRepository):
        self.repo = repo

    def list_processes(self):
        return self.repo.list_processes()

    def get_process(self, process_id: int):
        return self.repo.get_process(process_id)

    def list_items(self, process_id: int):
        return self.repo.list_items(process_id)


def get_runs_service(db: Session = Depends(get_db)) -> RunsService:
    return RunsService(RunsRepository(db))
