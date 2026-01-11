import networkx as nx


def load_demo_graph() -> nx.DiGraph:
    """
    Demo operational dependency graph.
    Replace with Neo4j loader later if desired.
    """
    g = nx.DiGraph()

    # Nodes (systems/services)
    g.add_node("OrderService", type="service", owner="SupplyOps", tier="app")
    g.add_node("InventoryService", type="service", owner="SupplyOps", tier="app")
    g.add_node("PricingService", type="service", owner="FinanceIT", tier="app")
    g.add_node("MessageBus", type="infra", owner="Platform", tier="infra")
    g.add_node("ProductDB", type="data", owner="DataPlatform", tier="data")
    g.add_node("WarehouseAPI", type="external", owner="3PL", tier="external")

    # Edges (dependencies)
    g.add_edge("OrderService", "InventoryService", rel="depends_on")
    g.add_edge("OrderService", "PricingService", rel="depends_on")
    g.add_edge("InventoryService", "ProductDB", rel="reads_from")
    g.add_edge("PricingService", "ProductDB", rel="reads_from")
    g.add_edge("OrderService", "MessageBus", rel="publishes_to")
    g.add_edge("InventoryService", "MessageBus", rel="subscribes_to")
    g.add_edge("InventoryService", "WarehouseAPI", rel="calls")

    return g
