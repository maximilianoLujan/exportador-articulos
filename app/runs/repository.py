from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExtractedItem, ExtractionRun


class RunsRepository:
    """Acceso a datos para procesos (runs) e items extraídos."""

    def __init__(self, db: Session):
        self.db = db

    def list_processes(self, limit: int = 50) -> list[ExtractionRun]:
        return (
            self.db.execute(
                select(ExtractionRun).order_by(ExtractionRun.id.desc()).limit(limit)
            )
            .scalars()
            .all()
        )

    def get_process(self, process_id: int) -> ExtractionRun | None:
        return self.db.get(ExtractionRun, process_id)

    def list_items(self, process_id: int) -> list[ExtractedItem]:
        return (
            self.db.execute(
                select(ExtractedItem)
                .where(ExtractedItem.run_id == process_id)
                .order_by(ExtractedItem.id.asc())
            )
            .scalars()
            .all()
        )

    def list_all_items(self) -> list[ExtractedItem]:
        return (
            self.db.execute(select(ExtractedItem).order_by(ExtractedItem.id.asc()))
            .scalars()
            .all()
        )
