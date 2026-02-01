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
    book_part = "book_part"
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


# ---- Domain model (graph-friendly) ----


class PublicationType(str, enum.Enum):
    article = "article"
    book = "book"
    book_part = "book_part"


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[PublicationType] = mapped_column(Enum(PublicationType), nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # provenance
    source_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="SET NULL"), nullable=True
    )
    source_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("extracted_items.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )

    identifiers: Mapped[list["PublicationIdentifier"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan"
    )
    contributors: Mapped[list["PublicationContributor"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan"
    )


class Article(Base):
    __tablename__ = "articles"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    journal: Mapped[str | None] = mapped_column(Text, nullable=True)
    volume: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issue: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pages: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Book(Base):
    __tablename__ = "books"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    publisher: Mapped[str | None] = mapped_column(Text, nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True)


class BookPart(Base):
    __tablename__ = "book_parts"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    book_publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), nullable=False
    )
    chapter_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    pages: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    orcid: Mapped[str | None] = mapped_column(String(32), nullable=True)

    __table_args__ = (
        UniqueConstraint("full_name", "orcid", name="uq_person_name_orcid"),
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class ContributorRole(str, enum.Enum):
    author = "author"
    editor = "editor"
    translator = "translator"


class PublicationContributor(Base):
    __tablename__ = "publication_contributors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ContributorRole] = mapped_column(
        Enum(ContributorRole), nullable=False, default=ContributorRole.author
    )
    ord: Mapped[int | None] = mapped_column(Integer, nullable=True)

    publication: Mapped[Publication] = relationship(back_populates="contributors")

    __table_args__ = (
        UniqueConstraint(
            "publication_id", "person_id", "role", name="uq_pub_person_role"
        ),
    )


class IdentifierScheme(str, enum.Enum):
    doi = "doi"
    issn = "issn"
    isbn = "isbn"
    url = "url"
    other = "other"


class PublicationIdentifier(Base):
    __tablename__ = "publication_identifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), nullable=False
    )
    scheme: Mapped[IdentifierScheme] = mapped_column(
        Enum(IdentifierScheme), nullable=False
    )
    value: Mapped[str] = mapped_column(String(512), nullable=False)

    publication: Mapped[Publication] = relationship(back_populates="identifiers")

    __table_args__ = (
        UniqueConstraint("scheme", "value", name="uq_identifier_scheme_value"),
    )


class PersonAffiliation(Base):
    __tablename__ = "person_affiliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    from_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "person_id", "organization_id", "from_year", "to_year", name="uq_affil"
        ),
    )


Index("ix_runs_document_id", ExtractionRun.document_id)
Index("ix_runs_pipeline", ExtractionRun.pipeline)
