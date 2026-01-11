import re

GRAPH_HINTS = [
    r"\bdependency\b",
    r"\bdepends on\b",
    r"\broot cause\b",
    r"\bimpact\b",
    r"\bupstream\b",
    r"\bdownstream\b",
    r"\brelationship\b",
    r"\bconnected\b",
]

DOC_HINTS = [
    r"\bpolicy\b",
    r"\bprocedure\b",
    r"\bhow do i\b",
    r"\bsteps\b",
    r"\bguide\b",
    r"\bmanual\b",
]


def route_query(query: str, trace) -> str:
    q = query.lower()
    if any(re.search(p, q) for p in GRAPH_HINTS):
        trace.event("router_decision", route="graph_rag")
        return "graph_rag"
    if any(re.search(p, q) for p in DOC_HINTS):
        trace.event("router_decision", route="doc_rag")
        return "doc_rag"
    trace.event("router_decision", route="hybrid")
    return "hybrid"
