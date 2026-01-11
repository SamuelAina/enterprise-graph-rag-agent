from typing import Dict, Any


def retrieve_context(query: str, route: str, retriever, trace) -> Dict[str, Any]:
    trace.event("retrieval_start", route=route)
    result = retriever.retrieve(query=query, mode=route, trace=trace)
    trace.event(
        "retrieval_done",
        graph_nodes=len(result.get("graph_nodes", [])),
        docs=len(result.get("docs", [])),
    )
    return result
