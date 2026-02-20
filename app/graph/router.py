from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.graph.metrics import MetricsConfig, compute_metrics
from app.graph.model import (
    EdgeModel,
    GraphMetricsResponseModel,
    GraphResponseModel,
    VertexModel,
)
from app.graph.service import GraphService, get_graph_service

router = APIRouter(prefix="/grafo", tags=["grafo"])


@router.get(
    "/procesos/{proceso_id}",
    response_model=GraphResponseModel,
    response_model_exclude_none=True,
)
def graph_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    result = service.graph_for_process(proceso_id)
    if result is None:
        raise HTTPException(status_code=404, detail="proceso no encontrado")
    return GraphResponseModel.model_validate(result)


@router.get(
    "/procesos",
    response_model=GraphResponseModel,
    response_model_exclude_none=True,
)
def graph_for_all_processes(
    limit: int = 50,
    service: GraphService = Depends(get_graph_service),
):
    # Devuelve un grafo que incluye nodos tipo "process" + publicaciones + autores.
    return GraphResponseModel.model_validate(
        service.graph_for_all_processes(limit=limit)
    )


@router.get(
    "/procesos/{proceso_id}/vertices",
    response_model=list[VertexModel],
    response_model_exclude_none=True,
)
def vertices_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    result = graph_for_process(proceso_id, service)
    return [VertexModel.model_validate(v) for v in result.vertices]


@router.get(
    "/procesos/{proceso_id}/edges",
    response_model=list[EdgeModel],
    response_model_exclude_none=True,
)
def edges_for_process(
    proceso_id: int,
    service: GraphService = Depends(get_graph_service),
):
    result = graph_for_process(proceso_id, service)
    return [EdgeModel.model_validate(e) for e in result.edges]


@router.get(
    "/procesos/{proceso_id}/metricas",
    response_model=GraphMetricsResponseModel,
    response_model_exclude_none=True,
)
def metrics_for_process(
    proceso_id: int,
    directed: bool = True,
    use_weights: bool = True,
    weight_is_distance: bool = False,
    aggregate_parallel_edges: bool = True,
    seed: int | None = 1,
    service: GraphService = Depends(get_graph_service),
):
    graph = graph_for_process(proceso_id, service)
    vertices = [v.model_dump(exclude_none=True) for v in graph.vertices]
    edges = [e.model_dump(exclude_none=True) for e in graph.edges]

    result = compute_metrics(
        vertices=vertices,
        edges=edges,
        config=MetricsConfig(
            directed=directed,
            use_weights=use_weights,
            weight_attr="weight",
            default_weight=1.0,
            weight_is_distance=weight_is_distance,
            aggregate_parallel_edges=aggregate_parallel_edges,
            seed=seed,
        ),
    )
    return GraphMetricsResponseModel.model_validate(result)


@router.get(
    "/metricas",
    response_model=GraphMetricsResponseModel,
    response_model_exclude_none=True,
)
def metrics_for_all_processes(
    limit: int = 50,
    directed: bool = True,
    use_weights: bool = True,
    weight_is_distance: bool = False,
    aggregate_parallel_edges: bool = True,
    seed: int | None = 1,
    service: GraphService = Depends(get_graph_service),
):
    graph = GraphResponseModel.model_validate(
        service.graph_for_all_processes(limit=limit)
    )
    vertices = [v.model_dump(exclude_none=True) for v in graph.vertices]
    edges = [e.model_dump(exclude_none=True) for e in graph.edges]

    result = compute_metrics(
        vertices=vertices,
        edges=edges,
        config=MetricsConfig(
            directed=directed,
            use_weights=use_weights,
            weight_attr="weight",
            default_weight=1.0,
            weight_is_distance=weight_is_distance,
            aggregate_parallel_edges=aggregate_parallel_edges,
            seed=seed,
        ),
    )
    return GraphMetricsResponseModel.model_validate(result)
