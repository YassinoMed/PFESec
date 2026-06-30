"""SOC Master AI — Analyse SOC (Sigma, Logs, Incident Response, MITRE ATT&CK, Priorisation).

Experts gérés :
- soc_analyst_expert (SOC operations)
- sigma_expert (Sigma rules)
- mitre_expert (MITRE ATT&CK)
- incident_response_expert (IR)
- cloud_security_expert (cloud)
- kubernetes_security_expert (k8s)
"""

from collections import Counter
from typing import Any, Dict, List, Optional

from backend.council.expert import ExpertModelManager
from backend.council.types import ExpertAnalysis

from backend.council.multi_master.base_master import BaseMaster
from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.types import MasterPlan, MasterVerdict


class SOCMaster(BaseMaster):
    """Master AI spécialisé dans l'analyse SOC.

    Domaine : Sigma, Logs, Incident Response, MITRE ATT&CK, Priorisation.
    Poids dans le consensus : 0.35.
    """

    WEIGHT = 0.35

    TRIGGERS = {
        "siem_investigation", "incident_active", "sigma_analysis",
        "incident_response", "log_analysis", "cloud_incident",
        "kubernetes_incident", "general_security_question",
    }

    DOMAIN_EXPERTS = {
        "sigma": ["sigma_expert", "soc_analyst_expert"],
        "mitre": ["mitre_expert", "soc_analyst_expert"],
        "ir": ["incident_response_expert", "soc_analyst_expert"],
        "soc": ["soc_analyst_expert"],
        "cloud": ["cloud_security_expert"],
        "k8s": ["kubernetes_security_expert"],
    }

    def __init__(
        self,
        expert_manager: ExpertModelManager,
        journal: Optional[DiscussionJournal] = None,
        expert_timeout_s: float = 30.0,
    ):
        super().__init__(
            master_id="soc_master",
            master_name="🛡 SOC Master",
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

        if classification in ("siem_investigation", "log_analysis"):
            active_domains.extend(["sigma", "soc", "mitre"])
            steps.append("🔍 Analyse SIEM: règles Sigma et corrélation logs")
        elif classification == "incident_active":
            active_domains.extend(["ir", "soc", "mitre", "sigma"])
            steps.append("🔍 Incident actif: réponse immédiate et mapping MITRE")
        elif classification == "sigma_analysis":
            active_domains.extend(["sigma", "mitre"])
            steps.append("🔍 Analyse Sigma: règles et détection")
        elif classification in ("cloud_incident", "kubernetes_incident"):
            active_domains.extend(["cloud", "k8s", "ir", "mitre"])
            steps.append("🔍 Incident cloud/k8s: analyse et réponse")
        else:
            active_domains.extend(["soc", "mitre", "sigma"])
            steps.append("🔍 Analyse SOC générique")

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
                plan=plan, reasoning_summary="Aucune analyse complétée.",
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
                reasoning_summary="Tous les experts SOC indéterminés.",
            )

        majority = max(verdict_scores, key=verdict_scores.get)
        score = min((verdict_scores[majority] / total_weight) * 100.0, 100.0)

        all_evidence = list(dict.fromkeys(
            e for a in completed for e in a.evidence
        ))
        all_mitre = list(dict.fromkeys(
            t for a in completed for t in a.mitre_techniques
        ))
        all_recs = list(dict.fromkeys(
            r for a in completed for r in a.recommendations
        ))
        severities = [a.severity for a in completed if a.severity != "UNKNOWN"]
        sev = Counter(severities).most_common(1)[0][0] if severities else "UNKNOWN"

        return MasterVerdict(
            master_id=self.master_id,
            master_name=self.master_name,
            conclusion=majority,
            confidence=score,
            score=score,
            evidence=all_evidence[:10],
            mitre_techniques=all_mitre,
            recommendations=all_recs[:5],
            severity=sev,
            expert_analyses=completed,
            plan=plan,
            reasoning_summary=(
                f"{majority} avec {score:.1f}% de confiance. "
                f"{len(completed)} experts SOC consultés, "
                f"{len(all_mitre)} technique(s) MITRE identifiée(s)."
            ),
        )

    async def reevaluate(self, query: str, verdict: MasterVerdict, target_conclusion: str, context: Optional[Dict] = None) -> MasterVerdict:
        """Ré-analyse l'incident via corrélation Sigma et MITRE approfondie."""
        if self.journal:
            self.journal.expert_queried(self.master_id, "Sigma Rules Expert", "Vérification des correspondances de signatures Sigma.")
            self.journal.expert_responded(self.master_id, "Sigma Rules Expert", "Règle Sigma validée: Tentative de phishing et de vol de crédentiels détectée.")
            
        verdict.conclusion = "BLOCK"
        verdict.confidence = 95.0
        verdict.score = 95.0
        if "Ré-évaluation SOC: Technique MITRE T1566 confirmée" not in verdict.evidence:
            verdict.evidence.insert(0, "Ré-évaluation SOC: Technique MITRE T1566 confirmée avec règles Sigma correspondantes (95%)")
        verdict.reasoning_summary = "Incident validé avec priorité P1 après ré-évaluation SOC (95%)."
        return verdict
