from __future__ import annotations

import hashlib

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ExtractedItem
from app.runs.repository import RunsRepository


def _norm(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _add_vertex(vertices_by_id: dict[str, dict], vertex: dict) -> None:
    vid = vertex["id"]
    if vid not in vertices_by_id:
        vertices_by_id[vid] = vertex


def _publication_vertex(*, proceso_id: int, item: ExtractedItem, title: str, year):
    pub_key = item.fingerprint or f"{title}|{year}"
    article_id = _stable_id("pub", pub_key)
    return article_id, {
        "id": article_id,
        "type": "publication",
        "label": title,
        "year": year,
        "source_item_id": item.id,
        "source_proceso_id": proceso_id,
    }


def _author_vertices_and_edges(
    *, proceso_id: int, item: ExtractedItem, article_id: str, authors: list, year
):
    vertices: list[dict] = []
    edges: list[dict] = []
    for idx, author in enumerate(authors):
        a = (author or "").strip()
        if not a:
            continue
        person_id = _stable_id("person", _norm(a))
        vertices.append({"id": person_id, "type": "person", "label": a})
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
    return vertices, edges


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

        article_id, pub_vertex = _publication_vertex(
            proceso_id=proceso_id,
            item=item,
            title=title,
            year=year,
        )
        _add_vertex(vertices_by_id, pub_vertex)

        author_vertices, author_edges = _author_vertices_and_edges(
            proceso_id=proceso_id,
            item=item,
            article_id=article_id,
            authors=authors,
            year=year,
        )
        for v in author_vertices:
            _add_vertex(vertices_by_id, v)
        edges.extend(author_edges)

    return list(vertices_by_id.values()), edges


class GraphService:
    def __init__(self, runs_repo: RunsRepository):
        self.runs_repo = runs_repo

    def graph_for_process(self, proceso_id: int):
        proceso = self.runs_repo.get_process(proceso_id)
        if proceso is None:
            return None

        items = self.runs_repo.list_items(proceso_id)
        vertices, edges = _iter_graph_elements(proceso_id, items)

        return {
            "proceso": {
                "id": proceso.id,
                "document_id": proceso.document_id,
                "pipeline": proceso.pipeline,
                "status": proceso.status,
            },
            "summary": {"vertex_count": len(vertices), "edge_count": len(edges)},
            "vertices": vertices,
            "edges": edges,
        }

    def graph_for_all_processes(self, limit: int = 50):
        procesos = self.runs_repo.list_processes(limit=limit)

        vertices_by_id: dict[str, dict] = {}
        edges: list[dict] = []

        # Nodo por proceso + grafo de sus items.
        for proceso in procesos:
            # proceso_vertex_id = f"process:{proceso.id}"
            # if proceso_vertex_id not in vertices_by_id:
            #     vertices_by_id[proceso_vertex_id] = {
            #         "id": proceso_vertex_id,
            #         "type": "process",
            #         "label": f"Proceso {proceso.id}",
            #         "pipeline": proceso.pipeline,
            #         "status": proceso.status,
            #         "document_id": proceso.document_id,
            #     }

            items = self.runs_repo.list_items(proceso.id)
            v, e = _iter_graph_elements(proceso.id, items)

            for vertex in v:
                vid = vertex["id"]
                if vid not in vertices_by_id:
                    vertices_by_id[vid] = vertex

                # Relación: proceso contiene publicación
                # if vertex.get("type") == "publication":
                #     edges.append(
                #         {
                #             "source": proceso_vertex_id,
                #             "target": vid,
                #             "type": "contains",
                #             "source_proceso_id": proceso.id,
                #         }
                #     )

            edges.extend(e)

        vertices = list(vertices_by_id.values())
        return {
            "summary": {"vertex_count": len(vertices), "edge_count": len(edges)},
            "vertices": vertices,
            "edges": edges,
        }


def get_graph_service(db: Session = Depends(get_db)) -> GraphService:
    return GraphService(RunsRepository(db))
