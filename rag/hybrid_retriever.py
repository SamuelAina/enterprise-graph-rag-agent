from __future__ import annotations

from typing import Dict, Any, List
import os

from rag.ranker import maybe_rerank
from graph.traversal import find_seed_nodes, k_hop_neighborhood


class HybridRetriever:
    def __init__(self, graph, vector_store):
        self.graph = graph
        self.vector_store = vector_store
        self.top_k_docs = int(os.getenv("TOP_K_DOCS", "6"))
        self.graph_hops = int(os.getenv("GRAPH_HOPS", "2"))
        self.max_context_chars = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))

        # Practical knobs
        self.enable_rerank = os.getenv("RERANK_ENABLED", "true").lower() in ("1", "true", "yes", "y")
        self.per_doc_snippet_chars = int(os.getenv("PER_DOC_SNIPPET_CHARS", "280"))
        self.include_scores_in_context = os.getenv("INCLUDE_SCORES_IN_CONTEXT", "true").lower() in ("1", "true", "yes", "y")

    def retrieve(self, query: str, mode: str, trace) -> Dict[str, Any]:
        graph_nodes: List[Dict[str, Any]] = []
        docs: List[Dict[str, Any]] = []

        if mode in ("graph_rag", "hybrid"):
            seeds = find_seed_nodes(self.graph, query)
            trace.event("graph_seeds", seeds=seeds)
            if seeds:
                graph_nodes = k_hop_neighborhood(self.graph, seeds, hops=self.graph_hops)

        # Doc retrieval
        if mode in ("doc_rag", "hybrid", "graph_rag"):
            docs = self.vector_store.search(query=query, top_k=self.top_k_docs)

            # Trace pre-rerank ordering (top doc ids)
            trace.event("doc_retrieval", doc_ids=[d.get("doc_id") for d in docs])

            if self.enable_rerank:
                before = [d.get("doc_id") for d in docs]
                docs = maybe_rerank(query, docs)
                after = [d.get("doc_id") for d in docs]

                trace.event(
                    "doc_rerank",
                    before=before,
                    after=after,
                    top_scores=[
                        {
                            "doc_id": d.get("doc_id"),
                            "score": d.get("score"),
                            "rerank_score": d.get("rerank_score"),
                            "final_score": d.get("final_score"),
                        }
                        for d in docs[: min(5, len(docs))]
                    ],
                )

        # Build compact context (include scores + truncate snippets)
        context_text = self._build_context_text(graph_nodes, docs)

        return {
            "graph_nodes": graph_nodes,
            "docs": docs,
            "context_text": context_text,
        }

    def _build_context_text(self, graph_nodes: List[Dict[str, Any]], docs: List[Dict[str, Any]]) -> str:
        parts: List[str] = []

        if graph_nodes:
            parts.append("## Dependency Graph Context")
            for n in graph_nodes:
                parts.append(
                    f"- {n['node_id']} (type={n.get('type')}, owner={n.get('owner')}, tier={n.get('tier')})"
                )

        if docs:
            parts.append("\n## Retrieved Documents")
            for d in docs:
                snippet = (d.get("snippet") or "")[: self.per_doc_snippet_chars]
                if self.include_scores_in_context:
                    fs = d.get("final_score", d.get("score", 0.0))
                    parts.append(f"- [{d['doc_id']}] {d['title']} (score={fs:.4f}): {snippet}")
                else:
                    parts.append(f"- [{d['doc_id']}] {d['title']}: {snippet}")

        txt = "\n".join(parts)
        return txt[: self.max_context_chars]
