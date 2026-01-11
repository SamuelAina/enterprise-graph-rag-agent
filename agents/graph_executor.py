from typing import Dict, Any
from agents.router import route_query
from agents.retrieval_agent import retrieve_context
from agents.reasoning_agent import generate_answer
from agents.guardrails import apply_guardrails


class GraphExecutor:
    """
    A lightweight LangGraph-style executor:
    route -> retrieve -> guardrails -> reason -> return
    """

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def run(self, query: str, trace) -> Dict[str, Any]:
        route = route_query(query, trace=trace)

        ctx = retrieve_context(query, route=route, retriever=self.retriever, trace=trace)

        guarded = apply_guardrails(query=query, context=ctx, trace=trace)
        safe_query = guarded["query"]
        safe_ctx = guarded["context"]

        answer, sources = generate_answer(
            query=safe_query,
            context=safe_ctx,
            llm=self.llm,
            trace=trace,
        )

        return {
            "answer": answer,
            "route": route,
            "sources": sources,
            "context": safe_ctx,          # ✅ NEW: lets evaluation inspect redactions
            "query_sanitized": safe_query # ✅ NEW: useful for debugging/metrics
        }


