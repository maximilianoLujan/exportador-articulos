from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    runs: Mapped[list["ExtractionRun"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class RunStatus(str, enum.Enum):
    started = "started"
    succeeded = "succeeded"
    failed = "failed"


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    pipeline: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # e.g. articles_v1
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), nullable=False, default=RunStatus.started
    )

    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    finished_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optional: store extracted text for debug/repro (can be large)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship(back_populates="runs")
    items: Mapped[list["ExtractedItem"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ItemType(str, enum.Enum):
    article = "article"
    book = "book"
    book_parts = "book_parts"
    unknown = "unknown"


class ExtractedItem(Base):
    __tablename__ = "extracted_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="CASCADE"), nullable=False
    )

    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType), nullable=False, default=ItemType.unknown
    )

    # Raw chunk as extracted + parsed result. Keep both for traceability.
    raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[ExtractionRun] = relationship(back_populates="items")


Index("ix_extracted_items_run_id", ExtractedItem.run_id)
Index("ix_extracted_items_type", ExtractedItem.item_type)
Index("ix_extracted_items_fingerprint", ExtractedItem.fingerprint)
