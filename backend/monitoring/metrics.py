import time
from collections import defaultdict
from typing import Any, Dict, List, Optional


class MetricsCollector:
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
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.max_histogram_size = 1000

    def increment(self, metric: str, value: int = 1):
        self.counters[metric] += value

    def gauge(self, metric: str, value: float):
        self.gauges[metric] = value

    def observe(self, metric: str, value: float):
        self.histograms[metric].append(value)
        if len(self.histograms[metric]) > self.max_histogram_size:
            self.histograms[metric] = self.histograms[metric][-self.max_histogram_size:]

    def get_counters(self) -> Dict[str, int]:
        return dict(self.counters)

    def get_gauges(self) -> Dict[str, float]:
        return dict(self.gauges)

    def get_histograms(self) -> Dict[str, Dict]:
        result = {}
        for metric, values in self.histograms.items():
            if values:
                result[metric] = {
                    "count": len(values),
                    "avg": round(sum(values) / len(values), 4),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "p50": round(sorted(values)[len(values) // 2], 4),
                    "p95": round(sorted(values)[int(len(values) * 0.95)], 4),
                    "p99": round(sorted(values)[int(len(values) * 0.99)], 4),
                }
        return result

    def get_all_metrics(self) -> Dict:
        return {
            "counters": self.get_counters(),
            "gauges": self.get_gauges(),
            "histograms": self.get_histograms(),
        }

    def snapshot(self) -> str:
        import json
        return json.dumps(self.get_all_metrics(), indent=2)

    def reset(self):
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
