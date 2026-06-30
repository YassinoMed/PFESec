"""Weighted Consensus Engine — Calcul du consensus pondéré entre Masters AI.

Chaque Master possède un poids fixe :
- Threat Master : 0.40
- SOC Master : 0.35
- RAG Master : 0.25

Le consensus calcule :
1. Score global = somme des (score_Master × poids_Master)
2. Niveau de confiance basé sur le score final
3. Détection de désaccords persistants
4. Justification de la décision
"""

from typing import Dict, List

from backend.council.multi_master.types import MasterVerdict, WeightedConsensus


class WeightedConsensusEngine:
    """Calcule le consensus pondéré entre les verdicts des Masters."""

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "threat_master": 0.40,
        "soc_master": 0.35,
        "rag_master": 0.25,
    }

    def compute(
        self,
        verdicts: Dict[str, MasterVerdict],
        discussion_log: List,
        discussion_rounds: int,
        weights: Dict[str, float] = None,
    ) -> WeightedConsensus:
        if weights is None:
            weights = dict(self.DEFAULT_WEIGHTS)

        # 1. Vérifier que tous les Masters ont voté
        active_masters = list(verdicts.keys())
        if not active_masters:
            return self._empty_consensus(weights)

        # 2. Normaliser les poids pour les Masters actifs
        active_weights = {mid: weights.get(mid, 0) for mid in active_masters}
        total_w = sum(active_weights.values())
        if total_w > 0:
            norm_weights = {mid: w / total_w for mid, w in active_weights.items()}
        else:
            norm_weights = {mid: 1.0 / len(active_masters) for mid in active_masters}

        # 3. Calculer le score global pondéré
        global_score = sum(
            verdicts[mid].score * norm_weights.get(mid, 0)
            for mid in active_masters
        )

        # 4. Déterminer le verdict final majoritaire pondéré
        verdict_scores: Dict[str, float] = {}
        for mid in active_masters:
            v = verdicts[mid].conclusion
            if v != "UNKNOWN":
                verdict_scores[v] = verdict_scores.get(v, 0.0) + norm_weights.get(mid, 0)

        if not verdict_scores:
            verdict_final = "UNKNOWN"
        else:
            verdict_final = max(verdict_scores, key=verdict_scores.get)

        # 5. Détection des contradictions résiduelles
        contradictions = self._detect_residual_contradictions(verdicts, active_masters)

        # 6. Niveau de confiance
        confidence_level = (
            "High" if global_score >= 80.0
            else "Medium" if global_score >= 50.0
            else "Low"
        )

        # 7. Justification
        justification = self._build_justification(
            verdict_final, global_score, verdicts, active_masters, contradictions
        )

        return WeightedConsensus(
            score=round(global_score, 2),
            confidence_level=confidence_level,
            verdict_final=verdict_final,
            weights_used={k: round(v, 3) for k, v in norm_weights.items()},
            master_verdicts=verdicts,
            contradictions=contradictions,
            contradictions_resolved=len(contradictions) == 0,
            decision_justification=justification,
        )

    def _detect_residual_contradictions(
        self,
        verdicts: Dict[str, MasterVerdict],
        active_masters: List[str],
    ) -> List[Dict]:
        contradictions = []
        for i, left_id in enumerate(active_masters):
            for right_id in active_masters[i + 1:]:
                left = verdicts[left_id]
                right = verdicts[right_id]
                if left.conclusion != right.conclusion and left.conclusion != "UNKNOWN" and right.conclusion != "UNKNOWN":
                    contradictions.append({
                        "left": left_id,
                        "right": right_id,
                        "left_conclusion": left.conclusion,
                        "right_conclusion": right.conclusion,
                        "left_score": left.score,
                        "right_score": right.score,
                        "resolved": False,
                    })
        return contradictions

    def _build_justification(
        self,
        verdict_final: str,
        global_score: float,
        verdicts: Dict[str, MasterVerdict],
        active_masters: List[str],
        contradictions: List[Dict],
    ) -> str:
        parts = [
            f"Décision finale: {verdict_final} (score consensus: {global_score:.1f}%).",
            f"Masters participants: {', '.join(verdicts[mid].master_name for mid in active_masters)}.",
        ]
        for mid in active_masters:
            v = verdicts[mid]
            parts.append(
                f"{v.master_name}: {v.conclusion} ({v.score:.1f}%) — "
                f"{len(v.expert_analyses)} expert(s), {len(v.evidence)} preuve(s)."
            )
        if contradictions:
            parts.append(
                f"{len(contradictions)} contradiction(s) non résolue(s) — "
                "revue humaine recommandée."
            )
        else:
            parts.append("Aucune contradiction résiduelle — décision validée.")
        return " ".join(parts)

    def _empty_consensus(self, weights: Dict[str, float]) -> WeightedConsensus:
        return WeightedConsensus(
            score=0.0,
            confidence_level="N/A",
            verdict_final="UNKNOWN",
            weights_used=weights,
            master_verdicts={},
            contradictions=[],
            contradictions_resolved=True,
            decision_justification="Aucun Master AI activé.",
        )
