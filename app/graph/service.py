from __future__ import annotations

import hashlib

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ExtractedItem
from app.importer.utils.name_matching import normalize as _normalize_name
from app.importer.utils.name_matching import same_person, split_name
from app.runs.repository import RunsRepository


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _person_key(name: str) -> str:
    last, first = split_name(name)
    if last and first:
        base = f"{last},{first}"
    else:
        base = last or (name or "")
    return _normalize_name(base).lower()


class _PersonResolver:
    def __init__(self):
        self._entries: list[dict[str, str]] = []
        self._by_last_initial: dict[str, list[dict[str, str]]] = {}

    def _bucket(self, name: str) -> str:
        last, _ = split_name(name)
        base = (last or _normalize_name(name)).strip()
        return (base[:1] or "?").lower()

    def resolve(self, raw_name: str) -> tuple[str, str]:
        raw = (raw_name or "").strip()
        if not raw:
            return "", ""

        bucket = self._bucket(raw)
        candidates = self._by_last_initial.get(bucket, [])

        for entry in candidates:
            if same_person(raw, entry["repr"]):
                return entry["id"], entry["label"]

        # No match found: create a new deterministic-ish id based on parsed key.
        pid = _stable_id("person", _person_key(raw))
        entry = {"id": pid, "repr": raw, "label": raw}
        self._entries.append(entry)
        self._by_last_initial.setdefault(bucket, []).append(entry)
        return pid, raw


def _add_vertex(vertices_by_id: dict[str, dict], vertex: dict) -> None:
    vid = vertex["id"]
    if vid not in vertices_by_id:
        vertices_by_id[vid] = vertex


def _category_vertex(*, category: str) -> dict:
    cid = _stable_id("category", (category or "").strip().lower())
    return {
        "id": cid,
        "type": "category",
        "label": category,
    }


def _category_edge(*, publication_id: str, category_id: str) -> dict:
    return {
        "source": publication_id,
        "target": category_id,
        "type": "has_category",
    }


def _publication_vertex(*, proceso_id: int, item: ExtractedItem, title: str, year):
    pub_key = item.fingerprint or f"{title}|{year}"
    publication_id = _stable_id("pub", pub_key)
    item_type = getattr(item.item_type, "value", item.item_type)
    category = None
    try:
        category = (item.data or {}).get("category")
    except Exception:
        category = None
    return publication_id, {
        "id": publication_id,
        "type": "publication",
        "publication_type": item_type,
        "label": title,
        "year": year,
        "category": category,
        "source_item_id": item.id,
        "source_proceso_id": proceso_id,
    }


def _author_vertices_and_edges(
    *,
    publication_id: str,
    authors: list,
    person_resolver: _PersonResolver,
):
    vertices: list[dict] = []
    edges: list[dict] = []
    for idx, author in enumerate(authors):
        a = (author or "").strip()
        if not a:
            continue

        person_id, label = person_resolver.resolve(a)
        if not person_id:
            continue

        vertices.append({"id": person_id, "type": "person", "label": label})
        edges.append(
            {
                "source": person_id,
                "target": publication_id,
                "type": "authored",
            }
        )
    return vertices, edges


def _iter_graph_elements(
    proceso_id: int,
    items: list[ExtractedItem],
    *,
    person_resolver: _PersonResolver | None = None,
):
    vertices_by_id: dict[str, dict] = {}
    edges: list[dict] = []

    if person_resolver is None:
        person_resolver = _PersonResolver()

    for item in items:
        if item.parse_error:
            continue

        data = item.data or {}
        title = (data.get("title") or "").strip()
        year = data.get("year")
        authors = data.get("authors") or []

        if not title or not authors:
            continue

        publication_id, pub_vertex = _publication_vertex(
            proceso_id=proceso_id,
            item=item,
            title=title,
            year=year,
        )
        _add_vertex(vertices_by_id, pub_vertex)

        category = pub_vertex.get("category")
        if category:
            cat_vertex = _category_vertex(category=category)
            _add_vertex(vertices_by_id, cat_vertex)
            edges.append(
                _category_edge(
                    publication_id=publication_id,
                    category_id=cat_vertex["id"],
                )
            )

        author_vertices, author_edges = _author_vertices_and_edges(
            publication_id=publication_id,
            authors=authors,
            person_resolver=person_resolver,
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

        person_resolver = _PersonResolver()

        # Nodo por proceso + grafo de sus items.
        for proceso in procesos:
            items = self.runs_repo.list_items(proceso.id)
            v, e = _iter_graph_elements(
                proceso.id, items, person_resolver=person_resolver
            )

            for vertex in v:
                vid = vertex["id"]
                if vid not in vertices_by_id:
                    vertices_by_id[vid] = vertex

            edges.extend(e)

        vertices = list(vertices_by_id.values())
        return {
            "summary": {"vertex_count": len(vertices), "edge_count": len(edges)},
            "vertices": vertices,
            "edges": edges,
        }


def get_graph_service(db: Session = Depends(get_db)) -> GraphService:
    return GraphService(RunsRepository(db))
