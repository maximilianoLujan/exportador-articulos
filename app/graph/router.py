from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ExtractedItem, ExtractionRun

router = APIRouter(prefix="/grafo", tags=["grafo"])


def _norm(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _add_vertex(vertices_by_id: dict[str, dict], vertex: dict) -> None:
    vid = vertex["id"]
    if vid not in vertices_by_id:
        vertices_by_id[vid] = vertex


def _iter_graph_elements(proceso_id: int, items: list[ExtractedItem]):
    vertices_by_id: dict[str, dict] = {}
    edges: list[dict] = []

    for item in items:
        if item.parse_error:
            continue

        data = item.data or {}
        title = (data.get("title") or "").strip()
        year = data.get("year")
        authors = data.get("authors") or []

        if not title or not authors:
            continue

        article_key = f"{item.id}|{title}|{year}"
        article_id = _stable_id("pub", article_key)
        _add_vertex(
            vertices_by_id,
            {
                "id": article_id,
                "type": "publication",
                "label": title,
                "year": year,
                "source_item_id": item.id,
                "source_proceso_id": proceso_id,
            },
        )

        for idx, author in enumerate(authors):
            a = (author or "").strip()
            if not a:
                continue

            person_id = _stable_id("person", _norm(a))
            _add_vertex(vertices_by_id, {"id": person_id, "type": "person", "label": a})

            edges.append(
                {
                    "source": person_id,
                    "target": article_id,
                    "type": "authored",
                    "ord": idx + 1,
                    "year": year,
                    "source_item_id": item.id,
                    "source_proceso_id": proceso_id,
                }
            )

    return list(vertices_by_id.values()), edges


@router.get("/procesos/{proceso_id}")
def graph_for_process(proceso_id: int, db: Session = Depends(get_db)):
    proceso = db.get(ExtractionRun, proceso_id)
    if proceso is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")

    items = (
        db.execute(
            select(ExtractedItem)
            .where(ExtractedItem.run_id == proceso_id)
            .order_by(ExtractedItem.id.asc())
        )
        .scalars()
        .all()
    )

    vertices, edges = _iter_graph_elements(proceso_id, items)

    return {
        "proceso": {
            "id": proceso.id,
            "document_id": proceso.document_id,
            "pipeline": proceso.pipeline,
            "status": proceso.status,
        },
        "summary": {
            "vertex_count": len(vertices),
            "edge_count": len(edges),
        },
        "vertices": vertices,
        "edges": edges,
    }


@router.get("/procesos/{proceso_id}/vertices")
def vertices_for_process(proceso_id: int, db: Session = Depends(get_db)):
    return graph_for_process(proceso_id, db)["vertices"]


@router.get("/procesos/{proceso_id}/edges")
def edges_for_process(proceso_id: int, db: Session = Depends(get_db)):
    return graph_for_process(proceso_id, db)["edges"]
