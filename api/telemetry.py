import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_ts: float = field(default_factory=time.time)
    events: list[dict] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def event(self, name: str, **kwargs):
        self.events.append({"name": name, "ts": time.time(), **kwargs})

    def set_metric(self, key: str, value: Any):
        self.metrics[key] = value

    def finish(self):
        self.set_metric("latency_ms", int((time.time() - self.start_ts) * 1000))
        return self
