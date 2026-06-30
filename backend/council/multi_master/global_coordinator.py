"""Global Coordinator AI — Point d'entrée de l'architecture Multi-Master.

Fonctionnement :
1. Reçoit la requête utilisateur
2. Classe la requête (via QueryClassifier)
3. Active les Masters AI pertinents en parallèle
4. Anime la discussion inter-Masters
5. Calcule le consensus pondéré
6. Produit le rapport final via le pipeline existant
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.agents.base import AgentContext
from backend.agents.query_classifier import QueryClassifierAgent
from backend.council.config import CouncilConfig
from backend.council.engines import (
    CouncilConsensusEngine,
    CrossValidationEngine,
    DebateEngine,
    DiscussionEngine,
    ExplainabilityEngine,
    LocalFactCheckEngine,
    MetricsCollector,
    ReflectionEngine,
    debate_needed,
    detect_contradictions,
)
from backend.council.expert import ExpertModelManager
from backend.council.evidence_fusion import EvidenceFusionEngine
from backend.council.orchestrator import MasterAIOrchestrator, _stage
from backend.council.reasoning_engine import ReasoningEngine
from backend.council.response_plan import ResponsePlanEngine
from backend.council.risk_assessment import RiskAssessmentEngine
from backend.council.types import CouncilMessage, CouncilResult

from backend.council.multi_master.discussion_engine import InterMasterDiscussionEngine
from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.rag_master import RAGMaster
from backend.council.multi_master.soc_master import SOCMaster
from backend.council.multi_master.threat_master import ThreatMaster
from backend.council.multi_master.governance_master import GovernanceMaster
from backend.council.multi_master.types import MultiMasterResult
from backend.council.multi_master.weighted_consensus import WeightedConsensusEngine


class GlobalCoordinator:
    """Global Coordinator — Orchestre l'architecture Multi-Master.

    Points clés :
    - Active UNIQUEMENT les Masters pertinents pour la classification
    - Parallélise l'analyse des Masters
    - Anime la discussion inter-Masters
    - Calcule le consensus pondéré
    - Produit le rapport final via le pipeline existant
    """

    # Mapping classification → Masters à activer
    CLASSIFICATION_TO_MASTERS: Dict[str, List[str]] = {
        "phishing_analysis": ["threat_master", "rag_master", "soc_master", "governance_master"],
        "email_analysis": ["threat_master", "rag_master", "soc_master", "governance_master"],
        "url_analysis": ["threat_master", "rag_master", "governance_master"],
        "ioc_analysis": ["threat_master", "soc_master", "governance_master"],
        "malware_analysis": ["threat_master", "soc_master", "rag_master", "governance_master"],
        "cve_analysis": ["threat_master", "rag_master", "soc_master", "governance_master"],
        "siem_investigation": ["soc_master", "rag_master", "governance_master"],
        "incident_active": ["soc_master", "threat_master", "rag_master", "governance_master"],
        "sigma_analysis": ["soc_master", "threat_master", "governance_master"],
        "incident_response": ["soc_master", "threat_master", "governance_master"],
        "log_analysis": ["soc_master", "rag_master", "governance_master"],
        "cloud_incident": ["soc_master", "threat_master", "rag_master", "governance_master"],
        "kubernetes_incident": ["soc_master", "threat_master", "governance_master"],
        "general_security_question": ["soc_master", "rag_master", "governance_master"],
        "devsecops_review": ["rag_master", "threat_master", "governance_master"],
        "threat_hunting": ["threat_master", "soc_master", "governance_master"],
        "rag_question": ["rag_master", "governance_master"],
        "HORS_DOMAINE": [],
        "ERREUR_INPUT": [],
    }

    # Poids des Masters dans le consensus
    MASTER_WEIGHTS: Dict[str, float] = {
        "threat_master": 0.40,
        "soc_master": 0.30,
        "rag_master": 0.20,
        "governance_master": 0.10,
    }

    def __init__(
        self,
        registry,
        config: Optional[CouncilConfig] = None,
        expert_manager: Optional[ExpertModelManager] = None,
        journal: Optional[DiscussionJournal] = None,
    ):
        self.registry = registry
        self.config = config or CouncilConfig.default()
        self.experts = expert_manager or ExpertModelManager(registry)
        self.experts.register_all_virtual_experts()

        # Orchestrateur existant (pour la compatibilité)
        self.legacy_orchestrator = MasterAIOrchestrator(registry, config, expert_manager)

        # Classifieur
        self.classifier = QueryClassifierAgent()

        # Journal de discussion temps réel
        self.journal = journal or DiscussionJournal()

        # Masters AI
        self.threat_master = ThreatMaster(
            self.experts, journal=self.journal,
            expert_timeout_s=self.config.expert_timeout_s,
        )
        self.soc_master = SOCMaster(
            self.experts, journal=self.journal,
            expert_timeout_s=self.config.expert_timeout_s,
        )
        self.rag_master = RAGMaster(
            self.experts, journal=self.journal,
            expert_timeout_s=self.config.expert_timeout_s,
        )
        self.governance_master = GovernanceMaster(
            self.experts, journal=self.journal,
            expert_timeout_s=self.config.expert_timeout_s,
        )

        # Moteurs
        self.discussion_engine = InterMasterDiscussionEngine(journal=self.journal)
        self.consensus_engine = WeightedConsensusEngine()
        self.council_consensus = CouncilConsensusEngine()
        self.reasoning_engine = ReasoningEngine()
        self.fusion_engine = EvidenceFusionEngine()
        self.risk_engine = RiskAssessmentEngine()
        self.response_engine = ResponsePlanEngine()
        self.explainability = ExplainabilityEngine()
        self.reflection = ReflectionEngine()
        self.metrics = MetricsCollector()
        self.fact_check = LocalFactCheckEngine()
        self.discussion = DiscussionEngine()
        self.debate = DebateEngine()
        self.cross_validation = CrossValidationEngine()

        # Registre des Masters
        self._masters = {
            "threat_master": self.threat_master,
            "soc_master": self.soc_master,
            "rag_master": self.rag_master,
            "governance_master": self.governance_master,
        }

    async def run(
        self,
        query: str,
        user_role: str = "analyst",
        context: Optional[Dict] = None,
        models: Optional[List[str]] = None,
    ) -> MultiMasterResult:
        """Point d'entrée principal de l'architecture Multi-Master."""
        started_at = time.time()
        session_id = str(uuid.uuid4())[:8]
        stage_times: Dict[str, float] = {}

        self.journal.coordinator_opened()

        # ── Étape 1: Classification ────────────────────────────────────────
        t = time.time()
        agent_ctx = AgentContext(query=query, user_role=user_role, metadata=context or {})
        classification_result = await self.classifier.run(agent_ctx)
        classification = classification_result.output.get("primary_category", "general_security_question")
        classification_confidence = classification_result.confidence
        stage_times["classification"] = (time.time() - t) * 1000

        self.journal._log("classification", "global_coordinator", None,
                          f"Requête classifiée: {classification} (confiance: {classification_confidence:.1%})",
                          icon="🔍")

        # ── Étape 2: Déterminer les Masters à activer ──────────────────────
        master_ids = self.CLASSIFICATION_TO_MASTERS.get(classification, [])

        if not master_ids:
            self.journal._log("coordinator", "global_coordinator", None,
                              f"Aucun Master activé pour '{classification}'. Utilisation du pipeline legacy.",
                              icon="⚠️")
            legacy_result = await self.legacy_orchestrator.run(query, user_role, context, models)
            return self._legacy_to_multimaster(legacy_result, session_id)

        activated_masters = [mid for mid in master_ids if mid in self._masters]
        self.journal.coordinator_opened(
            f"Masters activés: {', '.join(self._masters[mid].master_name for mid in activated_masters)}"
        )

        # ── Étape 3: Exécution parallèle des Masters ───────────────────────
        t = time.time()
        pipeline_context = dict(context or {})

        tasks = {}
        for mid in activated_masters:
            master = self._masters[mid]
            tasks[mid] = master.analyze(query, classification, pipeline_context)

        master_results = {}
        for mid, task in tasks.items():
            master_results[mid] = await task

        stage_times["master_analysis"] = (time.time() - t) * 1000

        # Collecter les verdicts
        verdicts = {}
        all_analyses = []
        for mid, result in master_results.items():
            verdicts[mid] = result.verdict
            all_analyses.extend(result.analyses)

        # ── Étape 4: Discussion inter-Masters ──────────────────────────────
        t = time.time()
        discussion_log, discussion_rounds, adjusted_verdicts = (
            await self.discussion_engine.conduct_discussion(
                verdicts, self.MASTER_WEIGHTS, self._masters, query
            )
        )
        stage_times["discussion"] = (time.time() - t) * 1000

        # ── Étape 5: Consensus pondéré ─────────────────────────────────────
        t = time.time()
        weighted_consensus = self.consensus_engine.compute(
            adjusted_verdicts, discussion_log, discussion_rounds, self.MASTER_WEIGHTS
        )
        stage_times["weighted_consensus"] = (time.time() - t) * 1000

        if self.journal:
            self.journal.consensus_reached(
                weighted_consensus.score,
                weighted_consensus.verdict_final,
                f"Poids: {weighted_consensus.weights_used}",
            )

        # ── Étape 6: Pipeline legacy pour le rapport final ─────────────────
        t = time.time()
        contradictions_list = []
        if all_analyses:
            contradictions_list = detect_contradictions(
                all_analyses, self.config.disagreement_threshold
            )

        fact_check = self.fact_check.check(query, all_analyses)

        consensus_dict = self._build_consensus_dict(weighted_consensus, all_analyses, contradictions_list)
        fusion = self.fusion_engine.fuse(query, all_analyses, fact_check)

        reasoning_artifacts = self.reasoning_engine.execute(
            query=query,
            classification=classification,
            classification_confidence=classification_confidence,
            selected_experts=list({a.expert_id for a in all_analyses}),
            analyses=all_analyses,
            contradictions=contradictions_list,
            cross_validations=[],
            fact_check=fact_check,
            consensus=consensus_dict,
        )

        final_response = self.explainability.build(query, all_analyses, consensus_dict, fact_check, contradictions_list)
        reflection = self.reflection.reflect(final_response, contradictions_list, fact_check)
        stage_times["final_report"] = (time.time() - t) * 1000

        # ── Étape 7: Assembler le résultat ─────────────────────────────────
        metrics = self.metrics.collect(started_at, stage_times, all_analyses)
        conversation = [CouncilMessage("Global Coordinator", None, "start",
                                        f"Session Multi-Master {session_id}.")]

        council_result = CouncilResult(
            query=query,
            classification=classification,
            selected_models=list({a.expert_id for a in all_analyses}),
            experts=all_analyses,
            conversation=conversation,
            contradictions=contradictions_list,
            cross_validations=[],
            fact_check=fact_check,
            consensus=consensus_dict,
            reflection=reflection,
            final_response=final_response,
            timeline=[_stage(f"master_{mid}", "completed", master_results[mid].elapsed_ms)
                      for mid in activated_masters],
            metrics=metrics,
            config=self.config.to_dict(),
            reasoning_trace=reasoning_artifacts.get("reasoning_trace"),
            attack_timeline=reasoning_artifacts.get("attack_timeline"),
            risk_assessment=reasoning_artifacts.get("risk_assessment"),
            response_plan=reasoning_artifacts.get("response_plan"),
            decision_journal=reasoning_artifacts.get("decision_journal"),
            evidence_fusion=reasoning_artifacts.get("evidence_fusion"),
        )

        # Rapport final
        report = self._generate_report(
            query, classification, weighted_consensus, council_result
        )
        if self.journal:
            self.journal.report_generated(report[:200])

        return MultiMasterResult(
            query=query,
            classification=classification,
            activated_masters=activated_masters,
            master_verdicts=verdicts,
            discussion_log=discussion_log,
            discussion_rounds=discussion_rounds,
            weighted_consensus=weighted_consensus,
            council_result=council_result,
            report=report,
            session_id=session_id,
        )

    def get_journal(self) -> DiscussionJournal:
        return self.journal

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_consensus_dict(
        self,
        weighted_consensus: 'WeightedConsensus',
        analyses: List,
        contradictions: List[Dict],
    ) -> Dict:
        from backend.council.engines import _agreement_points
        completed = [a for a in analyses if a.status == "completed"]
        return {
            "global_score": weighted_consensus.score,
            "confidence_level": weighted_consensus.confidence_level,
            "consensus_reached": weighted_consensus.score >= 50.0,
            "final_response": f"{weighted_consensus.verdict_final} (score: {weighted_consensus.score:.1f}%)",
            "verdict_final": weighted_consensus.verdict_final,
            "score_consensus": weighted_consensus.score,
            "ratio_accord": weighted_consensus.score / 100.0,
            "votes_detail": {mid: {"verdict": v.conclusion, "confiance": round(v.confidence, 2)}
                            for mid, v in weighted_consensus.master_verdicts.items()},
            "plancher_applique": False,
            "plancher_unanimite_applique": False,
            "valeur_plancher": 0.0,
            "anomalie_detectee": False,
            "score_brut": weighted_consensus.score,
            "poids_normalises": True,
            "confidence_boosted_ids": [],
            "total_models_executed": len(completed),
            "total_retained": len(completed),
            "total_rejected": len(analyses) - len(completed),
            "agreements": _agreement_points(analyses),
            "disagreements": contradictions,
            "false_positive_risk": "Low" if weighted_consensus.score >= 70 else "Medium",
            "consensus_metadata": {
                "ratio_accord": round(weighted_consensus.score / 100.0, 3),
                "nombre_agents": len(completed),
                "plancher_applique": False,
                "score_brut": weighted_consensus.score,
                "score_final": weighted_consensus.score,
                "unanimite": len(weighted_consensus.master_verdicts) > 0 and
                           len(set(v.conclusion for v in weighted_consensus.master_verdicts.values())) == 1,
                "anomalie_consensus": False,
            },
            "multi_master": {
                "activated": list(weighted_consensus.master_verdicts.keys()),
                "weights": weighted_consensus.weights_used,
                "discussion_rounds": len(weighted_consensus.contradictions),
            },
        }

    def _generate_report(
        self,
        query: str,
        classification: str,
        consensus: 'WeightedConsensus',
        council_result: CouncilResult,
    ) -> str:
        lines = []
        lines.append(f"RAPPORT DE SÉCURITÉ — Architecture Multi-Master AI")
        lines.append(f"{'=' * 60}")
        lines.append(f"Requête: {query[:150]}")
        lines.append(f"Classification: {classification}")
        lines.append(f"Décision finale: {consensus.verdict_final} (score: {consensus.score:.1f}%)")
        lines.append(f"Confiance: {consensus.confidence_level}")
        lines.append("")

        lines.append(f"Masters participants:")
        for mid, v in consensus.master_verdicts.items():
            lines.append(f"  {v.master_name}: {v.conclusion} ({v.score:.1f}%)")
            for e in v.evidence[:3]:
                lines.append(f"    • {e}")
        lines.append("")

        if consensus.contradictions:
            lines.append(f"Contradictions non résolues: {len(consensus.contradictions)}")
            for c in consensus.contradictions:
                lines.append(f"  • {c['left']} ({c['left_conclusion']}) vs {c['right']} ({c['right_conclusion']})")
        else:
            lines.append("Aucune contradiction — décision validée")

        lines.append("")
        if council_result and council_result.response_plan:
            lines.append("Plan de réponse:")
            plans = council_result.response_plan
            for a in plans.containment[:3]:
                lines.append(f"  [Confinement] {a.action}: {a.description}")
            for a in plans.eradication[:2]:
                lines.append(f"  [Éradication] {a.action}: {a.description}")

        return "\n".join(lines)

    def _legacy_to_multimaster(self, result: CouncilResult, session_id: str) -> MultiMasterResult:
        return MultiMasterResult(
            query=result.query,
            classification=result.classification,
            activated_masters=[],
            session_id=session_id,
            council_result=result,
            discussion_log=[],
            discussion_rounds=0,
            report=result.final_response.get("answer", ""),
        )
