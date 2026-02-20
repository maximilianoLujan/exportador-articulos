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
    weight: float | None = None


class ProcessInfoModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    document_id: int
    pipeline: str | None = None
    status: str | None = None


class SummaryModel(BaseModel):
    vertex_count: int
    edge_count: int


class GraphResponseModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    proceso: ProcessInfoModel | None = None
    summary: SummaryModel
    vertices: list[VertexModel]
    edges: list[EdgeModel]

    # deja pasar claves futuras si aparecen
    extra: dict[str, Any] | None = None


class GraphPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vertices: list[VertexModel]
    edges: list[EdgeModel]


class GraphMetricsNodeModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str

    degree: float | None = None
    in_degree: float | None = None
    out_degree: float | None = None

    degree_centrality: float | None = None
    in_degree_centrality: float | None = None
    out_degree_centrality: float | None = None
    betweenness_centrality: float | None = None
    closeness_centrality: float | None = None
    eigenvector_centrality: float | None = None
    pagerank: float | None = None

    hits_hub: float | None = None
    hits_authority: float | None = None

    clustering_coefficient: float | None = None
    k_core: int | None = None


class GraphMetricsEdgeModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    type: str | None = None
    weight: float | None = None
    edge_betweenness_centrality: float | None = None


class GraphMetricsGraphModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    node_count: int
    edge_count: int
    directed: bool
    weighted: bool
    weight_attr: str

    density: float | None = None
    diameter_lcc_undirected: int | None = None
    average_path_length_lcc_undirected: float | None = None
    transitivity_global_clustering: float | None = None
    average_clustering_local_mean: float | None = None

    components: dict[str, Any] | None = None
    reciprocity: dict[str, Any] | None = None

    modularity_louvain: float | None = None
    communities_louvain: list[list[str]] | None = None


class GraphMetricsResponseModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    graph: GraphMetricsGraphModel
    nodes: list[GraphMetricsNodeModel]
    edges: list[GraphMetricsEdgeModel]
    reciprocity_by_node: dict[str, float | None] | None = None
    errors: dict[str, str] | None = None
