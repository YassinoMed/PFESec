import numpy as np
from typing import Any, Dict, List, Optional


class EvidenceFuser:
    def __init__(self):
        self.weights = {
            "cysecbert": 1.0,
            "secbert": 1.0,
            "phishsense": 1.2,
            "securityllm": 1.3,
        }

    def fuse_classifications(self, results: List[Dict]) -> Dict:
        if not results:
            return {"verdict": "UNKNOWN", "confidence": 0.0}

        weighted_votes = {"BLOCK": 0.0, "ACCEPT": 0.0}
        total_confidence = 0.0

        for r in results:
            model_id = r.get("model_id", "unknown")
            verdict = r.get("verdict", "UNKNOWN")
            confidence = r.get("confidence", 0.5)
            weight = self.weights.get(model_id, 1.0)

            if verdict in weighted_votes:
                weighted_votes[verdict] += confidence * weight
                total_confidence += weight

        if total_confidence > 0:
            block_pct = weighted_votes["BLOCK"] / total_confidence
            accept_pct = weighted_votes["ACCEPT"] / total_confidence

            if block_pct > accept_pct:
                verdict = "BLOCK"
                confidence = block_pct
            elif accept_pct > block_pct:
                verdict = "ACCEPT"
                confidence = accept_pct
            else:
                verdict = "UNCERTAIN"
                confidence = max(block_pct, accept_pct)
        else:
            verdict = "UNKNOWN"
            confidence = 0.0

        return {
            "verdict": verdict,
            "confidence": round(min(confidence, 1.0), 3),
            "block_weight": round(weighted_votes["BLOCK"], 3),
            "accept_weight": round(weighted_votes["ACCEPT"], 3),
            "model_count": len(results),
        }

    def fuse_rag_contexts(self, contexts: List[str], scores: List[float]) -> str:
        if not contexts:
            return ""

        sorted_pairs = sorted(zip(contexts, scores), key=lambda x: x[1], reverse=True)
        top = sorted_pairs[:3]

        seen = set()
        unique = []
        for text, score in top:
            key = text[:50]
            if key not in seen:
                seen.add(key)
                unique.append(text)

        return "\n\n".join(unique)

    def compute_threat_score(self, model_results: List[Dict], agent_results: List[Dict]) -> float:
        scores = []

        for r in model_results:
            if "threat_score" in r:
                scores.append(r["threat_score"] / 100.0)

        for r in agent_results:
            if isinstance(r.get("output"), dict):
                o = r["output"]
                if "risk_summary" in o:
                    rs = o["risk_summary"]
                    if rs.get("max_risk"):
                        scores.append(rs["max_risk"] / 100.0)
                if "quality" in o:
                    scores.append(1.0 - o["quality"].get("score", 50) / 100.0)

        return round(float(np.mean(scores)) * 100, 1) if scores else 50.0
