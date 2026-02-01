from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, ExtractedItem, ExtractionRun, ItemType, RunStatus


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint_from_fields(*parts: str) -> str:
    normalized = "|".join(p.strip().lower() for p in parts if p is not None)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PersistedRun:
    document_id: int
    run_id: int


class PersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_document(
        self, *, blob: bytes, filename: str | None, content_type: str | None
    ) -> Document:
        digest = sha256_bytes(blob)
        existing = self.db.execute(
            select(Document).where(Document.sha256 == digest)
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        doc = Document(
            filename=filename,
            content_type=content_type,
            sha256=digest,
            size_bytes=len(blob),
            blob=blob,
        )
        self.db.add(doc)
        self.db.flush()
        return doc

    def start_run(
        self, *, document_id: int, pipeline: str, raw_text: str | None
    ) -> ExtractionRun:
        run = ExtractionRun(
            document_id=document_id,
            pipeline=pipeline,
            status=RunStatus.started,
            raw_text=raw_text,
            started_at=dt.datetime.now(dt.UTC),
        )
        self.db.add(run)
        self.db.flush()
        return run

    def finish_run_success(self, run: ExtractionRun) -> None:
        run.status = RunStatus.succeeded
        run.finished_at = dt.datetime.now(dt.UTC)
        self.db.add(run)

    def finish_run_failed(self, run: ExtractionRun, error: str) -> None:
        run.status = RunStatus.failed
        run.error = error
        run.finished_at = dt.datetime.now(dt.UTC)
        self.db.add(run)

    def add_item(
        self,
        *,
        run_id: int,
        item_type: ItemType,
        raw: str | None,
        data: dict,
        fingerprint: str | None,
        confidence: int | None = None,
        parse_error: str | None = None,
    ) -> ExtractedItem:
        item = ExtractedItem(
            run_id=run_id,
            item_type=item_type,
            raw=raw,
            data=data or {},
            fingerprint=fingerprint,
            confidence=confidence,
            parse_error=parse_error,
        )
        self.db.add(item)
        return item
