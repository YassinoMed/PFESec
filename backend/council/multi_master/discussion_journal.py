"""Discussion Journal — Audit trail temps réel de l'architecture Multi-Master.

Enregistre chronologiquement tous les échanges entre le Coordinator,
les Masters AI, et leurs experts. Supporte l'export en temps réel
pour le Dashboard WebSocket.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class DiscussionJournal:
    """Journal d'orchestration temps réel — n'expose jamais le raisonnement interne des modèles.

    Enregistre :
    - Activation des Masters
    - Plans d'analyse construits
    - Échanges Master ↔ Experts
    - Discussions inter-Masters
    - Contradictions détectées
    - Résolution des désaccords
    - Consensus pondéré
    - Rapport final
    """

    def __init__(self, session_id: Optional[str] = None, log_dir: str = "logs/discussion"):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.log_dir = log_dir
        self._entries: List[Dict] = []
        self._listeners: List[Callable] = []
        self._started_at = time.time()

    # ── Event types ───────────────────────────────────────────────────────

    def coordinator_opened(self, message: str = "Nouvelle session ouverte."):
        self._log("coordinator", "global_coordinator", None, message, icon="🧠")

    def master_activated(self, master_id: str, master_name: str, plan_summary: str = ""):
        self._log("master_activation", master_id, None,
                  f"Activation de {master_name}. {plan_summary}", icon="🛡")

    def master_plan(self, master_id: str, master_name: str, steps: List[str]):
        for step in steps:
            self._log("master_planning", master_id, None, step, icon="📋")

    def expert_queried(self, master_id: str, expert_name: str, question: str):
        self._log("expert_query", master_id, expert_name, question, icon="🎯")

    def expert_responded(self, master_id: str, expert_name: str, summary: str):
        self._log("expert_response", expert_name, master_id, summary, icon="💬")

    def master_discussion(self, round_n: int, speaker: str, target: Optional[str], message: str):
        self._log("discussion", speaker, target,
                  f"[Tour {round_n}] {message}", icon="🗣")

    def contradiction_detected(self, left: str, right: str, detail: str):
        self._log("contradiction", left, right, detail, icon="⚡")

    def contradiction_resolved(self, left: str, right: str, resolution: str):
        self._log("contradiction_resolved", left, right, resolution, icon="✅")

    def consensus_in_progress(self, detail: str = "Consensus en cours."):
        self._log("consensus", "weighted_consensus_engine", None, detail, icon="⚖")

    def consensus_reached(self, score: float, verdict: str, detail: str):
        self._log("consensus_final", "weighted_consensus_engine", None,
                  f"Consensus final: {score:.1f}%. Décision: {verdict}. {detail}", icon="🏁")

    def report_generated(self, report_summary: str):
        self._log("report", "securityllm_report_engine", None, report_summary, icon="📊")

    def master_completed(self, master_id: str, master_name: str, verdict: str, score: float):
        self._log("master_completed", master_id, None,
                  f"{master_name} terminé: {verdict} (score: {score:.1f}%)", icon="✅")

    def error(self, source: str, message: str):
        self._log("error", source, None, message, icon="❌")

    # ── Core ──────────────────────────────────────────────────────────────

    def _log(self, event_type: str, source: str, target: Optional[str], message: str, icon: str = ""):
        entry = {
            "type": event_type,
            "source": source,
            "target": target,
            "message": message,
            "icon": icon,
            "elapsed_ms": round((time.time() - self._started_at) * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._entries.append(entry)
        self._persist(entry)
        self._notify(entry)

    def get_entries(self, since_index: int = 0) -> List[Dict]:
        return self._entries[since_index:]

    def get_all(self) -> List[Dict]:
        return list(self._entries)

    # ── Listeners (pour WebSocket push) ────────────────────────────────────

    def add_listener(self, callback: Callable[[Dict], None]):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ── Persistence ───────────────────────────────────────────────────────

    def _persist(self, entry: Dict):
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            path = os.path.join(self.log_dir, f"journal_{self.session_id}.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def _notify(self, entry: Dict):
        for cb in self._listeners:
            try:
                cb(entry)
            except Exception:
                pass
