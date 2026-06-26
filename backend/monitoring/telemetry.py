import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"
    error: Optional[str] = None

    def finish(self):
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return round((end - self.start_time) * 1000, 2)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "status": self.status,
            "error": self.error,
        }


class TelemetryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.spans: List[Span] = []
        self.active_spans: Dict[str, Span] = {}

    def start_span(self, name: str, trace_id: str, parent_id: Optional[str] = None, attributes: Optional[Dict] = None) -> Span:
        span = Span(
            name=name,
            trace_id=trace_id,
            parent_id=parent_id,
            attributes=attributes or {},
        )
        self.active_spans[span.span_id] = span
        return span

    def end_span(self, span: Span, status: str = "OK", error: Optional[str] = None):
        span.finish()
        span.status = status
        span.error = error
        self.spans.append(span)
        self.active_spans.pop(span.span_id, None)

    def get_trace(self, trace_id: str) -> List[Dict]:
        return [s.to_dict() for s in self.spans if s.trace_id == trace_id]

    def get_all_spans(self, limit: int = 100) -> List[Dict]:
        return [s.to_dict() for s in self.spans[-limit:]]

    def get_latency_stats(self, span_name: str, last_n: int = 50) -> Dict:
        matching = [s for s in self.spans[-last_n:] if s.name == span_name]
        if not matching:
            return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "count": 0}

        durations = [s.duration_ms for s in matching]
        return {
            "avg_ms": round(sum(durations) / len(durations), 2),
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2),
            "count": len(matching),
        }

    def get_error_rate(self, last_n: int = 100) -> float:
        recent = self.spans[-last_n:]
        if not recent:
            return 0.0
        errors = sum(1 for s in recent if s.status == "ERROR")
        return round(errors / len(recent), 3)

    def clear(self):
        self.spans.clear()
        self.active_spans.clear()
