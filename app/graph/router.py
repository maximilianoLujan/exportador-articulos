from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.graph.service import GraphService, get_graph_service

router = APIRouter(prefix="/grafo", tags=["grafo"])


@router.get("/procesos/{proceso_id}")
def graph_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    result = service.graph_for_process(proceso_id)
    if result is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    return result


@router.get("/procesos")
def graph_for_all_processes(
    limit: int = 50,
    service: GraphService = Depends(get_graph_service),
):
    # Devuelve un grafo que incluye nodos tipo "process" + publicaciones + autores.
    return service.graph_for_all_processes(limit=limit)


@router.get("/procesos/{proceso_id}/vertices")
def vertices_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    return graph_for_process(proceso_id, service)["vertices"]


@router.get("/procesos/{proceso_id}/edges")
def edges_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    return graph_for_process(proceso_id, service)["edges"]
