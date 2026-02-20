from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

import networkx as nx


@dataclass(frozen=True)
class MetricsConfig:
    directed: bool = True
    use_weights: bool = True
    weight_attr: str = "weight"
    default_weight: float = 1.0
    weight_is_distance: bool = False
    aggregate_parallel_edges: bool = True
    seed: int | None = 1


def _as_weight(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        w = float(value)
    except Exception:
        return default
    if math.isnan(w):
        return default
    return w


def build_graph(
    *,
    vertices: Iterable[dict[str, Any]],
    edges: Iterable[dict[str, Any]],
    config: MetricsConfig,
) -> nx.Graph:
    graph: nx.Graph
    if config.directed:
        graph = nx.DiGraph()
    else:
        graph = nx.Graph()

    for v in vertices:
        node_id = v.get("id")
        if node_id is None:
            continue
        graph.add_node(node_id, **{k: v[k] for k in v.keys() if k != "id"})

    for e in edges:
        source = e.get("source")
        target = e.get("target")
        if not source or not target:
            continue

        weight = (
            _as_weight(e.get(config.weight_attr), config.default_weight)
            if config.use_weights
            else config.default_weight
        )
        edge_type = e.get("type")

        if config.aggregate_parallel_edges and graph.has_edge(source, target):
            data = graph.get_edge_data(source, target) or {}
            data[config.weight_attr] = (
                _as_weight(data.get(config.weight_attr), config.default_weight) + weight
            )
            existing_type = data.get("type")
            if existing_type is None:
                data["type"] = edge_type
            elif edge_type is not None and existing_type != edge_type:
                data["type"] = "mixed"
            graph.add_edge(source, target, **data)
        else:
            attrs: dict[str, Any] = {config.weight_attr: weight}
            if edge_type is not None:
                attrs["type"] = edge_type
            graph.add_edge(source, target, **attrs)

    return graph


def _largest_component_nodes(ug: nx.Graph) -> set[Any]:
    if ug.number_of_nodes() == 0:
        return set()

    try:
        components = list(nx.connected_components(ug))
    except nx.NetworkXNotImplemented:
        # Should never happen for undirected graphs, but keep it defensive.
        components = [set(ug.nodes())]

    if not components:
        return set()
    return set(max(components, key=len))


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def compute_metrics(
    *,
    vertices: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    config: MetricsConfig,
) -> dict[str, Any]:
    g = build_graph(vertices=vertices, edges=edges, config=config)

    weight_kw = config.weight_attr if config.use_weights else None
    distance_kw = (
        config.weight_attr
        if (config.use_weights and config.weight_is_distance)
        else None
    )

    # Project to undirected for metrics that are typically defined/used that way in
    # "NodeXL-style" graphs (clustering, k-core, Louvain, and component path stats).
    ug = g.to_undirected(as_view=False)

    # Components
    if config.directed:
        weak_components = [set(c) for c in nx.weakly_connected_components(g)]
        strong_components = [set(c) for c in nx.strongly_connected_components(g)]
    else:
        weak_components = [set(c) for c in nx.connected_components(ug)]
        strong_components = None

    lcc_nodes = _largest_component_nodes(ug)
    lcc = ug.subgraph(lcc_nodes).copy() if lcc_nodes else ug.copy()

    # Node-level centralities
    node_metrics: dict[Any, dict[str, Any]] = {n: {} for n in g.nodes()}

    # degrees
    if config.directed:
        for n in g.nodes():
            node_metrics[n]["in_degree"] = float(g.in_degree(n, weight=weight_kw))
            node_metrics[n]["out_degree"] = float(g.out_degree(n, weight=weight_kw))
            node_metrics[n]["degree"] = float(g.degree(n, weight=weight_kw))
        in_deg_cent = nx.in_degree_centrality(g) if g.number_of_nodes() else {}
        out_deg_cent = nx.out_degree_centrality(g) if g.number_of_nodes() else {}
        deg_cent = nx.degree_centrality(g) if g.number_of_nodes() else {}
        for n in g.nodes():
            node_metrics[n]["in_degree_centrality"] = in_deg_cent.get(n)
            node_metrics[n]["out_degree_centrality"] = out_deg_cent.get(n)
            node_metrics[n]["degree_centrality"] = deg_cent.get(n)
    else:
        for n in g.nodes():
            node_metrics[n]["degree"] = float(g.degree(n, weight=weight_kw))
        deg_cent = nx.degree_centrality(g) if g.number_of_nodes() else {}
        for n in g.nodes():
            node_metrics[n]["degree_centrality"] = deg_cent.get(n)

    # betweenness
    # In NetworkX, `weight` is interpreted as a distance/cost. Only apply it when
    # the caller explicitly indicates weights represent distances.
    betweenness, betweenness_err = _safe_call(
        nx.betweenness_centrality,
        g,
        weight=distance_kw,
        normalized=True,
    )
    if betweenness is None:
        betweenness = {}
    for n in g.nodes():
        node_metrics[n]["betweenness_centrality"] = betweenness.get(n)

    # closeness
    closeness, closeness_err = _safe_call(
        nx.closeness_centrality,
        g,
        distance=distance_kw,
    )
    if closeness is None:
        closeness = {}
    for n in g.nodes():
        node_metrics[n]["closeness_centrality"] = closeness.get(n)

    # eigenvector
    eigenvector, eigenvector_err1 = _safe_call(
        nx.eigenvector_centrality,
        g,
        max_iter=2000,
        tol=1e-08,
        weight=weight_kw,
    )
    eigenvector_err = eigenvector_err1
    if eigenvector is None:
        # Fallback to undirected projection (common workaround for non-strongly-connected digraphs).
        eigenvector, eigenvector_err2 = _safe_call(
            nx.eigenvector_centrality,
            ug,
            max_iter=2000,
            tol=1e-08,
            weight=weight_kw,
        )
        if eigenvector is None:
            eigenvector = {}
            eigenvector_err = eigenvector_err1 or eigenvector_err2
        else:
            # Fallback succeeded; don't surface the directed-graph failure.
            eigenvector_err = None
    for n in g.nodes():
        node_metrics[n]["eigenvector_centrality"] = eigenvector.get(n, 0.0)

    # PageRank
    pagerank, pagerank_err = _safe_call(
        nx.pagerank,
        g,
        weight=weight_kw,
    )
    if pagerank is None:
        pagerank = {}
    for n in g.nodes():
        node_metrics[n]["pagerank"] = pagerank.get(n)

    # HITS
    hubs, hubs_err = _safe_call(nx.hits, g, max_iter=2000, tol=1e-08, normalized=True)
    authorities = None
    hits_err = None
    if hubs is None:
        hubs = {}
        authorities = {}
        hits_err = hubs_err
    else:
        authorities = hubs[1]
        hubs = hubs[0]

    for n in g.nodes():
        node_metrics[n]["hits_hub"] = hubs.get(n)
        node_metrics[n]["hits_authority"] = authorities.get(n)

    # Clustering
    clustering, clustering_err = _safe_call(nx.clustering, ug, weight=weight_kw)
    if clustering is None:
        clustering = {}
    for n in g.nodes():
        node_metrics[n]["clustering_coefficient"] = clustering.get(n)

    # k-core decomposition (core number)
    core_numbers, core_err = _safe_call(nx.core_number, ug)
    if core_numbers is None:
        core_numbers = {}
    for n in g.nodes():
        node_metrics[n]["k_core"] = core_numbers.get(n)

    # Reciprocity
    reciprocity_overall = None
    reciprocity_by_node: dict[Any, Any] | None = None
    reciprocity_err = None
    if config.directed:
        reciprocity_overall, reciprocity_err = _safe_call(nx.reciprocity, g)
        reciprocity_by_node = {}
        for n in g.nodes():
            val, _ = _safe_call(nx.reciprocity, g, n)
            reciprocity_by_node[n] = val

    # Edge betweenness
    edge_between, edge_between_err = _safe_call(
        nx.edge_betweenness_centrality,
        g,
        weight=distance_kw,
        normalized=True,
    )
    if edge_between is None:
        edge_between = {}

    edge_metrics: list[dict[str, Any]] = []
    for u, v, data in g.edges(data=True):
        edge_metrics.append(
            {
                "source": u,
                "target": v,
                "type": data.get("type"),
                config.weight_attr: data.get(config.weight_attr),
                "edge_betweenness_centrality": edge_between.get((u, v)),
            }
        )

    # Graph-level clustering coefficients
    transitivity, transitivity_err = _safe_call(nx.transitivity, ug)
    avg_clustering, avg_clustering_err = _safe_call(
        nx.average_clustering, ug, weight=weight_kw
    )

    # Density
    density = nx.density(g)

    # Path-length based metrics on the largest connected component of the undirected projection.
    # For disconnected graphs, these are computed on the LCC.
    diameter = None
    avg_path_length = None
    diameter_err = None
    apl_err = None
    if lcc.number_of_nodes() == 0:
        diameter = None
        avg_path_length = None
    elif lcc.number_of_nodes() == 1:
        diameter = 0
        avg_path_length = 0.0
    else:
        diameter, diameter_err = _safe_call(nx.diameter, lcc)
        avg_path_length, apl_err = _safe_call(
            nx.average_shortest_path_length,
            lcc,
            weight=distance_kw,
        )

    # Modularity (Louvain)
    communities = None
    modularity = None
    louvain_err = None
    if ug.number_of_nodes() > 0 and ug.number_of_edges() > 0:
        communities, louvain_err = _safe_call(
            nx.algorithms.community.louvain_communities,
            ug,
            weight=weight_kw,
            seed=config.seed,
        )
        if communities is not None:
            modularity, _ = _safe_call(
                nx.algorithms.community.modularity,
                ug,
                communities,
                weight=weight_kw,
            )
            communities = [sorted(c) for c in communities]

    # Assemble response
    errors: dict[str, str] = {}
    for key, err in [
        ("betweenness_centrality", betweenness_err),
        ("closeness_centrality", closeness_err),
        ("eigenvector_centrality", eigenvector_err),
        ("pagerank", pagerank_err),
        ("hits", hits_err),
        ("clustering", clustering_err),
        ("k_core", core_err),
        ("reciprocity", reciprocity_err),
        ("edge_betweenness_centrality", edge_between_err),
        ("transitivity", transitivity_err),
        ("average_clustering", avg_clustering_err),
        ("diameter", diameter_err),
        ("average_path_length", apl_err),
        ("louvain", louvain_err),
    ]:
        if err:
            errors[key] = err

    graph_metrics: dict[str, Any] = {
        "node_count": g.number_of_nodes(),
        "edge_count": g.number_of_edges(),
        "directed": config.directed,
        "weighted": bool(config.use_weights),
        "weight_attr": config.weight_attr,
        "density": density,
        "diameter_lcc_undirected": diameter,
        "average_path_length_lcc_undirected": avg_path_length,
        "transitivity_global_clustering": transitivity,
        "average_clustering_local_mean": avg_clustering,
        "components": {
            "weak": {
                "count": len(weak_components),
                "sizes": sorted([len(c) for c in weak_components], reverse=True),
            },
            "strong": (
                {
                    "count": len(strong_components or []),
                    "sizes": sorted(
                        [len(c) for c in (strong_components or [])], reverse=True
                    ),
                }
                if strong_components is not None
                else None
            ),
            "largest": {
                "size": int(lcc.number_of_nodes()),
                "nodes": sorted(lcc_nodes) if lcc_nodes else [],
            },
        },
        "reciprocity": {
            "overall": reciprocity_overall,
        }
        if config.directed
        else None,
        "modularity_louvain": modularity,
        "communities_louvain": communities,
    }

    nodes_out: list[dict[str, Any]] = []
    for n in g.nodes():
        nodes_out.append({"id": n, **node_metrics.get(n, {})})

    return {
        "graph": graph_metrics,
        "nodes": nodes_out,
        "edges": edge_metrics,
        "reciprocity_by_node": reciprocity_by_node,
        "errors": errors or None,
    }
