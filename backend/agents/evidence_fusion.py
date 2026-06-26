from typing import Any, Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


class EvidenceFusionAgent(BaseAgent):
    def __init__(self):
        super().__init__("evidence_fusion")

    async def execute(self, context: AgentContext) -> AgentResult:
        intermediate = context.intermediate_results
        query = context.query

        results = []
        for agent_name, result in intermediate.items():
            if isinstance(result, dict):
                results.append(result)

        model_scores = self._aggregate_model_scores(results)
        agent_scores = self._aggregate_agent_scores(results)
        threat_assessment = self._compute_threat_assessment(model_scores, agent_scores)
        unified_report = self._build_unified_report(query, model_scores, agent_scores, threat_assessment)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=unified_report,
            confidence=threat_assessment["confidence"],
            metadata={
                "models_fused": len(model_scores),
                "agents_fused": len(agent_scores),
                "threat_verdict": threat_assessment["verdict"],
            },
        )

    def _aggregate_model_scores(self, results: List[Dict]) -> Dict:
        scores = {}
        for r in results:
            model_id = r.get("model_id")
            if model_id:
                scores[model_id] = {
                    "verdict": r.get("verdict", "UNKNOWN"),
                    "threat_score": r.get("threat_score", 50),
                    "confidence": r.get("confidence", 0.5),
                    "type": r.get("type", "unknown"),
                    "elapsed_s": r.get("elapsed_s", 0),
                }
        return scores

    def _aggregate_agent_scores(self, results: List[Dict]) -> Dict:
        agents = {}
        for r in results:
            agent_name = r.get("agent_name")
            if agent_name and agent_name not in ("evidence_fusion", "securityllm_synthesis"):
                output = r.get("output", {})
                if isinstance(output, dict):
                    agents[agent_name] = {
                        "success": r.get("success", False),
                        "confidence": r.get("confidence", 0),
                        "latency_ms": r.get("latency_ms", 0),
                        "summary": output.get("summary", output.get("prediction", "")),
                    }
                elif isinstance(output, str):
                    agents[agent_name] = {
                        "success": r.get("success", False),
                        "confidence": r.get("confidence", 0),
                        "latency_ms": r.get("latency_ms", 0),
                        "summary": output[:200],
                    }
        return agents

    def _compute_threat_assessment(self, model_scores: Dict, agent_scores: Dict) -> Dict:
        all_threat_scores = [m["threat_score"] for m in model_scores.values()]
        all_confidences = [m["confidence"] for m in model_scores.values() if m.get("confidence")]

        avg_threat = sum(all_threat_scores) / max(len(all_threat_scores), 1) if all_threat_scores else 50
        avg_confidence = sum(all_confidences) / max(len(all_confidences), 1) if all_confidences else 0.5

        if avg_threat >= 70:
            verdict = "BLOCK"
            confidence = min(0.5 + 0.2 * len(model_scores), 0.98)
        elif avg_threat >= 40:
            verdict = "UNCERTAIN"
            confidence = min(0.4 + 0.1 * len(model_scores), 0.85)
        else:
            verdict = "ACCEPT"
            confidence = min(0.5 + 0.15 * len(model_scores), 0.95)

        return {
            "verdict": verdict,
            "average_threat_score": round(avg_threat, 1),
            "average_confidence": round(avg_confidence, 3),
            "confidence": round(confidence, 3),
            "models_contributing": len(model_scores),
            "agents_contributing": len(agent_scores),
        }

    def _build_unified_report(self, query: str, model_scores: Dict, agent_scores: Dict, threat: Dict) -> Dict:
        report = {
            "query_preview": query[:200],
            "threat_assessment": threat,
            "models": model_scores,
            "agents": agent_scores,
            "evidence_summary": {
                "total_models": len(model_scores),
                "total_agents": len(agent_scores),
                "block_votes": sum(1 for m in model_scores.values() if m.get("verdict") == "BLOCK"),
                "accept_votes": sum(1 for m in model_scores.values() if m.get("verdict") == "ACCEPT"),
                "total_latency_ms": sum(a.get("latency_ms", 0) for a in agent_scores.values()),
            },
        }

        if threat["verdict"] == "BLOCK":
            report["summary"] = "Menace confirmee par analyse multi-modeles"
        elif threat["verdict"] == "ACCEPT":
            report["summary"] = "Contenu legitime - aucun marqueur de menace significatif"
        else:
            report["summary"] = "Resultats divergents - analyse supplementaire recommandee"

        return report
