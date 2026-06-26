import time
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ModelMonitor:
    def __init__(self, storage_path: str = "backend/governance/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, List[Dict]] = {}

    def record_inference(self, model_id: str, latency_ms: float, success: bool, confidence: Optional[float] = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "latency_ms": latency_ms,
            "success": success,
            "confidence": confidence,
        }
        self.metrics.setdefault(model_id, []).append(entry)
        self._persist(model_id, entry)

    def _persist(self, model_id: str, entry: Dict):
        log_path = self.storage_path / f"{model_id}_metrics.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_model_stats(self, model_id: str, last_n: int = 100) -> Dict:
        entries = self.metrics.get(model_id, [])[-last_n:]
        if not entries:
            return {"model_id": model_id, "total_calls": 0}

        success_count = sum(1 for e in entries if e["success"])
        avg_latency = sum(e["latency_ms"] for e in entries) / len(entries)
        confidences = [e["confidence"] for e in entries if e.get("confidence") is not None]

        return {
            "model_id": model_id,
            "total_calls": len(entries),
            "success_rate": round(success_count / len(entries), 3),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
            "last_called": entries[-1]["timestamp"],
        }

    def get_all_stats(self) -> Dict[str, Dict]:
        return {mid: self.get_model_stats(mid) for mid in self.metrics}

    def detect_drift(self, model_id: str, window: int = 50) -> Dict:
        entries = self.metrics.get(model_id, [])[-window:]
        if len(entries) < 10:
            return {"drift_detected": False, "message": "Donnees insuffisantes"}

        recent = entries[-10:]
        older = entries[:-10]

        recent_conf = [e["confidence"] for e in recent if e.get("confidence")]
        older_conf = [e["confidence"] for e in older if e.get("confidence")]

        if not recent_conf or not older_conf:
            return {"drift_detected": False, "message": "Pas assez de donnees de confiance"}

        recent_avg = sum(recent_conf) / len(recent_conf)
        older_avg = sum(older_conf) / len(older_conf)

        drift = abs(recent_avg - older_avg)
        return {
            "drift_detected": drift > 0.15,
            "drift_score": round(drift, 4),
            "recent_avg_confidence": round(recent_avg, 3),
            "historical_avg_confidence": round(older_avg, 3),
            "message": "Drift detecte" if drift > 0.15 else "Normal",
        }
