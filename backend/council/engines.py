import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List

from backend.consensus.config import ConsensusConfig
from backend.consensus.engine import ConsensusEngine, ModelVote
from backend.council.config import CouncilConfig
from backend.council.expert import ExpertModelManager
from backend.council.types import CouncilMessage, CrossValidation, ExpertAnalysis, FactCheckResult


class DiscussionEngine:
    QUESTIONS = [
        "Pourquoi es-tu arrive a cette conclusion ?",
        "Quelle est la preuve la plus importante ?",
        "Quelle est la principale faiblesse de ton analyse ?",
        "Existe-t-il une autre hypothese plausible ?",
    ]

    async def interview(self, manager: ExpertModelManager, analyses: List[ExpertAnalysis]) -> List[CouncilMessage]:
        messages = []
        for analysis in analyses:
            if analysis.status != "completed":
                continue
            expert = manager.get_expert(analysis.expert_id)
            if not expert:
                continue
            for question in self.QUESTIONS:
                messages.append(CouncilMessage("Master AI", analysis.expert_id, "discussion", question))
                answer = await expert.answer(question, analysis)
                messages.append(CouncilMessage(analysis.expert_name, "Master AI", "discussion", answer))
        return messages


class DebateEngine:
    async def debate(self, manager: ExpertModelManager, analyses: List[ExpertAnalysis], contradictions: List[Dict], max_rounds: int) -> List[CouncilMessage]:
        messages = []
        if not contradictions:
            return messages
        for round_id in range(max_rounds):
            for contradiction in contradictions:
                left = _find_analysis(analyses, contradiction["left"])
                right = _find_analysis(analyses, contradiction["right"])
                if not left or not right:
                    continue
                for current, peer in ((left, right), (right, left)):
                    expert = manager.get_expert(current.expert_id)
                    if not expert:
                        continue
                    question = (
                        f"Tour {round_id + 1}: peux-tu expliquer pourquoi ton resultat "
                        f"differe de {peer.expert_name} ({peer.conclusion}) ?"
                    )
                    messages.append(CouncilMessage("Master AI", current.expert_id, "debate", question))
                    answer = await expert.answer(question, current, peer)
                    messages.append(CouncilMessage(current.expert_name, "Master AI", "debate", answer))
        return messages


class CrossValidationEngine:
    async def validate(self, manager: ExpertModelManager, analyses: List[ExpertAnalysis]) -> List[CrossValidation]:
        validations = []
        completed = [a for a in analyses if a.status == "completed"]
        for reviewer in completed:
            expert = manager.get_expert(reviewer.expert_id)
            if not expert:
                continue
            for reviewed in completed:
                if reviewer.expert_id == reviewed.expert_id:
                    continue
                outcome = await expert.validate(reviewed, reviewer)
                validations.append(CrossValidation(reviewer.expert_id, reviewed.expert_id, outcome["status"], outcome["notes"]))
        return validations


class LocalFactCheckEngine:
    def __init__(self, knowledge_dir: str = "backend/rag_agent/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.entries = self._load_entries()

    def check(self, query: str, analyses: List[ExpertAnalysis]) -> FactCheckResult:
        corpus = " ".join([query] + [str(a.response or "") for a in analyses]).lower()
        matches = []
        for entry in self.entries:
            score = _keyword_overlap(corpus, entry["text"].lower())
            if score > 0:
                matches.append({**entry, "score": score})
        matches.sort(key=lambda item: item["score"], reverse=True)

        verified = []
        references = []
        for item in matches[:6]:
            references.append({"source": item["source"], "text": item["text"], "score": round(item["score"], 3)})
            verified.append({"claim": item["text"], "source": item["source"]})

        hypotheses = []
        for analysis in analyses:
            if analysis.conclusion != "UNKNOWN" and analysis.confidence < 80:
                hypotheses.append(f"{analysis.expert_name}: {analysis.conclusion} avec confiance limitee ({analysis.confidence:.1f}%).")

        unconfirmed = []
        if not references:
            unconfirmed.append("Aucune reference RAG locale ne correspond directement aux affirmations principales.")

        return FactCheckResult(verified_facts=verified, hypotheses=hypotheses, unconfirmed=unconfirmed, references=references)

    def _load_entries(self) -> List[Dict]:
        entries = []
        if not self.knowledge_dir.exists():
            return entries
        for path in self.knowledge_dir.glob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and item.get("text"):
                        entries.append({"source": path.stem, "text": item["text"], "metadata": item})
        return entries


class CouncilConsensusEngine:
    def __init__(self):
        self.engine = ConsensusEngine(ConsensusConfig.default())

    def compute(self, query: str, analyses: List[ExpertAnalysis], contradictions: List[Dict], fact_check = None) -> Dict:
        completed_analyses = [a for a in analyses if a.status == "completed"]

        n = len(completed_analyses)
        if n == 0:
            return _empty_consensus()

        # ── Bloc 2 — Confiance minimale 0.35 ───────────────────────────────
        boosted = {}
        for a in completed_analyses:
            if a.confidence < 35.0 and a.conclusion != "UNKNOWN":
                boosted[a.expert_id] = True

        # ── Bloc 1 — Poids normalisés à somme 1.0 ──────────────────────────
        raw_weights = {a.expert_id: 1.0 / n for a in completed_analyses}
        total_weight = sum(raw_weights.values())
        if abs(total_weight - 1.0) > 0.001:
            weights = {eid: w / total_weight for eid, w in raw_weights.items()}
            poids_normalises = True
        else:
            weights = raw_weights
            poids_normalises = False

        # ── Bloc 2 — Score pondéré par verdict ─────────────────────────────
        verdict_scores: Dict[str, float] = {}
        for a in completed_analyses:
            v = a.conclusion
            if v == "UNKNOWN":
                continue
            effective_conf = max(a.confidence, 35.0) if a.expert_id in boosted else a.confidence
            w = weights.get(a.expert_id, 0.0)
            verdict_scores[v] = verdict_scores.get(v, 0.0) + (effective_conf / 100.0) * w

        active_weight_sum = sum(weights.get(a.expert_id, 0.0) for a in completed_analyses if a.conclusion != "UNKNOWN")
        if active_weight_sum > 0:
            for v in verdict_scores:
                verdict_scores[v] /= active_weight_sum
        for v in verdict_scores:
            verdict_scores[v] = round(verdict_scores[v] * 100.0, 2)

        # ── Comptage des verdicts ───────────────────────────────────────────
        verdict_counts: Dict[str, int] = {}
        for a in completed_analyses:
            v = a.conclusion
            if v == "UNKNOWN":
                continue
            verdict_counts[v] = verdict_counts.get(v, 0) + 1

        if not verdict_counts:
            return _all_unknown_result(completed_analyses, analyses, contradictions)

        n_agents_that_voted = sum(verdict_counts.values())
        majority_verdict = max(verdict_counts, key=verdict_counts.get)
        n_accord = verdict_counts[majority_verdict]
        ratio_accord = n_accord / n_agents_that_voted if n_agents_that_voted > 0 else 0.0
        unanimite = ratio_accord == 1.0

        base_score = verdict_scores.get(majority_verdict, 0.0)

        # ── Bonus d'unanimité Bloc 2: +15 points ───────────────────────────
        score_brut = base_score
        if unanimite:
            base_score += 15.0

        # ── Bloc 1 — Règles de plancher renforcées ─────────────────────────
        plancher_applique = False
        plancher_unanimite_applique = False
        valeur_plancher = 0.0

        if unanimite:
            plancher = 78.0
            if base_score < plancher:
                base_score = plancher
                plancher_applique = True
                plancher_unanimite_applique = True
                valeur_plancher = plancher
        elif ratio_accord >= 0.90:
            plancher = 75.0
            if base_score < plancher:
                base_score = plancher
                plancher_applique = True
                valeur_plancher = plancher
        elif ratio_accord >= 0.75:
            plancher = 60.0
            if base_score < plancher:
                base_score = plancher
                plancher_applique = True
                valeur_plancher = plancher
        elif ratio_accord >= 0.60:
            plancher = 45.0
            if base_score < plancher:
                base_score = plancher
                plancher_applique = True
                valeur_plancher = plancher

        # ── Plafonnement ────────────────────────────────────────────────────
        adjusted_score = min(max(base_score, 0.0), 95.0 if unanimite else 100.0)

        anomalie_detectee = ratio_accord >= 0.90 and score_brut < 65.0 and not plancher_applique

        if anomalie_detectee:
            import logging
            logging.getLogger("council.consensus").warning(
                f"ANOMALIE_CONSENSUS: ratio={ratio_accord:.3f} score_calcule={score_brut:.2f}"
            )

        # ── Résultat ────────────────────────────────────────────────────────
        votes_detail = {}
        for a in completed_analyses:
            entry = {"verdict": a.conclusion, "confiance": round(a.confidence, 2)}
            if a.expert_id in boosted:
                entry["confidence_boosted"] = True
            votes_detail[a.expert_id] = entry

        result = {
            "global_score": round(adjusted_score, 2),
            "confidence_level": "High" if adjusted_score >= 80.0 else "Medium" if adjusted_score >= 50.0 else "Low",
            "consensus_reached": adjusted_score >= 70.0,
            "final_response": f"{majority_verdict} (score: {adjusted_score:.1f}%)",
            "verdict_final": majority_verdict,
            "score_consensus": round(adjusted_score, 2),
            "ratio_accord": round(ratio_accord, 3),
            "votes_detail": votes_detail,
            "plancher_applique": plancher_applique,
            "plancher_unanimite_applique": plancher_unanimite_applique,
            "valeur_plancher": valeur_plancher,
            "anomalie_detectee": anomalie_detectee,
            "score_brut": round(score_brut, 2),
            "poids_normalises": poids_normalises,
            "confidence_boosted_ids": list(boosted.keys()),
            "total_models_executed": len(completed_analyses),
            "total_retained": len(completed_analyses),
            "total_rejected": len(analyses) - len(completed_analyses),
            "agreements": _agreement_points(analyses),
            "disagreements": contradictions,
            "false_positive_risk": "Low",
            # Bloc 3 — Métadonnées consensus pour le Decision Journal
            "consensus_metadata": {
                "ratio_accord": round(ratio_accord, 3),
                "nombre_agents": n_agents_that_voted,
                "plancher_applique": plancher_applique,
                "score_brut": round(score_brut, 2),
                "score_final": round(adjusted_score, 2),
                "unanimite": unanimite,
                "anomalie_consensus": anomalie_detectee,
            },
        }

        return result


class ReflectionEngine:
    def reflect(self, final_response: Dict, contradictions: List[Dict], fact_check: FactCheckResult) -> Dict:
        issues = []
        if contradictions:
            issues.append("contradictions_present")
        if fact_check.unconfirmed:
            issues.append("unconfirmed_claims_present")
        if not final_response.get("references_rag"):
            issues.append("no_rag_reference")
        return {
            "passed": len(issues) == 0 or issues == ["contradictions_present"],
            "issues": issues,
            "action": "relancer_discussion" if "unconfirmed_claims_present" in issues and contradictions else "accept",
        }


class ExplainabilityEngine:
    def build(self, query: str, analyses: List[ExpertAnalysis], consensus: Dict, fact_check: FactCheckResult, contradictions: List[Dict]) -> Dict:
        primary = consensus.get("primary_model") or {}
        conclusion = _majority_conclusion(analyses)
        evidence = []
        for analysis in analyses:
            evidence.extend(analysis.evidence)
        evidence = list(dict.fromkeys(evidence))[:8]
        return {
            "conclusion": conclusion,
            "answer": _build_answer_text(query, conclusion, consensus, evidence, contradictions, fact_check),
            "global_confidence": consensus.get("global_score", 0.0),
            "confidence_level": consensus.get("confidence_level", "Low"),
            "participants": [a.expert_id for a in analyses],
            "primary_model": primary.get("model_name") or primary.get("model_id"),
            "main_evidence": evidence,
            "references_rag": fact_check.references,
            "decision_reasons": [
                f"Consensus score: {consensus.get('global_score', 0.0):.1f}%",
                f"Experts retenus: {consensus.get('total_retained', 0)}/{consensus.get('total_models_executed', 0)}",
                f"Conclusion majoritaire: {conclusion}",
            ],
            "divergences": contradictions,
        }


class MetricsCollector:
    def collect(self, started_at: float, stage_times: Dict[str, float], analyses: List[ExpertAnalysis]) -> Dict:
        return {
            "total_execution_ms": round((time.time() - started_at) * 1000, 2),
            "stage_times_ms": {k: round(v, 2) for k, v in stage_times.items()},
            "experts_total": len(analyses),
            "experts_completed": sum(1 for a in analyses if a.status == "completed"),
            "experts_failed": sum(1 for a in analyses if a.status in ("error", "timeout")),
        }


def detect_contradictions(analyses: List[ExpertAnalysis], disagreement_threshold: float) -> List[Dict]:
    contradictions = []
    completed = [a for a in analyses if a.status == "completed" and a.conclusion != "UNKNOWN"]
    for i, left in enumerate(completed):
        for right in completed[i + 1:]:
            if left.conclusion != right.conclusion:
                confidence_gap = abs(left.confidence - right.confidence) / 100.0
                significance = (left.confidence + right.confidence) / 200.0
                if significance >= disagreement_threshold or confidence_gap >= disagreement_threshold:
                    contradictions.append({
                        "left": left.expert_id,
                        "right": right.expert_id,
                        "left_conclusion": left.conclusion,
                        "right_conclusion": right.conclusion,
                        "significance": round(significance, 3),
                    })
    return contradictions


def debate_needed(analyses: List[ExpertAnalysis], contradictions: List[Dict], min_confidence: float) -> bool:
    if contradictions:
        return True
    completed = [a for a in analyses if a.status == "completed"]
    return bool(completed) and max(a.confidence for a in completed) < min_confidence


def _find_analysis(analyses: List[ExpertAnalysis], expert_id: str) -> ExpertAnalysis:
    return next((a for a in analyses if a.expert_id == expert_id), None)


def _keyword_overlap(left: str, right: str) -> float:
    left_words = set(re.findall(r"[a-z0-9_-]{4,}", left))
    right_words = set(re.findall(r"[a-z0-9_-]{4,}", right))
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / len(right_words)


def _agreement_points(analyses: List[ExpertAnalysis]) -> List[Dict]:
    counts = Counter(a.conclusion for a in analyses if a.status == "completed")
    return [{"conclusion": key, "count": value} for key, value in counts.most_common()]


def _all_unknown_result(completed_analyses, analyses, contradictions) -> Dict:
    return {
        "global_score": 0.0,
        "confidence_level": "Low",
        "consensus_reached": False,
        "final_response": "UNKNOWN (aucun verdict majoritaire)",
        "verdict_final": "UNKNOWN",
        "score_consensus": 0.0,
        "ratio_accord": 0.0,
        "votes_detail": {a.expert_id: {"verdict": a.conclusion, "confiance": round(a.confidence, 2)} for a in completed_analyses},
        "plancher_applique": False,
        "plancher_unanimite_applique": False,
        "valeur_plancher": 0.0,
        "anomalie_detectee": False,
        "score_brut": 0.0,
        "poids_normalises": False,
        "confidence_boosted_ids": [],
        "total_models_executed": len(completed_analyses),
        "total_retained": len(completed_analyses),
        "total_rejected": len(analyses) - len(completed_analyses),
        "agreements": _agreement_points(analyses),
        "disagreements": contradictions,
        "false_positive_risk": "Low",
        "consensus_metadata": {
            "ratio_accord": 0.0,
            "nombre_agents": 0,
            "plancher_applique": False,
            "score_brut": 0.0,
            "score_final": 0.0,
            "unanimite": False,
            "anomalie_consensus": False,
        },
    }


def _empty_consensus() -> Dict:
    return {
        "global_score": 0.0,
        "confidence_level": "N/A",
        "consensus_reached": False,
        "final_response": "Aucun expert disponible",
        "verdict_final": "UNKNOWN",
        "score_consensus": 0.0,
        "ratio_accord": 0.0,
        "votes_detail": {},
        "plancher_applique": False,
        "plancher_unanimite_applique": False,
        "valeur_plancher": 0.0,
        "anomalie_detectee": False,
        "score_brut": 0.0,
        "poids_normalises": False,
        "confidence_boosted_ids": [],
        "total_models_executed": 0,
        "total_retained": 0,
        "total_rejected": 0,
        "agreements": [],
        "disagreements": [],
        "false_positive_risk": "N/A",
        "consensus_metadata": {
            "ratio_accord": 0.0,
            "nombre_agents": 0,
            "plancher_applique": False,
            "score_brut": 0.0,
            "score_final": 0.0,
            "unanimite": False,
            "anomalie_consensus": False,
        },
    }


def _majority_conclusion(analyses: List[ExpertAnalysis]) -> str:
    weighted = Counter()
    for analysis in analyses:
        if analysis.status == "completed":
            weighted[analysis.conclusion] += analysis.confidence
    return weighted.most_common(1)[0][0] if weighted else "UNKNOWN"


def _build_answer_text(query: str, conclusion: str, consensus: Dict, evidence: List[str], contradictions: List[Dict], fact_check: FactCheckResult) -> str:
    refs = [r["source"] for r in fact_check.references[:3]]
    parts = [
        f"Conclusion du Security Council: {conclusion}.",
        f"Score de confiance global: {consensus.get('global_score', 0.0):.1f}% ({consensus.get('confidence_level', 'Low')}).",
    ]
    if evidence:
        parts.append("Preuves principales: " + ", ".join(evidence[:5]) + ".")
    if refs:
        parts.append("References RAG utilisees: " + ", ".join(dict.fromkeys(refs)) + ".")
    if contradictions:
        parts.append(f"Divergences detectees: {len(contradictions)} contradiction(s), traitees pendant le debat.")
    return " ".join(parts)
