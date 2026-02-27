# 🧠 Enterprise Graph-RAG Agent Platform

Enterprise-grade Generative AI system combining Graph-RAG, Hybrid Retrieval, Deterministic Reranking, Governance Guardrails, Evaluation (LLMOps), and Observability, with a full Streamlit demo UI and FastAPI service.

## Recruiter TL;DR
**What this demonstrates:** production-style GenAI backend engineering — routing, hybrid retrieval, deterministic testing, governance guardrails, and observability.

- **Backend:** FastAPI service + API-key auth
- **Product demo:** Streamlit UI
- **RAG:** Graph-RAG + vector Doc-RAG + Hybrid router
- **Quality:** deterministic reranking + pytest evaluation harness
- **Governance:** PII/secret redaction + optional blocking + audit events
- **Ops:** structured traces + metrics (latency/tokens/redactions)


This project demonstrates how to build production-ready GenAI systems, not just prototypes.

## 🚀 Key Capabilities
### ✅ Intelligent Retrieval
- Graph-RAG: dependency-aware retrieval using service graphs
- Doc-RAG: vector search over enterprise documentation
- Hybrid-RAG: combines graph context + documents
- Routing agent automatically selects the best mode
### ✅ Deterministic Reranking
- Offline, CI-safe reranker (no external models required)
- Token-overlap relevance (Jaccard)
- Document-type weighting (runbook > guide > policy)
- Optional MMR diversification
- Stable ordering (important for regression testing)
### ✅ Governance & Guardrails
- Redacts secrets and PII from:
  - user queries
  - retrieved snippets
  - generated context
- Detects:
  - API keys, tokens, passwords
  - Bearer tokens
  - Credit cards, SSN, UK NINO
- Supports blocking on high-risk patterns
- Emits structured audit events
### ✅ LLMOps / AgentOps
- Deterministic evaluation (no flaky tests)
- YAML-driven test cases
- Latency budgets
- Grounding checks
- Governance verification
- Trace-based observability
## ✅ Observability
- Structured trace events:
  - routing decisions
  - graph seeds
  - rerank before/after
  - guardrail hits
- Metrics:
  - token usage
  - latency
  - redactions
  - blocked flags
## ✅ Full Demo Experience
- Streamlit UI (local & API modes)
- FastAPI backend
- Toggle reranking, hops, context size, providers
- Visualise:
  - sanitized context
  - reranked documents
  - trace events
  - evaluation results
## 🏗️ Architecture Overview
```
User Query
   ↓
Router Agent
   ↓
Hybrid Retriever
   ├── Graph traversal (dependencies)
   ├── Vector search (documents)
   └── Deterministic Reranker
   ↓
Governance Guardrails
   ├── Query redaction
   ├── Context redaction
   └── Optional blocking
   ↓
Reasoning Agent (LLM)
   ↓
Answer + Sources
   ↓
Trace + Metrics + Evaluation
```

## 📂 Project Structure
```
enterprise-graph-rag-agent/
├── api/
│   ├── main.py              # FastAPI app
│   ├── auth.py              # API key auth
│   └── telemetry.py         # Trace & metrics
│
├── agents/
│   ├── graph_executor.py    # End-to-end orchestration
│   ├── router.py            # Query routing logic
│   ├── retrieval_agent.py   # Retrieval wrapper
│   ├── reasoning_agent.py   # LLM interaction
│   └── guardrails.py        # Governance & redaction
│
├── rag/
│   ├── hybrid_retriever.py  # Graph + Doc retrieval
│   ├── ranker.py            # Deterministic reranking
│   ├── corpus.py            # Demo corpus
│   └── vector_store.py      # TF-IDF vector store
│
├── graph/
│   ├── loader.py            # Demo dependency graph
│   └── traversal.py        # k-hop graph traversal
│
├── evaluation/
│   ├── test_cases.yaml      # Evaluation scenarios
│   ├── test_eval.py         # Pytest evaluation
│   ├── metrics.py           # LLMOps metrics
│   └── runner.py            # Evaluation runner
│
├── llm/
│   ├── clients.py           # Mock / Azure / OpenAI clients
│   └── prompts.py           # Prompt templates
│
├── streamlit_app.py         # Full demo UI
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```
# ⚙️ Setup & Installation
## 1️⃣ Clone & Install
```
git clone https://github.com/SamuelAina/enterprise-graph-rag-agent.git
cd enterprise-graph-rag-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

# 🔐 Environment Configuration

Create a .env file (or set env vars):
```
# LLM
LLM_PROVIDER=mock          # mock | azure_openai | openai_compatible

# Retrieval
TOP_K_DOCS=6
GRAPH_HOPS=2
MAX_CONTEXT_CHARS=8000
PER_DOC_SNIPPET_CHARS=280

# Reranking
RERANK_ENABLED=true
RERANK_ALPHA=0.65
RERANK_MMR_LAMBDA=1.0

# API
API_KEY=change-me
API_BASE_URL=http://127.0.0.1:8000
```

## ▶️ Running the System
### Option A — Streamlit Demo 

```bash
streamlit run streamlit_app.py
```
What you can demo:
- Graph-RAG vs Doc-RAG vs Hybrid
- Reranking effects
- Redaction in action
- Trace events & metrics
- Evaluation runner (LLMOps)

### Option B — FastAPI Service

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```
Health check:
```bash
curl http://127.0.0.1:8000/health
```
Ask endpoint:
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me" \
  -d '{"query":"OrderService is slow. What dependencies should I check first?"}'
```



# 🧪 Evaluation & Testing (LLMOps)
Run automated evaluation
```
pytest -q
```

What’s tested:
- Answer correctness (token checks)
- Grounding (sources present)
- Governance (redaction enforced)
- Latency budgets
- Deterministic behavior

## Custom test cases

Edit:
```
evaluation/test_cases.yaml
```

Example:
```
- id: case-004
  query: "api_key=sk_live_123 OrderService failing"
  expect_redaction: true
  min_overall: 0.5
```

# 🔎 Governance Example

Input
```
OrderService failing. api_key=sk_live_123 Authorization: Bearer abc.def.ghi
```

Sanitized Query
```
OrderService failing. api_key=[REDACTED] Authorization: Bearer [REDACTED]
```

Sanitized Context
```
[BLOCKED: sensitive content detected]
```

All actions are logged via structured trace events.

# 🧠 Why This Project Matters

This repo demonstrates real enterprise GenAI engineering, including:

- Deterministic evaluation (no flaky LLM tests)
- Explicit governance & auditability
- Separation of retrieval, reasoning, and policy
- Production-ready observability
- Config-driven experimentation
- CI-safe design

# 🧭 Future Extensions
- Cross-encoder / LLM reranking
- Vector DB swap (FAISS / Pinecone / Azure AI Search)
- Graph visualisation in Streamlit
- Policy-based access control (ABAC)
- Prompt versioning & A/B tests
- Token-level cost tracking

# 📜 License
MIT LICENSE

✉️ Contact
- samuel.aina@gmail.com
- If you’re reviewing this for hiring, architecture discussions, or collaboration, feel free to reach out.
