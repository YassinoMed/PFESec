"""Evidence Fusion Engine — Aggregates and deduplicates multi-source expert analyses.

Fuses results from GPU models, virtual experts, and RAG sources into a unified
structured security report. Produces weighted aggregations and unified IOC lists.
"""

from collections import Counter
from typing import Dict, List, Optional

from backend.council.types import ExpertAnalysis, FactCheckResult


class EvidenceFusionEngine:
    """
    Fuses evidence from multiple expert analyses into a unified report.
    Handles deduplication, weighting, and confidence-based aggregation.
    """

    def fuse(
        self,
        query: str,
        analyses: List[ExpertAnalysis],
        fact_check: FactCheckResult,
    ) -> Dict:
        completed = [a for a in analyses if a.status == "completed"]

        # Evidence aggregation
        all_evidence = self._aggregate_evidence(completed)
        all_iocs = self._aggregate_iocs(completed)
        all_mitre = self._aggregate_mitre(completed)
        all_recs = self._aggregate_recommendations(completed)

        # Agreement analysis
        conclusions = [a.conclusion for a in completed if a.conclusion != "UNKNOWN"]
        conclusion_counter = Counter(conclusions)
        dominant_conclusion = conclusion_counter.most_common(1)[0][0] if conclusions else "UNKNOWN"
        agreement_rate = (conclusion_counter.most_common(1)[0][1] / len(conclusions)) * 100 if conclusions else 0.0

        # Confidence aggregation (weighted by evidence count)
        weighted_confidence = self._weighted_confidence(completed)

        # Sources diversity
        categories = list({a.category for a in completed})
        gpu_models = [a.expert_id for a in completed if a.category in ("bert", "llm", "phishing", "lora")]
        virtual_experts = [a.expert_id for a in completed if a.category not in ("bert", "llm", "phishing", "lora")]
        rag_refs = [r["source"] for r in fact_check.references]

        # Severity aggregation
        severities = [a.severity for a in completed if a.severity != "UNKNOWN"]
        dominant_severity = Counter(severities).most_common(1)[0][0] if severities else "UNKNOWN"

        return {
            "total_sources": len(analyses),
            "sources_completed": len(completed),
            "sources_failed": len(analyses) - len(completed),
            "dominant_conclusion": dominant_conclusion,
            "agreement_rate": round(agreement_rate, 2),
            "weighted_confidence": round(weighted_confidence, 2),
            "dominant_severity": dominant_severity,
            "categories_consulted": categories,
            "gpu_models_used": gpu_models,
            "virtual_experts_used": virtual_experts,
            "rag_sources_used": rag_refs,
            "unified_evidence": all_evidence,
            "unified_iocs": all_iocs,
            "unified_mitre_techniques": all_mitre,
            "unified_recommendations": all_recs,
            "fact_check_verified": len(fact_check.verified_facts),
            "fact_check_unconfirmed": len(fact_check.unconfirmed),
            "information_richness": self._compute_richness(
                all_evidence, all_iocs, all_mitre, rag_refs
            ),
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _aggregate_evidence(self, completed: List[ExpertAnalysis]) -> List[str]:
        seen = set()
        result = []
        for a in completed:
            for e in a.evidence:
                key = e.lower().strip()
                if key not in seen:
                    seen.add(key)
                    result.append(e)
        return result[:15]

    def _aggregate_iocs(self, completed: List[ExpertAnalysis]) -> List[Dict]:
        seen = set()
        result = []
        for a in completed:
            for ioc in a.iocs:
                key = f"{ioc.get('type', '')}:{ioc.get('value', '')}"
                if key not in seen:
                    seen.add(key)
                    result.append(ioc)
        return result[:20]

    def _aggregate_mitre(self, completed: List[ExpertAnalysis]) -> List[str]:
        seen = set()
        result = []
        for a in completed:
            for t in a.mitre_techniques:
                if t not in seen:
                    seen.add(t)
                    result.append(t)
        return result[:12]

    def _aggregate_recommendations(self, completed: List[ExpertAnalysis]) -> List[str]:
        seen = set()
        result = []
        for a in sorted(completed, key=lambda x: x.confidence, reverse=True):
            for r in a.recommendations:
                key = r.lower().strip()
                if key not in seen:
                    seen.add(key)
                    result.append(r)
        return result[:10]

    def _weighted_confidence(self, completed: List[ExpertAnalysis]) -> float:
        if not completed:
            return 0.0
        total_weight = 0.0
        total_score = 0.0
        for a in completed:
            # Weight by evidence richness
            weight = 1.0 + min(len(a.evidence) * 0.1, 0.5)
            total_weight += weight
            total_score += a.confidence * weight
        return total_score / total_weight if total_weight else 0.0

    def _compute_richness(
        self,
        evidence: List,
        iocs: List,
        mitre: List,
        rag_refs: List,
    ) -> str:
        score = len(evidence) * 1 + len(iocs) * 2 + len(mitre) * 2 + len(rag_refs) * 3
        if score >= 30:
            return "Rich — High-confidence analysis with multiple corroborating sources"
        if score >= 15:
            return "Moderate — Good evidence base with some corroboration"
        if score >= 5:
            return "Limited — Some evidence available, increased uncertainty"
        return "Sparse — Minimal evidence; results should be treated as preliminary"
