from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Node:
    node_id: str
    label: str
    props: Dict[str, Any]


@dataclass
class Edge:
    src: str
    dst: str
    rel: str
    props: Dict[str, Any]
