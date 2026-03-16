from __future__ import annotations

import hashlib
import re
from collections import Counter

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


def _parse_year(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        try:
            return int(value)
        except Exception:
            return None

    text = str(value).strip()
    if not text:
        return None

    # accept common forms like "2019", "(2019)", "2019." etc.
    m = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _norm_category(value: str | None) -> str:
    return (value or "").strip().lower()


def _item_matches_filters(
    *,
    item: ExtractedItem,
    anio: list[int] | None,
    persona: list[str] | None,
    categoria: str | None,
) -> bool:
    data = item.data or {}

    if anio:
        item_year = _parse_year(data.get("year"))
        if item_year not in set(anio):
            return False

    if categoria:
        item_category = _norm_category(data.get("category"))
        if item_category != _norm_category(categoria):
            return False

    if persona:
        authors = data.get("authors") or []
        personas = [p for p in persona if (p or "").strip()]
        if not personas:
            return True

        # include item if any provided person matches any author
        if not any(
            same_person(p, a) for p in personas for a in authors if (a or "").strip()
        ):
            return False

    return True


def _extract_publication_fields(item: ExtractedItem) -> tuple[str, int | None, list]:
    data = item.data or {}
    title = (data.get("title") or "").strip()
    year = data.get("year")
    authors = data.get("authors") or []
    return title, _parse_year(year), authors


def _graph_elements_for_item(
    *,
    proceso_id: int,
    item: ExtractedItem,
    person_resolver: _PersonResolver,
    only_personas: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    data = item.data or {}
    title = (data.get("title") or "").strip()
    year_raw = data.get("year")
    authors = data.get("authors") or []

    publication_id, pub_vertex = _publication_vertex(
        proceso_id=proceso_id,
        item=item,
        title=title,
        year=year_raw,
    )

    vertices: list[dict] = [pub_vertex]
    edges: list[dict] = []

    category = pub_vertex.get("category")
    if category:
        cat_vertex = _category_vertex(category=category)
        vertices.append(cat_vertex)
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
        only_personas=only_personas,
    )
    vertices.extend(author_vertices)
    edges.extend(author_edges)

    return vertices, edges


def _should_include_item(
    *,
    item: ExtractedItem,
    anio: list[int] | None,
    persona: list[str] | None,
    categoria: str | None,
) -> bool:
    if item.parse_error:
        return False

    if not _item_matches_filters(
        item=item,
        anio=anio,
        persona=persona,
        categoria=categoria,
    ):
        return False

    title, _, authors = _extract_publication_fields(item)
    if not title or not authors:
        return False

    return True


def _author_vertices_and_edges(
    *,
    publication_id: str,
    authors: list,
    person_resolver: _PersonResolver,
    only_personas: list[str] | None = None,
):
    vertices: list[dict] = []
    edges: list[dict] = []
    personas = [p for p in (only_personas or []) if (p or "").strip()]
    for idx, author in enumerate(authors):
        a = (author or "").strip()
        if not a:
            continue

        if personas and not any(same_person(p, a) for p in personas):
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
    anio: list[int] | None = None,
    persona: list[str] | None = None,
    categoria: str | None = None,
    solo_persona: bool = False,
):
    vertices_by_id: dict[str, dict] = {}
    edges: list[dict] = []

    if person_resolver is None:
        person_resolver = _PersonResolver()

    for item in items:
        if not _should_include_item(
            item=item,
            anio=anio,
            persona=persona,
            categoria=categoria,
        ):
            continue

        only_personas = persona if (solo_persona and persona) else None

        item_vertices, item_edges = _graph_elements_for_item(
            proceso_id=proceso_id,
            item=item,
            person_resolver=person_resolver,
            only_personas=only_personas,
        )
        for v in item_vertices:
            _add_vertex(vertices_by_id, v)
        edges.extend(item_edges)

    return list(vertices_by_id.values()), edges


class GraphService:
    def __init__(self, runs_repo: RunsRepository):
        self.runs_repo = runs_repo

    def _summary_with_counts(
        self,
        *,
        vertices: list[dict],
        edges: list[dict],
        process_count: int | None = None,
    ) -> dict:
        # Conteos robustos: siempre por id (distinct)
        publication_type_by_id: dict[str, str] = {}
        article_category_by_id: dict[str, str] = {}
        person_ids: set[str] = set()
        category_ids: set[str] = set()

        for v in vertices:
            vtype = v.get("type")
            vid = v.get("id")
            if not isinstance(vid, str) or not vid:
                continue

            if vtype == "publication":
                ptype = v.get("publication_type") or "unknown"
                publication_type_by_id[vid] = str(ptype)
                if str(ptype) == "article":
                    article_category_by_id[vid] = str(
                        v.get("category") or "sin_categoria"
                    )
            elif vtype == "person":
                person_ids.add(vid)
            elif vtype == "category":
                category_ids.add(vid)

        publications_by_type: Counter[str] = Counter(publication_type_by_id.values())
        articles_by_category: Counter[str] = Counter(article_category_by_id.values())

        publication_count = len(publication_type_by_id)
        authors_count = len(person_ids)
        category_count = len(category_ids)

        # Atajos esperados por UI/consumidores
        books_count = publications_by_type.get("book", 0)
        articles_count = publications_by_type.get("article", 0)
        book_parts_count = publications_by_type.get("book_parts", 0)

        return {
            "vertex_count": len(vertices),
            "edge_count": len(edges),
            "publication_count": publication_count,
            "authors_count": authors_count,
            "category_count": category_count,
            "process_count": process_count,
            "books_count": books_count,
            "articles_count": articles_count,
            "book_parts_count": book_parts_count,
            "articles_by_category": dict(articles_by_category),
        }

    def list_persons(self) -> list[dict]:
        items = self.runs_repo.list_all_items()

        person_resolver = _PersonResolver()
        vertices_by_id: dict[str, dict] = {}

        for item in items:
            if item.parse_error:
                continue

            data = item.data or {}
            authors = data.get("authors") or []
            for author in authors:
                raw = (author or "").strip()
                if not raw:
                    continue
                pid, label = person_resolver.resolve(raw)
                if not pid:
                    continue
                _add_vertex(
                    vertices_by_id, {"id": pid, "type": "person", "label": label}
                )

        # stable order for frontend
        persons = list(vertices_by_id.values())
        persons.sort(key=lambda v: (v.get("label") or "").lower())
        return persons

    def graph_for_process(
        self,
        proceso_id: int,
        *,
        anio: list[int] | None = None,
        persona: list[str] | None = None,
        categoria: str | None = None,
        solo_persona: bool = False,
    ):
        proceso = self.runs_repo.get_process(proceso_id)
        if proceso is None:
            return None

        items = self.runs_repo.list_items(proceso_id)
        vertices, edges = _iter_graph_elements(
            proceso_id,
            items,
            anio=anio,
            persona=persona,
            categoria=categoria,
            solo_persona=solo_persona,
        )

        return {
            "proceso": {
                "id": proceso.id,
                "document_id": proceso.document_id,
                "pipeline": proceso.pipeline,
                "status": proceso.status,
            },
            "summary": self._summary_with_counts(
                vertices=vertices,
                edges=edges,
                process_count=1,
            ),
            "vertices": vertices,
            "edges": edges,
        }

    def graph_for_all_processes(
        self,
        *,
        limit: int = 50,
        anio: list[int] | None = None,
        persona: list[str] | None = None,
        categoria: str | None = None,
        solo_persona: bool = False,
    ):
        procesos = self.runs_repo.list_processes(limit=limit)

        vertices_by_id: dict[str, dict] = {}
        edges: list[dict] = []

        person_resolver = _PersonResolver()

        # Nodo por proceso + grafo de sus items.
        for proceso in procesos:
            items = self.runs_repo.list_items(proceso.id)
            v, e = _iter_graph_elements(
                proceso.id,
                items,
                person_resolver=person_resolver,
                anio=anio,
                persona=persona,
                categoria=categoria,
                solo_persona=solo_persona,
            )

            for vertex in v:
                vid = vertex["id"]
                if vid not in vertices_by_id:
                    vertices_by_id[vid] = vertex

            edges.extend(e)

        vertices = list(vertices_by_id.values())
        return {
            "summary": self._summary_with_counts(
                vertices=vertices,
                edges=edges,
                process_count=len(procesos),
            ),
            "vertices": vertices,
            "edges": edges,
        }


def get_graph_service(db: Session = Depends(get_db)) -> GraphService:
    return GraphService(RunsRepository(db))
