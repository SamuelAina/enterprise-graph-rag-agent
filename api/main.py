from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from api.models import AskRequest, AskResponse
from api.auth import require_api_key
from api.telemetry import Trace

from agents.graph_executor import GraphExecutor
from graph.loader import load_demo_graph
from rag.corpus import load_demo_corpus
from rag.vector_store import TfidfVectorStore
from rag.hybrid_retriever import HybridRetriever
from llm.clients import build_llm_client

load_dotenv()

app = FastAPI(title="Enterprise Graph-RAG Agent Platform", version="1.0.0")

# --- Boot-time wiring (simple DI) ---
GRAPH = load_demo_graph()
CORPUS = load_demo_corpus()
VSTORE = TfidfVectorStore.from_corpus(CORPUS)
RETRIEVER = HybridRetriever(graph=GRAPH, vector_store=VSTORE)
LLM = build_llm_client()
EXECUTOR = GraphExecutor(retriever=RETRIEVER, llm=LLM)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, _=Depends(require_api_key)):
    trace = Trace()
    trace.event("request_received", user_id=req.user_id)

    result = EXECUTOR.run(query=req.query, trace=trace)

    

    trace.finish()
    return AskResponse(
        answer=result["answer"],
        trace_id=trace.trace_id,
        route=result["route"],
        sources=result["sources"],
        metrics=trace.metrics,
    )
