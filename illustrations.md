## Starup
command:
```
uvicorn api.main:app --host 127.0.0.1 --port 8000 --log-level debug
```

response:
```
INFO:     Started server process [10140]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 1️⃣ Health & Readiness (Ops sanity)
This is a simple readiness probe — in production it would be wired into a load balancer or Kubernetes health check.

## Health check
```
curl http://127.0.0.1:8000/health
```


response:
```
{"ok":true}
```


## 2️⃣ Agent Routing (Graph vs Doc vs Hybrid)

### Graph-driven question (dependency language)
The router agent detects relationship language and switches to Graph-RAG.
```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -H "X-API-Key: change-me" -d "{\"query\":\"What services are upstream and downstream of InventoryService?\"}"
```

Respomse:

```json
{
    "answer": "### Upstream and Downstream Services of InventoryService\n\n**Upstream Services:**\n- **None identified** in the provided context.\n\n**Downstream Services:**\n- **OrderService**: Depends on InventoryService for inventory-related operations.\n- **PricingService**: Also mentioned as a dependency in the context of OrderService.\n\n### Troubleshooting Path\n- If issues arise with InventoryService:\n  - **Check OrderService**: Monitor for any degradation or latency issues.\n  - **Review PricingService**: Ensure it is functioning correctly, as it may impact OrderService's performance.\n\n### Next Steps\n- Validate the health of OrderService and PricingService.\n- Monitor logs for any errors or performance metrics related to these services.",
    "trace_id": "6c43ba33-5d2f-46b8-8537-27f55a27a17b",
    "route": "graph_rag",
    "metrics": {
        "redactions": 0,
        "llm_latency_ms": 2986,
        "latency_ms": 2988
    }
}
```



### Document-driven question (policy/procedure)

This avoids unnecessary graph traversal and uses document RAG only.

```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -H "X-API-Key: change-me" -d "{\"query\":\"What is the data access policy for ProductDB?\"}"
```

Response:
```JSON
{"answer":"### Data Access Policy for ProductDB:\n- **Access Level**: Requires least privilege.\n- **Audit Requirement**: All queries must be audited.\n- **Sensitive Data Handling**: Sensitive fields must not be returned to logs or external services.\n\n### Next Steps:\n- **Verify User Permissions**: Ensure users have the appropriate access level based on their role.\n- **Audit Logs**: Check audit logs for compliance with query auditing.\n- **Review Logging Practices**: Confirm that sensitive fields are not included in logs or external services.","trace_id":"14f80fe3-49d7-4199-8e0a-3525f48b1abf","route":"doc_rag","sources":[{"doc_id":"DOC-003","title":"Data Access Policy - ProductDB","snippet":"ProductDB access requires least privilege. All queries must be audited. Sensitive fields must not be returned to logs or external services.","score":0.3382901333617146,"metadata":{"type":"policy","system":"ProductDB"}},{"doc_id":"DOC-001","title":"Incident Response - Message Bus Backlog","snippet":"If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.","score":0.13039794402867969,"metadata":{"type":"runbook","system":"MessageBus"}},{"doc_id":"DOC-005","title":"PricingService Change Management","snippet":"PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.","score":0.0,"metadata":{"type":"procedure","system":"PricingService"}},{"doc_id":"DOC-004","title":"WarehouseAPI Integration Guide","snippet":"WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.","score":0.0,"metadata":{"type":"guide","system":"WarehouseAPI"}},{"doc_id":"DOC-002","title":"OrderService Degradation Playbook","snippet":"OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.","score":0.0,"metadata":{"type":"runbook","system":"OrderService"}}],"metrics":{"redactions":0,"llm_latency_ms":2409,"latency_ms":2410}}
{
    "answer": "### Data Access Policy for ProductDB:\n- **Access Level**: Requires least privilege.\n- **Audit Requirement**: All queries must be audited.\n- **Sensitive Data Handling**: Sensitive fields must not be returned to logs or external services.\n\n### Next Steps:\n- **Verify User Permissions**: Ensure users have the appropriate access level based on their role.\n- **Audit Logs**: Check audit logs for compliance with query auditing.\n- **Review Logging Practices**: Confirm that sensitive fields are not included in logs or external services.",
    "trace_id": "14f80fe3-49d7-4199-8e0a-3525f48b1abf",
    "route": "doc_rag",
    "sources": [
        {
            "doc_id": "DOC-003",
            "title": "Data Access Policy - ProductDB",
            "snippet": "ProductDB access requires least privilege. All queries must be audited. Sensitive fields must not be returned to logs or external services.",
            "score": 0.3382901333617146,
            "metadata": {
                "type": "policy",
                "system": "ProductDB"
            }
        },
        {
            "doc_id": "DOC-001",
            "title": "Incident Response - Message Bus Backlog",
            "snippet": "If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.",
            "score": 0.13039794402867969,
            "metadata": {
                "type": "runbook",
                "system": "MessageBus"
            }
        },
        {
            "doc_id": "DOC-005",
            "title": "PricingService Change Management",
            "snippet": "PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.",
            "score": 0.0,
            "metadata": {
                "type": "procedure",
                "system": "PricingService"
            }
        },
        {
            "doc_id": "DOC-004",
            "title": "WarehouseAPI Integration Guide",
            "snippet": "WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.",
            "score": 0.0,
            "metadata": {
                "type": "guide",
                "system": "WarehouseAPI"
            }
        },
        {
            "doc_id": "DOC-002",
            "title": "OrderService Degradation Playbook",
            "snippet": "OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.",
            "score": 0.0,
            "metadata": {
                "type": "runbook",
                "system": "OrderService"
            }
        }
    ],
    "metrics": {
        "redactions": 0,
        "llm_latency_ms": 2409,
        "latency_ms": 2410
    }
}
```

## Hybrid reasoning (realistic ops question)
Dependencies + runbook guidance
```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -H "X-API-Key: change-me" -d "{\"query\":\"OrderService is timing out. What should I investigate first?\"}"
```

Response:
```JSON
{"answer":"To investigate the timeout issue with OrderService, follow these steps:\n\n1. **Check Downstream Dependencies**:\n   - Verify the latency of **InventoryService** and **PricingService** as they are direct dependencies.\n   - Ensure that there are no circuit breaker activations affecting these services.\n\n2. **Connection Pools and Thread Saturation**:\n   - Inspect the connection pools for OrderService to ensure they are not exhausted.\n   - Check for thread saturation in OrderService, which could lead to timeouts.\n\n3. **Monitor External Dependencies**:\n   - Review the status of the **WarehouseAPI** for any 4xx/5xx errors that could impact OrderService.\n\n4. **MessageBus Health**:\n   - Check the **MessageBus** for any backlog or consumer lag that might affect message processing.\n\n5. **Logs and Metrics**:\n   - Analyze logs for any error messages or patterns that coincide with the timeouts.\n   - Monitor metrics related to response times and error rates.\n\nBy following this path, you can systematically identify the root cause of the timeout issue.","trace_id":"c505049e-0ce1-4c26-b41f-c3f28d0dcdc1","route":"hybrid","sources":[{"doc_id":"DOC-002","title":"OrderService Degradation Playbook","snippet":"OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.","score":0.2531551114229024,"metadata":{"type":"runbook","system":"OrderService"}},{"doc_id":"DOC-005","title":"PricingService Change Management","snippet":"PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.","score":0.0,"metadata":{"type":"procedure","system":"PricingService"}},{"doc_id":"DOC-004","title":"WarehouseAPI Integration Guide","snippet":"WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.","score":0.0,"metadata":{"type":"guide","system":"WarehouseAPI"}},{"doc_id":"DOC-003","title":"Data Access Policy - ProductDB","snippet":"ProductDB access requires least privilege. All queries must be audited. Sensitive fields must not be returned to logs or external services.","score":0.0,"metadata":{"type":"policy","system":"ProductDB"}},{"doc_id":"DOC-001","title":"Incident Response - Message Bus Backlog","snippet":"If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.","score":0.0,"metadata":{"type":"runbook","system":"MessageBus"}}],"metrics":{"redactions":0,"llm_latency_ms":3578,"latency_ms":3578}}
{
    "answer": "To investigate the timeout issue with OrderService, follow these steps:\n\n1. **Check Downstream Dependencies**:\n   - Verify the latency of **InventoryService** and **PricingService** as they are direct dependencies.\n   - Ensure that there are no circuit breaker activations affecting these services.\n\n2. **Connection Pools and Thread Saturation**:\n   - Inspect the connection pools for OrderService to ensure they are not exhausted.\n   - Check for thread saturation in OrderService, which could lead to timeouts.\n\n3. **Monitor External Dependencies**:\n   - Review the status of the **WarehouseAPI** for any 4xx/5xx errors that could impact OrderService.\n\n4. **MessageBus Health**:\n   - Check the **MessageBus** for any backlog or consumer lag that might affect message processing.\n\n5. **Logs and Metrics**:\n   - Analyze logs for any error messages or patterns that coincide with the timeouts.\n   - Monitor metrics related to response times and error rates.\n\nBy following this path, you can systematically identify the root cause of the timeout issue.",
    "trace_id": "c505049e-0ce1-4c26-b41f-c3f28d0dcdc1",
    "route": "hybrid",
    "sources": [
        {
            "doc_id": "DOC-002",
            "title": "OrderService Degradation Playbook",
            "snippet": "OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.",
            "score": 0.2531551114229024,
            "metadata": {
                "type": "runbook",
                "system": "OrderService"
            }
        },
        {
            "doc_id": "DOC-005",
            "title": "PricingService Change Management",
            "snippet": "PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.",
            "score": 0.0,
            "metadata": {
                "type": "procedure",
                "system": "PricingService"
            }
        },
        {
            "doc_id": "DOC-004",
            "title": "WarehouseAPI Integration Guide",
            "snippet": "WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.",
            "score": 0.0,
            "metadata": {
                "type": "guide",
                "system": "WarehouseAPI"
            }
        },
        {
            "doc_id": "DOC-003",
            "title": "Data Access Policy - ProductDB",
            "snippet": "ProductDB access requires least privilege. All queries must be audited. Sensitive fields must not be returned to logs or external services.",
            "score": 0.0,
            "metadata": {
                "type": "policy",
                "system": "ProductDB"
            }
        },
        {
            "doc_id": "DOC-001",
            "title": "Incident Response - Message Bus Backlog",
            "snippet": "If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.",
            "score": 0.0,
            "metadata": {
                "type": "runbook",
                "system": "MessageBus"
            }
        }
    ],
    "metrics": {
        "redactions": 0,
        "llm_latency_ms": 3578,
        "latency_ms": 3578
    }
}
```




### 3️⃣ Governance & Safety 
Sensitive keyword redaction demo

This is where DLP or policy-based controls plug in. The hook is already there.

```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -H "X-API-Key: change-me" -d "{\"query\":\"Does ProductDB store passwords or secrets, such as password=aitX123?\"}"
```

Response:
```
{
    "answer": "- **ProductDB does not store passwords or secrets.** The provided context indicates that the sample password is redacted and is part of a data access policy that emphasizes least privilege and auditing.\n- **Next Steps:**\n  - Verify the Data Access Policy for any updates or changes regarding sensitive data handling.\n  - Ensure that all queries to ProductDB are audited and that sensitive fields are not logged.\n  - Confirm with the DataPlatform owner if there are any specific practices for managing secrets or sensitive information related to ProductDB.",
    "trace_id": "93d69562-4c81-463b-8e04-017de19591ae",
    "route": "hybrid",
    "sources": [
        {
            "doc_id": "DOC-003",
            "title": "Data Access Policy - ProductDB",
            "snippet": "ProductDB access requires least privilege. Sample password is password=[REDACTED] All queries must be audited. Sensitive fields must not be returned to logs or external services.",
            "score": 0.5049200677577248,
            "metadata": {
                "type": "policy",
                "system": "ProductDB"
            }
        },
        {
            "doc_id": "DOC-005",
            "title": "PricingService Change Management",
            "snippet": "PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.",
            "score": 0.0,
            "metadata": {
                "type": "procedure",
                "system": "PricingService"
            }
        },
        {
            "doc_id": "DOC-004",
            "title": "WarehouseAPI Integration Guide",
            "snippet": "WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.",
            "score": 0.0,
            "metadata": {
                "type": "guide",
                "system": "WarehouseAPI"
            }
        },
        {
            "doc_id": "DOC-002",
            "title": "OrderService Degradation Playbook",
            "snippet": "OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.",
            "score": 0.0,
            "metadata": {
                "type": "runbook",
                "system": "OrderService"
            }
        },
        {
            "doc_id": "DOC-001",
            "title": "Incident Response - Message Bus Backlog",
            "snippet": "If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.",
            "score": 0.0,
            "metadata": {
                "type": "runbook",
                "system": "MessageBus"
            }
        }
    ],
    "metrics": {
        "redactions": 3,
        "blocked": 0,
        "llm_latency_ms": 1632,
        "latency_ms": 1633
    }
}
```


## 5️⃣ Regression & Evaluation 
## Run the test suite
These are deterministic test cases to prevent prompt or retrieval regressions — part of LLMOps.
```
pytest -q
```

Output:
```
.                                  [100%]
1 passed in 2.25s
```

## Run evaluation runner manually

This is how we batch-evaluate new prompts or models before promotion.
```
python -c "from evaluation.runner import run_cases; print(run_cases('evaluation/test_cases.yaml'))"
```

outout:
```JSON
Building LLM client for provider: mock
[
    {
        "id": "case-001",
        "answer": "MOCK RESPONSE (offline mode). Using retrieved context:\n\nDependency view:\n- ProductDB (type=data, owner=DataPlatform, tier=data)\n- InventoryService (type=service, owner=SupplyOps, tier=app)\n- PricingService (type=service, owner=FinanceIT, tier=app)\n- OrderService (type=service, owner=SupplyOps, tier=app)\n- MessageBus (type=infra, owner=Platform, tier=infra)\n\nKey retrieved guidance:\n- [DOC-002] OrderService Degradation Playbook: OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.\n- [DOC-001] Incident Response - Message Bus Backlog: If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.\n- [DOC-005] PricingService Change Management: PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.\n\nAction plan:\n- Verify upstream/downstream dependencies and error rates.\n- Follow the most relevant runbook/policy from retrieved docs.\n- Capture trace_id and latency for observability.",
        "route": "hybrid",
        "metrics": {
            "redactions": 2,
            "blocked": 0,
            "latency_ms": 3
        }
    },
    {
        "id": "case-002",
        "answer": "MOCK RESPONSE (offline mode). Using retrieved context:\n\nDependency view:\n- ProductDB (type=data, owner=DataPlatform, tier=data)\n- InventoryService (type=service, owner=SupplyOps, tier=app)\n- PricingService (type=service, owner=FinanceIT, tier=app)\n- OrderService (type=service, owner=SupplyOps, tier=app)\n- MessageBus (type=infra, owner=Platform, tier=infra)\n\nKey retrieved guidance:\n- [DOC-001] Incident Response - Message Bus Backlog: If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.\n- [DOC-005] PricingService Change Management: PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.\n- [DOC-004] WarehouseAPI Integration Guide: WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.\n\nAction plan:\n- Verify upstream/downstream dependencies and error rates.\n- Follow the most relevant runbook/policy from retrieved docs.\n- Capture trace_id and latency for observability.",
        "route": "hybrid",
        "metrics": {
            "redactions": 2,
            "blocked": 0,
            "latency_ms": 0
        }
    },
    {
        "id": "case-003",
        "answer": "MOCK RESPONSE (offline mode). Using retrieved context:\n\nKey retrieved guidance:\n- [DOC-003] Data Access Policy - ProductDB: ProductDB access requires least privilege. Sample password is password=[REDACTED] All queries must be audited. Sensitive fields must not be returned to logs or external services.\n- [DOC-001] Incident Response - Message Bus Backlog: If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.\n- [DOC-005] PricingService Change Management: PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.\n\nAction plan:\n- Verify upstream/downstream dependencies and error rates.\n- Follow the most relevant runbook/policy from retrieved docs.\n- Capture trace_id and latency for observability.",
        "route": "doc_rag",
        "metrics": {
            "redactions": 2,
            "blocked": 0,
            "latency_ms": 3
        }
    }
]
```



## 6️⃣ Failure / Fallback Demo (Enterprise realism)
CI and local dev don’t depend on paid APIs — production swaps in Azure OpenAI.
Run without LLM credentials
```
Edit .env:

LLM_PROVIDER=mock
```

Restart uvicorn, 
```
uvicorn api.main:app --host 127.0.0.1 --port 8000 --log-level debug     
```

then in cmd...:
```
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -H "X-API-Key: change-me" -d "{\"query\":\"MessageBus backlog is increasing. What should I do?\"}"
```

output:
```
{
    "answer": "MOCK RESPONSE (offline mode). Using retrieved context:\n\nDependency view:\n- ProductDB (type=data, owner=DataPlatform, tier=data)\n- PricingService (type=service, owner=FinanceIT, tier=app)\n- WarehouseAPI (type=external, owner=3PL, tier=external)\n- MessageBus (type=infra, owner=Platform, tier=infra)\n- InventoryService (type=service, owner=SupplyOps, tier=app)\n\nKey retrieved guidance:\n- [DOC-001] Incident Response - Message Bus Backlog: If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.\n- [DOC-005] PricingService Change Management: PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.\n- [DOC-004] WarehouseAPI Integration Guide: WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.\n\nAction plan:\n- Verify upstream/downstream dependencies and error rates.\n- Follow the most relevant runbook/policy from retrieved docs.\n- Capture trace_id and latency for observability.",
    "trace_id": "6214148a-101b-4eef-9841-f595e6ed3c04",
    "route": "hybrid",
    "sources": [
        {
            "doc_id": "DOC-001",
            "title": "Incident Response - Message Bus Backlog",
            "snippet": "If MessageBus backlog increases: check consumer lag, autoscaling settings, dead-letter queues, and upstream publish rate. Validate retry policy and monitor broker CPU and disk.",
            "score": 0.31940842637826583,
            "metadata": {
                "type": "runbook",
                "system": "MessageBus"
            }
        },
        {
            "doc_id": "DOC-005",
            "title": "PricingService Change Management",
            "snippet": "PricingService changes require approval and rollout via CI/CD. Canary deployments are recommended. Track latency and error budgets.",
            "score": 0.0,
            "metadata": {
                "type": "procedure",
                "system": "PricingService"
            }
        },
        {
            "doc_id": "DOC-004",
            "title": "WarehouseAPI Integration Guide",
            "snippet": "WarehouseAPI is an external 3PL endpoint. Use exponential backoff, idempotency keys, and failover routing. Monitor 4xx/5xx rate.",
            "score": 0.0,
            "metadata": {
                "type": "guide",
                "system": "WarehouseAPI"
            }
        },
        {
            "doc_id": "DOC-003",
            "title": "Data Access Policy - ProductDB",
            "snippet": "ProductDB access requires least privilege. Sample password is password=[REDACTED] All queries must be audited. Sensitive fields must not be returned to logs or external services.",
            "score": 0.0,
            "metadata": {
                "type": "policy",
                "system": "ProductDB"
            }
        },
        {
            "doc_id": "DOC-002",
            "title": "OrderService Degradation Playbook",
            "snippet": "OrderService depends on InventoryService and PricingService. If timeouts occur, verify downstream latency and circuit breaker settings. Check connection pools and thread saturation.",
            "score": 0.0,
            "metadata": {
                "type": "runbook",
                "system": "OrderService"
            }
        }
    ],
    "metrics": {
        "redactions": 2,
        "blocked": 0,
        "latency_ms": 2
    }
}
```



## 7️⃣ Container / Production Readiness
This is deployable as-is to App Service, AKS, or container apps.

Build & run with Docker
```
docker compose up --build
```

Then in cmd:
```
curl http://127.0.0.1:8000/health
```

output:
```
{"ok":true}
```