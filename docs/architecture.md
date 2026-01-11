# Architecture

## Components
- FastAPI API layer with API-key auth
- Graph executor (route -> retrieve -> guardrails -> reason)
- Graph-RAG:
  - seed nodes from query
  - k-hop neighborhood expansion
- Vector retrieval:
  - TF-IDF baseline for offline, API-free demo
  - upgrade path to Azure AI Search embeddings

## Observability & LLMOps
- Trace ID per request
- Latency metrics
- Test-case regression harness (pytest + YAML)

## Security & Governance
- Simple API-key auth
- Redaction hook + audit event
- Upgrade path to RBAC + policy checks
