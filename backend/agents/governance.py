import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


class AIGovernanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("ai_governance")
        self.audit_log: List[Dict] = []
        self.performance_history: Dict[str, List[Dict]] = {}
        self.drift_scores: Dict[str, float] = {}
        self.cost_tracking: Dict[str, float] = {}

    async def execute(self, context: AgentContext) -> AgentResult:
        intermediate = context.intermediate_results
        trace_id = context.trace_id

        audit_entry = self._create_audit_entry(context, intermediate)
        self.audit_log.append(audit_entry)

        drift_summary = self._check_drift(intermediate)
        cost_summary = self._estimate_costs(intermediate)
        performance_summary = self._summarize_performance(intermediate)

        governance_report = {
            "trace_id": trace_id,
            "session_id": context.session_id,
            "timestamp": audit_entry["timestamp"],
            "audit": {
                "entry_id": len(self.audit_log),
                "agents_executed": audit_entry["agents"],
                "total_latency_ms": audit_entry["total_latency_ms"],
                "success_rate": audit_entry["success_rate"],
            },
            "drift": drift_summary,
            "costs": cost_summary,
            "performance": performance_summary,
            "governance_status": "COMPLIANT" if drift_summary["drift_detected"] is False else "MONITORING",
        }

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=governance_report,
            confidence=0.95,
            metadata={"audit_entries": len(self.audit_log), "drift_ok": not drift_summary["drift_detected"]},
        )

    def _create_audit_entry(self, context: AgentContext, intermediate: Dict) -> Dict:
        agents = []
        total_latency = 0
        success_count = 0
        total_count = 0

        for name, result in intermediate.items():
            if isinstance(result, dict):
                agents.append({
                    "name": name,
                    "success": result.get("success", False),
                    "latency_ms": result.get("latency_ms", 0),
                    "confidence": result.get("confidence", 0),
                })
                total_latency += result.get("latency_ms", 0)
                if result.get("success", False):
                    success_count += 1
                total_count += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "trace_id": context.trace_id,
            "session_id": context.session_id,
            "query_preview": context.query[:100],
            "user_role": context.user_role,
            "agents": agents,
            "total_latency_ms": round(total_latency, 2),
            "success_rate": round(success_count / max(total_count, 1), 3),
            "total_agents": total_count,
        }

    def _check_drift(self, intermediate: Dict) -> Dict:
        drift_detected = False
        anomalies = []

        for name, result in intermediate.items():
            if isinstance(result, dict):
                confidence = result.get("confidence", 0)
                success = result.get("success", True)

                if confidence < 0.3:
                    drift_detected = True
                    anomalies.append(f"{name}: confiance anormalement basse ({confidence:.2f})")
                if not success:
                    anomalies.append(f"{name}: echec d'execution")

                hist = self.performance_history.setdefault(name, [])
                hist.append({"timestamp": time.time(), "confidence": confidence, "success": success})
                if len(hist) > 100:
                    hist.pop(0)

                if len(hist) > 5:
                    recent = [h["confidence"] for h in hist[-5:]]
                    avg = sum(recent) / len(recent)
                    if abs(avg - confidence) > 0.3:
                        drift_detected = True
                        anomalies.append(f"{name}: variation de confiance detectee ({avg:.2f} -> {confidence:.2f})")

        return {"drift_detected": drift_detected, "anomalies": anomalies, "checks_performed": len(intermediate)}

    def _estimate_costs(self, intermediate: Dict) -> Dict:
        total_cost = 0.0
        breakdown = {}

        for name, result in intermediate.items():
            if isinstance(result, dict):
                latency_s = result.get("latency_ms", 0) / 1000
                if latency_s > 0:
                    cost = latency_s * 0.00005
                    total_cost += cost
                    breakdown[name] = round(cost, 6)

        return {
            "total_estimated_cost": round(total_cost, 6),
            "currency": "USD",
            "breakdown": breakdown,
            "note": "Estimation basee sur le temps GPU (0.05$/s)",
        }

    def _summarize_performance(self, intermediate: Dict) -> Dict:
        avg_latency = 0
        avg_confidence = 0
        count = 0

        for name, result in intermediate.items():
            if isinstance(result, dict) and name != "ai_governance":
                avg_latency += result.get("latency_ms", 0)
                confidence = result.get("confidence", 0)
                if confidence:
                    avg_confidence += confidence
                count += 1

        return {
            "average_latency_ms": round(avg_latency / max(count, 1), 2),
            "average_confidence": round(avg_confidence / max(count, 1), 3) if avg_confidence else 0,
            "total_executions": count,
            "health_status": "HEALTHY" if avg_confidence > 0.5 else "DEGRADED",
        }
