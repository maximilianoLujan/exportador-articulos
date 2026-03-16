from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class VertexModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: str
    label: str | None = None

    # comunes (opcionales)
    year: int | None = None
    category: str | None = None

    source_item_id: int | None = None
    source_proceso_id: int | None = None


class EdgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    type: str


class ProcessInfoModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    document_id: int
    pipeline: str | None = None
    status: str | None = None


class SummaryModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    vertex_count: int
    edge_count: int

    # Totales derivados del grafo
    publication_count: int | None = None
    authors_count: int | None = None
    category_count: int | None = None
    process_count: int | None = None

    # Atajos (compatibilidad / consumo simple)
    books_count: int | None = None
    articles_count: int | None = None
    book_parts_count: int | None = None

    # Subtipo de artículos (hoy: por categoría detectada en extracción)
    articles_by_category: dict[str, int] | None = None


class GraphResponseModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    proceso: ProcessInfoModel | None = None
    summary: SummaryModel
    vertices: list[VertexModel]
    edges: list[EdgeModel]

    # deja pasar claves futuras si aparecen
    extra: dict[str, Any] | None = None
