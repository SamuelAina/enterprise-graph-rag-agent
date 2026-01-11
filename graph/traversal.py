import networkx as nx
from typing import List, Dict, Any


def find_seed_nodes(graph: nx.DiGraph, query: str) -> List[str]:
    """
    Very simple seed matching by node name.
    You can upgrade this to entity extraction + alias mapping.
    """
    q = query.lower()
    seeds = []
    for n in graph.nodes:
        if n.lower() in q:
            seeds.append(n)
    return seeds


def k_hop_neighborhood(graph: nx.DiGraph, seeds: List[str], hops: int = 2) -> List[Dict[str, Any]]:
    visited = set(seeds)
    frontier = set(seeds)

    for _ in range(hops):
        next_frontier = set()
        for n in frontier:
            for nbr in graph.successors(n):
                if nbr not in visited:
                    visited.add(nbr)
                    next_frontier.add(nbr)
            for nbr in graph.predecessors(n):
                if nbr not in visited:
                    visited.add(nbr)
                    next_frontier.add(nbr)
        frontier = next_frontier

    nodes = []
    for n in visited:
        nodes.append({"node_id": n, **graph.nodes[n]})
    return nodes
