from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.graph.model import EdgeModel, GraphResponseModel, VertexModel
from app.graph.service import GraphService, get_graph_service

router = APIRouter(prefix="/grafo", tags=["grafo"])


_DESC_ANIO = "Filtrar publicaciones por año"
_DESC_PERSONA = "Filtrar publicaciones por autor/persona (fuzzy). Repetible."
_DESC_CATEGORIA = "Filtrar publicaciones por categoría"
_DESC_SOLO_PERSONA = "Si true, no incluye coautores (solo personas filtradas)"
_NOT_FOUND_DETAIL = "proceso no encontrado"


@router.get(
    "/personas",
    response_model=list[VertexModel],
    response_model_exclude_none=True,
)
def list_personas(service: GraphService = Depends(get_graph_service)):
    return [VertexModel.model_validate(v) for v in service.list_persons()]


@router.get(
    "/procesos/{proceso_id}",
    response_model=GraphResponseModel,
    response_model_exclude_none=True,
)
def graph_for_process(
    proceso_id: int,
    anio: list[int] | None = Query(None, description=_DESC_ANIO),
    persona: list[str] | None = Query(None, description=_DESC_PERSONA),
    categoria: str | None = Query(None, description=_DESC_CATEGORIA),
    solo_persona: bool = Query(False, description=_DESC_SOLO_PERSONA),
    service: GraphService = Depends(get_graph_service),
):
    result = service.graph_for_process(
        proceso_id,
        anio=anio,
        persona=persona,
        categoria=categoria,
        solo_persona=solo_persona,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    return GraphResponseModel.model_validate(result)


@router.get(
    "/procesos",
    response_model=GraphResponseModel,
    response_model_exclude_none=True,
)
def graph_for_all_processes(
    limit: int = 50,
    anio: list[int] | None = Query(None, description=_DESC_ANIO),
    persona: list[str] | None = Query(None, description=_DESC_PERSONA),
    categoria: str | None = Query(None, description=_DESC_CATEGORIA),
    solo_persona: bool = Query(False, description=_DESC_SOLO_PERSONA),
    service: GraphService = Depends(get_graph_service),
):
    # Devuelve un grafo que incluye nodos tipo "process" + publicaciones + autores.
    return GraphResponseModel.model_validate(
        service.graph_for_all_processes(
            limit=limit,
            anio=anio,
            persona=persona,
            categoria=categoria,
            solo_persona=solo_persona,
        )
    )


@router.get(
    "/procesos/{proceso_id}/vertices",
    response_model=list[VertexModel],
    response_model_exclude_none=True,
)
def vertices_for_process(
    proceso_id: int,
    anio: list[int] | None = Query(None, description=_DESC_ANIO),
    persona: list[str] | None = Query(None, description=_DESC_PERSONA),
    categoria: str | None = Query(None, description=_DESC_CATEGORIA),
    solo_persona: bool = Query(False, description=_DESC_SOLO_PERSONA),
    service: GraphService = Depends(get_graph_service),
):
    result = service.graph_for_process(
        proceso_id,
        anio=anio,
        persona=persona,
        categoria=categoria,
        solo_persona=solo_persona,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    graph = GraphResponseModel.model_validate(result)
    return [VertexModel.model_validate(v) for v in graph.vertices]


@router.get(
    "/procesos/{proceso_id}/edges",
    response_model=list[EdgeModel],
    response_model_exclude_none=True,
)
def edges_for_process(
    proceso_id: int,
    anio: list[int] | None = Query(None, description=_DESC_ANIO),
    persona: list[str] | None = Query(None, description=_DESC_PERSONA),
    categoria: str | None = Query(None, description=_DESC_CATEGORIA),
    solo_persona: bool = Query(False, description=_DESC_SOLO_PERSONA),
    service: GraphService = Depends(get_graph_service),
):
    result = service.graph_for_process(
        proceso_id,
        anio=anio,
        persona=persona,
        categoria=categoria,
        solo_persona=solo_persona,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    graph = GraphResponseModel.model_validate(result)
    return [EdgeModel.model_validate(e) for e in graph.edges]
