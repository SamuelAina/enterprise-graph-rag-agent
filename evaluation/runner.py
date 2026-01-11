import yaml
from typing import List, Dict, Any

from api.telemetry import Trace
from agents.graph_executor import GraphExecutor
from graph.loader import load_demo_graph
from rag.corpus import load_demo_corpus
from rag.vector_store import TfidfVectorStore
from rag.hybrid_retriever import HybridRetriever
from llm.clients import build_llm_client

from evaluation.metrics import evaluate_case

def load_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_executor() -> GraphExecutor:
    graph = load_demo_graph()
    corpus = load_demo_corpus()
    vstore = TfidfVectorStore.from_corpus(corpus)
    retriever = HybridRetriever(graph=graph, vector_store=vstore)
    llm = build_llm_client()
    return GraphExecutor(retriever=retriever, llm=llm)


def run_cases(cases_path: str):
    ex = build_executor()
    cases = load_cases(cases_path)
    results = []

    for c in cases:
        trace = Trace()
        out = ex.run(query=c["query"], trace=trace)
        trace.finish()

        report = evaluate_case(
            answer=out["answer"],
            sources=out.get("sources", []),
            context=out.get("context", {}),
            metrics=trace.metrics,
            must_include=c.get("must_include", []),
            forbidden=c.get("forbidden", []),
        )

        results.append({
            "id": c["id"],
            "answer": out["answer"],
            "route": out["route"],
            "sources": out.get("sources", []),
            "context": out.get("context", {}),
            "query_sanitized": out.get("query_sanitized"),
            "metrics": trace.metrics,
            "eval": report,  # ✅ NEW
        })

    return results
