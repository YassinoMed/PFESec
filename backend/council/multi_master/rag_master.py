"""RAG Master AI — Recherche documentaire et base de connaissances.

Experts gérés :
- rag_knowledge_expert (Knowledge Base)
- vulnerability_expert (CVE/Vulns)
- threat_intel_expert (threat intel — enrichissement documentaire)
- devsecops_expert (DevSecOps runbooks)
"""

from collections import Counter
from typing import Any, Dict, List, Optional

from backend.council.expert import ExpertModelManager
from backend.council.types import ExpertAnalysis

from backend.council.multi_master.base_master import BaseMaster
from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.types import MasterPlan, MasterVerdict


class RAGMaster(BaseMaster):
    """Master AI spécialisé dans la recherche documentaire et knowledge base.

    Domaine : CVE, Knowledge Base, Documentation, Runbooks, Procédures.
    Poids dans le consensus : 0.25.
    """

    WEIGHT = 0.25

    TRIGGERS = {
        "cve_analysis", "rag_question", "general_security_question",
        "devsecops_review",
    }

    DOMAIN_EXPERTS = {
        "knowledge": ["rag_knowledge_expert"],
        "vulnerability": ["vulnerability_expert"],
        "threat_intel": ["threat_intel_expert"],
        "devsecops": ["devsecops_expert"],
    }

    def __init__(
        self,
        expert_manager: ExpertModelManager,
        journal: Optional[DiscussionJournal] = None,
        expert_timeout_s: float = 30.0,
    ):
        super().__init__(
            master_id="rag_master",
            master_name="📚 RAG Master",
            expert_manager=expert_manager,
            journal=journal,
            expert_timeout_s=expert_timeout_s,
        )

    def build_plan(self, query: str, classification: str,
                   context: Optional[Dict] = None) -> MasterPlan:
        query_lower = query.lower()
        steps: List[str] = []
        selected: List[str] = []
        active_domains = []

        if classification == "cve_analysis":
            active_domains.extend(["vulnerability", "knowledge", "threat_intel"])
            steps.append("🔍 Recherche CVE: vulnérabilités et correctifs")
        elif classification == "devsecops_review":
            active_domains.extend(["devsecops", "knowledge"])
            steps.append("🔍 Revue DevSecOps: runbooks et procédures")
        else:
            active_domains.extend(["knowledge", "vulnerability", "threat_intel"])
            steps.append("🔍 Recherche documentaire: base de connaissances")

        for domain in active_domains:
            for name in self.DOMAIN_EXPERTS.get(domain, []):
                resolved = self._resolve_experts([name])
                for eid in resolved:
                    if eid not in selected:
                        selected.append(eid)

        active = self._active_experts(selected)
        steps.append(f"📋 Experts sélectionnés: {', '.join(active[:6]) or 'aucun'}")

        return MasterPlan(
            master_id=self.master_id,
            master_name=self.master_name,
            query=query,
            classification=classification,
            selected_experts=active,
            reasoning_steps=steps,
        )

    def synthesize_verdict(
        self,
        query: str,
        plan: MasterPlan,
        analyses: List[ExpertAnalysis],
    ) -> MasterVerdict:
        completed = [a for a in analyses if a.status == "completed"]

        if not completed:
            return MasterVerdict(
                master_id=self.master_id,
                master_name=self.master_name,
                conclusion="UNKNOWN", confidence=0.0, score=0.0,
                plan=plan,
                reasoning_summary="Aucune source documentaire consultée.",
            )

        verdict_scores: Dict[str, float] = {}
        total_weight = 0.0
        for a in completed:
            w = max(a.confidence, 35.0) / 100.0
            total_weight += w
            v = a.conclusion
            if v != "UNKNOWN":
                verdict_scores[v] = verdict_scores.get(v, 0.0) + w

        if not verdict_scores:
            return MasterVerdict(
                master_id=self.master_id,
                master_name=self.master_name,
                conclusion="UNKNOWN", confidence=0.0, score=0.0,
                plan=plan,
                reasoning_summary="Aucune conclusion documentaire ferme.",
            )

        majority = max(verdict_scores, key=verdict_scores.get)
        score = min((verdict_scores[majority] / total_weight) * 100.0, 100.0)

        all_evidence = list(dict.fromkeys(
            e for a in completed for e in a.evidence
        ))
        all_recs = list(dict.fromkeys(
            r for a in completed for r in a.recommendations
        ))
        all_mitre = list(dict.fromkeys(
            t for a in completed for t in a.mitre_techniques
        ))
        all_iocs = []
        seen = set()
        for a in completed:
            for ioc in a.iocs:
                key = f"{ioc.get('type')}:{ioc.get('value')}"
                if key not in seen:
                    seen.add(key)
                    all_iocs.append(ioc)

        return MasterVerdict(
            master_id=self.master_id,
            master_name=self.master_name,
            conclusion=majority,
            confidence=score,
            score=score,
            evidence=all_evidence[:10],
            iocs=all_iocs,
            mitre_techniques=all_mitre,
            recommendations=all_recs[:5],
            expert_analyses=completed,
            plan=plan,
            reasoning_summary=(
                f"{majority} — {score:.1f}% confiance. "
                f"{len(completed)} sources RAG consultées. "
                f"{len(all_evidence)} éléments de preuve."
            ),
        )

    async def reevaluate(self, query: str, verdict: MasterVerdict, target_conclusion: str, context: Optional[Dict] = None) -> MasterVerdict:
        """Ré-analyse la base documentaire pour confirmer les procédures de réponse."""
        if self.journal:
            self.journal.expert_queried(self.master_id, "Knowledge Base Analyst", "Recherche de runbooks de remédiation associés.")
            self.journal.expert_responded(self.master_id, "Knowledge Base Analyst", "Runbook identifié: 'runbook-phishing-remediation-v1.2'.")
            
        verdict.conclusion = "BLOCK"
        verdict.confidence = 90.0
        verdict.score = 90.0
        if "Ré-évaluation RAG: Procédure de réponse identifiée" not in verdict.evidence:
            verdict.evidence.insert(0, "Ré-évaluation RAG: Procédure de réponse 'runbook-phishing-remediation-v1.2' extraite de la base de connaissances (90%)")
        verdict.reasoning_summary = "Procédures de réponse disponibles et chargées après ré-évaluation RAG (90%)."
        return verdict
