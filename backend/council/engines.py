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

    def compute(self, query: str, analyses: List[ExpertAnalysis], contradictions: List[Dict]) -> Dict:
        votes = [
            ModelVote(
                model_id=a.expert_id,
                model_name=a.expert_name,
                category=a.category,
                confidence=a.confidence,
                weight=1,
                response=a.conclusion if a.conclusion != "UNKNOWN" else a.response,
                inference_ms=a.inference_ms,
                error=a.error if a.status not in ("completed",) else None,
            )
            for a in analyses
        ]
        result = self.engine.compute(query, votes).to_dict()
        result["agreements"] = _agreement_points(analyses)
        result["disagreements"] = contradictions
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
