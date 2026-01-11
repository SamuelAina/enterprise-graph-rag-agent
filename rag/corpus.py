from typing import List, Dict, Any


def load_demo_corpus() -> List[Dict[str, Any]]:
    """
    Demo documents - replace with real enterprise content later.
    """
    return [
        {
            "doc_id": "DOC-001",
            "title": "Incident Response - Message Bus Backlog",
            "text": (
                "If MessageBus backlog increases: check consumer lag, autoscaling settings, "
                "dead-letter queues, and upstream publish rate. Validate retry policy and "
                "monitor broker CPU and disk."
            ),
            "metadata": {"type": "runbook", "system": "MessageBus"},
        },
        {
            "doc_id": "DOC-002",
            "title": "OrderService Degradation Playbook",
            "text": (
                "OrderService depends on InventoryService and PricingService. "
                "If timeouts occur, verify downstream latency and circuit breaker settings. "
                "Check connection pools and thread saturation."
            ),
            "metadata": {"type": "runbook", "system": "OrderService"},
        },
        {
            "doc_id": "DOC-003",
            "title": "Data Access Policy - ProductDB",
            "text": (
                "ProductDB access requires least privilege. Sample password is password=SuperSecret123. All queries must be audited. "
                "Sensitive fields must not be returned to logs or external services."
            ),
            "metadata": {"type": "policy", "system": "ProductDB"},
        },
        {
            "doc_id": "DOC-004",
            "title": "WarehouseAPI Integration Guide",
            "text": (
                "WarehouseAPI is an external 3PL endpoint. Use exponential backoff, "
                "idempotency keys, and failover routing. Monitor 4xx/5xx rate."
            ),
            "metadata": {"type": "guide", "system": "WarehouseAPI"},
        },
        {
            "doc_id": "DOC-005",
            "title": "PricingService Change Management",
            "text": (
                "PricingService changes require approval and rollout via CI/CD. "
                "Canary deployments are recommended. Track latency and error budgets."
            ),
            "metadata": {"type": "procedure", "system": "PricingService"},
        },
    ]
