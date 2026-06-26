import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditLogger:
    def __init__(self, log_path: str = "backend/governance/audit_logs"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)

    def log(self, entry_type: str, data: Dict):
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            **data,
        }
        log_file = self.log_path / f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["audit_id"]

    def query(self, start_date: str, end_date: str, entry_type: Optional[str] = None) -> List[Dict]:
        results = []
        for f in sorted(self.log_path.glob("*.jsonl")):
            date_str = f.stem
            if date_str < start_date.replace("-", "") or date_str > end_date.replace("-", ""):
                continue
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    entry = json.loads(line)
                    if entry_type and entry.get("type") != entry_type:
                        continue
                    results.append(entry)
        return results

    def get_recent(self, limit: int = 50) -> List[Dict]:
        entries = []
        for f in sorted(self.log_path.glob("*.jsonl"), reverse=True):
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    entries.append(json.loads(line))
                    if len(entries) >= limit:
                        return entries
        return entries
