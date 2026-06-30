"""Master AI Reasoning Engine — Structured 9-step reasoning pipeline.

Orchestrates: comprehension → planning → evidence collection → cross-validation →
attack reconstruction → risk assessment → decision → response plan → final verification.

Never exposes raw model chain-of-thought. Produces a structured DecisionJournal.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from backend.council.attack_timeline import AttackTimelineBuilder
from backend.council.evidence_fusion import EvidenceFusionEngine
from backend.council.response_plan import ResponsePlanEngine
from backend.council.risk_assessment import RiskAssessmentEngine
from backend.council.types import (
    AttackTimeline,
    DecisionJournal,
    ExpertAnalysis,
    FactCheckResult,
    ReasoningStep,
    ReasoningTrace,
    ResponsePlan,
    RiskAssessment,
)


class ReasoningEngine:
    """
    Master AI Reasoning Engine — 9-step structured reasoning.

    Step 1: Query Comprehension
    Step 2: Expert Planning
    Step 3: Evidence Collection (parallel expert execution — done by orchestrator)
    Step 4: Cross-validation & Contradiction Detection
    Step 5: Attack Reconstruction (MITRE mapping)
    Step 6: Risk Assessment
    Step 7: Consensus Decision
    Step 8: Response Plan Generation
    Step 9: Final Verification & Reflection
    """

    def __init__(self):
        self.attack_builder = AttackTimelineBuilder()
        self.risk_engine = RiskAssessmentEngine()
        self.fusion_engine = EvidenceFusionEngine()
        self.response_engine = ResponsePlanEngine()

    def execute(
        self,
        query: str,
        classification: str,
        classification_confidence: float,
        selected_experts: List[str],
        analyses: List[ExpertAnalysis],
        contradictions: List[Dict],
        cross_validations: List[Any],
        fact_check: FactCheckResult,
        consensus: Dict,
    ) -> Dict:
        """
        Execute the full reasoning pipeline and return all v2 artifacts.

        Returns a dict with keys:
        - reasoning_trace: ReasoningTrace
        - attack_timeline: AttackTimeline
        - risk_assessment: RiskAssessment
        - response_plan: ResponsePlan
        - decision_journal: DecisionJournal
        - evidence_fusion: Dict
        """
        session_id = str(uuid.uuid4())[:8]
        steps: List[ReasoningStep] = []
        global_t0 = time.time()

        # ── Step 1 — Query Comprehension ─────────────────────────────────
        t = time.time()
        comprehension_findings = self._step_comprehension(query, classification, classification_confidence)
        steps.append(ReasoningStep(
            step=1, name="Query Comprehension",
            description="Analyse et classification de la requête entrante",
            findings=comprehension_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 2 — Expert Planning ──────────────────────────────────────
        t = time.time()
        planning_findings = self._step_planning(selected_experts, classification)
        steps.append(ReasoningStep(
            step=2, name="Expert Planning",
            description="Sélection des experts et définition de la stratégie d'analyse",
            findings=planning_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 3 — Evidence Collection (already done in parallel) ───────
        t = time.time()
        evidence_findings = self._step_evidence_collection(analyses)
        steps.append(ReasoningStep(
            step=3, name="Evidence Collection",
            description="Collecte parallèle des analyses de tous les experts activés",
            findings=evidence_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 4 — Cross-validation & Contradictions ────────────────────
        t = time.time()
        validation_findings = self._step_cross_validation(analyses, contradictions, cross_validations)
        steps.append(ReasoningStep(
            step=4, name="Cross-validation",
            description="Validation croisée des conclusions entre experts et détection des contradictions",
            findings=validation_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 5 — Evidence Fusion ──────────────────────────────────────
        t = time.time()
        fusion = self.fusion_engine.fuse(query, analyses, fact_check)
        fusion_findings = self._step_fusion_summary(fusion)
        steps.append(ReasoningStep(
            step=5, name="Evidence Fusion",
            description="Fusion et déduplication des preuves multi-sources",
            findings=fusion_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 6 — Attack Reconstruction ───────────────────────────────
        t = time.time()
        attack_timeline = self.attack_builder.build(
            query=query,
            classification=classification,
            analyses=analyses,
            fact_check_refs=fact_check.references,
        )
        attack_findings = self._step_attack_reconstruction(attack_timeline)
        steps.append(ReasoningStep(
            step=6, name="Attack Reconstruction",
            description="Reconstruction de la chronologie d'attaque et mapping MITRE ATT&CK",
            findings=attack_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 7 — Risk Assessment ──────────────────────────────────────
        t = time.time()
        risk = self.risk_engine.assess(
            query=query,
            classification=classification,
            analyses=analyses,
            consensus_score=consensus.get("global_score", 0.0),
        )
        risk_findings = self._step_risk_assessment(risk)
        steps.append(ReasoningStep(
            step=7, name="Risk Assessment",
            description="Évaluation du risque (sévérité, probabilité, impact, criticité)",
            findings=risk_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 8 — Response Plan ────────────────────────────────────────
        t = time.time()
        response_plan = self.response_engine.generate(
            query=query,
            classification=classification,
            analyses=analyses,
            risk=risk,
        )
        response_findings = self._step_response_plan(response_plan)
        steps.append(ReasoningStep(
            step=8, name="Response Plan",
            description="Génération du plan de réponse (confinement, éradication, récupération, prévention)",
            findings=response_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Step 9 — Final Verification ───────────────────────────────────
        t = time.time()
        final_decision = consensus.get("final_response") or "UNKNOWN"
        if isinstance(final_decision, dict):
            final_decision = final_decision.get("conclusion", "UNKNOWN")
        final_decision_str = str(final_decision).upper()
        if any(x in final_decision_str for x in ("BLOCK", "PHISH", "MALICIOUS", "MALWARE", "RANSOMWARE")):
            final_decision = "BLOCK"
        elif any(x in final_decision_str for x in ("ACCEPT", "SAFE", "LEGITIMATE", "BENIGN")):
            final_decision = "ACCEPT"
        else:
            final_decision = "UNKNOWN"

        verification_findings = self._step_final_verification(
            consensus, risk, contradictions, fact_check
        )
        steps.append(ReasoningStep(
            step=9, name="Final Verification",
            description="Vérification finale, cohérence de la décision et validation de la traçabilité",
            findings=verification_findings,
            elapsed_ms=(time.time() - t) * 1000,
        ))

        # ── Build Reasoning Trace ─────────────────────────────────────────
        rag_sources = list({r["source"] for r in fact_check.references})
        key_observations = self._extract_key_observations(analyses, fusion, attack_timeline)
        hypothesis = self._build_hypothesis(classification, attack_timeline, risk)
        hypothesis_validated = consensus.get("global_score", 0.0) >= 50 and len(contradictions) == 0
        info_gaps = self._identify_information_gaps(analyses, fact_check, attack_timeline)

        reasoning_trace = ReasoningTrace(
            incident_type=classification,
            classification_confidence=round(classification_confidence * 100, 2),
            experts_consulted=list({a.expert_name for a in analyses}),
            models_executed=[a.expert_id for a in analyses if a.status == "completed"],
            rag_sources_queried=rag_sources,
            steps=steps,
            key_observations=key_observations,
            hypothesis=hypothesis,
            hypothesis_validated=hypothesis_validated,
            information_gaps=info_gaps,
        )

        # ── Build Decision Journal ────────────────────────────────────────
        completed = [a for a in analyses if a.status == "completed"]
        formatted_decision = self._format_final_decision(final_decision, classification)
        contradictions_resolved = [
            {"left": c["left"], "right": c["right"], "resolved_by": c.get("resolved_by", "consensus"), "difference": c.get("difference", "conclusion")}
            for c in contradictions
        ]

        decision_journal = DecisionJournal(
            session_id=session_id,
            query_summary=query[:200],
            incident_type=classification,
            experts_solicited=[a.expert_name for a in analyses],
            models_executed=[a.expert_id for a in completed],
            sources_consulted=rag_sources + fusion.get("rag_sources_used", []),
            evidence_summary=fusion.get("unified_evidence", [])[:8],
            consensus_score=consensus.get("global_score", 0.0),
            confidence_level=consensus.get("confidence_level", "Low"),
            final_decision=formatted_decision,
            decision_justification=self._build_justification(
                formatted_decision, consensus, risk, contradictions
            ),
            contradictions_found=len(contradictions),
            contradictions_resolved=contradictions_resolved,
            false_positive_risk=consensus.get("false_positive_risk", "Low"),
            recommended_next_steps=response_plan.containment[:3] and
                [a.action for a in response_plan.containment[:3]] or [],
        )

        # Bloc 4: validation obligatoire avant émission
        decision_journal.validate_before_emission()

        return {
            "reasoning_trace": reasoning_trace,
            "attack_timeline": attack_timeline,
            "risk_assessment": risk,
            "response_plan": response_plan,
            "decision_journal": decision_journal,
            "evidence_fusion": fusion,
        }

    # ── Step builders ─────────────────────────────────────────────────────

    def _step_comprehension(self, query: str, classification: str, confidence: float) -> List[str]:
        return [
            f"Type de requête identifié: {classification}",
            f"Confiance classification: {confidence * 100:.1f}%",
            f"Longueur de la requête: {len(query)} caractères",
            f"Langue détectée: {'Français' if any(w in query.lower() for w in ['votre', 'compte', 'vérifiez', 'urgent', 'cliquez']) else 'Multilingual / Technique'}",
        ]

    def _step_planning(self, selected_experts: List[str], classification: str) -> List[str]:
        return [
            f"Stratégie d'analyse: priority_based avec fallback exhaustif",
            f"Experts sélectionnés: {len(selected_experts)} agents",
            f"Catégorie prioritaire: {classification}",
            f"Experts activés: {', '.join(selected_experts[:6]) or 'aucun chargé'}",
        ]

    def _step_evidence_collection(self, analyses: List[ExpertAnalysis]) -> List[str]:
        completed = sum(1 for a in analyses if a.status == "completed")
        failed = sum(1 for a in analyses if a.status in ("error", "timeout"))
        total_evidence = sum(len(a.evidence) for a in analyses)
        return [
            f"Experts interrogés: {len(analyses)}",
            f"Analyses complétées: {completed}",
            f"Analyses échouées: {failed}",
            f"Preuves totales collectées: {total_evidence}",
        ]

    def _step_cross_validation(
        self, analyses: List[ExpertAnalysis],
        contradictions: List[Dict],
        cross_validations: List[Any],
    ) -> List[str]:
        completed = [a for a in analyses if a.status == "completed"]
        confirmed = sum(1 for v in cross_validations if hasattr(v, 'status') and v.status == "confirmed")
        return [
            f"Experts validés mutuellement: {len(cross_validations)} paires vérifiées",
            f"Validations confirmées: {confirmed}",
            f"Contradictions détectées: {len(contradictions)}",
            f"Consensus entre experts: {'Fort' if not contradictions and len(completed) >= 2 else 'Modéré' if len(contradictions) <= 1 else 'Divergent'}",
        ]

    def _step_fusion_summary(self, fusion: Dict) -> List[str]:
        return [
            f"Sources fusionnées: {fusion.get('total_sources', 0)} ({fusion.get('sources_completed', 0)} complètes)",
            f"IOC unifiés: {len(fusion.get('unified_iocs', []))}",
            f"Techniques MITRE unifiées: {len(fusion.get('unified_mitre_techniques', []))}",
            f"Richesse de l'analyse: {fusion.get('information_richness', 'Unknown')}",
        ]

    def _step_attack_reconstruction(self, timeline: AttackTimeline) -> List[str]:
        findings = [
            f"Vecteur d'attaque: {timeline.attack_vector}",
            f"Point d'entrée: {timeline.entry_point}",
            f"Phases MITRE identifiées: {len(timeline.phases)}",
            f"IOC extraits: {len(timeline.iocs_extracted)}",
        ]
        if timeline.lateral_movement:
            findings.append("⚠️ Mouvement latéral détecté")
        if timeline.persistence_mechanism:
            findings.append(f"Persistance: {timeline.persistence_mechanism}")
        if timeline.exfiltration_detected:
            findings.append("⚠️ Exfiltration de données potentielle")
        return findings

    def _step_risk_assessment(self, risk: RiskAssessment) -> List[str]:
        return [
            f"Sévérité: {risk.severity} (score: {risk.severity_score:.1f}/10)",
            f"Probabilité: {risk.probability:.1f}%",
            f"Impact: {risk.impact}",
            f"Score de risque composite: {risk.risk_score:.1f}/100",
            f"Criticité: {risk.criticality}",
            f"Exploitabilité: {risk.exploitability}",
        ]

    def _step_response_plan(self, plan: ResponsePlan) -> List[str]:
        return [
            f"Type d'incident: {plan.incident_type}",
            f"Actions de confinement: {len(plan.containment)}",
            f"Actions d'éradication: {len(plan.eradication)}",
            f"Actions de récupération: {len(plan.recovery)}",
            f"Actions de prévention: {len(plan.prevention)}",
            f"Escalade requise: {'Oui' if plan.escalation_required else 'Non'}",
            f"Temps de résolution estimé: {plan.estimated_resolution_time}",
        ]

    def _step_final_verification(
        self, consensus: Dict, risk: RiskAssessment,
        contradictions: List[Dict], fact_check: FactCheckResult,
    ) -> List[str]:
        score = consensus.get("global_score", 0.0)
        findings = [
            f"Score de consensus final: {score:.1f}%",
            f"Niveau de confiance: {consensus.get('confidence_level', 'Low')}",
            f"Contradictions non résolues: {len(contradictions)}",
            f"Références RAG confirmées: {len(fact_check.references)}",
        ]
        if score >= 80:
            findings.append("✅ Décision à haute confiance — résultat fiable")
        elif score >= 50:
            findings.append("⚠️ Confiance modérée — revue humaine recommandée")
        else:
            findings.append("❌ Confiance faible — analyse humaine obligatoire")
        return findings

    # ── Synthesis helpers ─────────────────────────────────────────────────

    def _extract_key_observations(
        self, analyses: List[ExpertAnalysis],
        fusion: Dict, timeline: AttackTimeline,
    ) -> List[str]:
        obs = []
        if fusion.get("dominant_conclusion") and fusion["dominant_conclusion"] != "UNKNOWN":
            obs.append(f"Conclusion dominante: {fusion['dominant_conclusion']} "
                       f"({fusion.get('agreement_rate', 0):.0f}% d'accord entre experts)")
        if timeline.phases:
            obs.append(f"Tactique MITRE initiale détectée: {timeline.phases[0].phase_name}")
        if timeline.iocs_extracted:
            obs.append(f"{len(timeline.iocs_extracted)} indicateur(s) de compromission extraits")
        high_conf = [a for a in analyses if a.status == "completed" and a.confidence >= 70]
        if high_conf:
            obs.append(f"{len(high_conf)} expert(s) à haute confiance (≥70%)")
        return obs[:6]

    def _build_hypothesis(
        self, classification: str, timeline: AttackTimeline, risk: RiskAssessment
    ) -> str:
        if "phishing" in classification or "email" in classification:
            return (f"Hypothèse principale: tentative de phishing visant à "
                    f'{"compromettre des credentials" if "credential" in " ".join(timeline.mitre_tactics).lower() else "inciter l utilisateur à agir"}. '
                    f"Vecteur: {timeline.attack_vector}.")
        if "malware" in classification:
            return (f"Hypothèse principale: déploiement d'un malware via {timeline.attack_vector}. "
                    f"Impact potentiel: {risk.impact}.")
        if "ransomware" in classification:
            return "Hypothèse principale: attaque ransomware avec chiffrement de données potentiel."
        return (f"Hypothèse principale: incident de type '{classification}' avec "
                f"un niveau de risque {risk.severity}.")

    def _identify_information_gaps(
        self, analyses: List[ExpertAnalysis],
        fact_check: FactCheckResult, timeline: AttackTimeline,
    ) -> List[str]:
        gaps = []
        failed = [a for a in analyses if a.status in ("error", "timeout")]
        if failed:
            gaps.append(f"{len(failed)} expert(s) n'ont pas pu répondre: "
                        f"{', '.join(a.expert_name for a in failed)}")
        if not timeline.iocs_extracted:
            gaps.append("Aucun IOC précis extrait — analyse basée sur des patterns textuels")
        if fact_check.unconfirmed:
            gaps.append("Certaines affirmations n'ont pas de référence RAG locale correspondante")
        if not timeline.phases:
            gaps.append("Mapping MITRE ATT&CK incomplet — requête trop générique")
        return gaps

    def _build_justification(
        self, decision: str, consensus: Dict,
        risk: RiskAssessment, contradictions: List[Dict],
    ) -> str:
        score = consensus.get("global_score", 0.0)
        retained = consensus.get("total_retained", 0)
        total = consensus.get("total_models_executed", 0)
        parts = [
            f"Décision '{decision}' basée sur un consensus de {score:.1f}% "
            f"({retained}/{total} experts retenus).",
            f"Niveau de risque évalué: {risk.severity} avec un impact {risk.impact}.",
        ]
        if contradictions:
            parts.append(f"{len(contradictions)} contradiction(s) détectée(s) — traitées durant la phase de débat.")
        else:
            parts.append("Aucune contradiction majeure entre les experts.")
        return " ".join(parts)

    def _assess_fp_risk(
        self, risk: RiskAssessment, consensus: Dict,
        analyses: List[ExpertAnalysis],
    ) -> str:
        score = consensus.get("global_score", 0.0)
        if score >= 80 and risk.severity in ("HIGH", "CRITICAL"):
            return "Low — High-confidence detection with strong evidence"
        if score >= 50:
            return "Medium — Moderate confidence; human review recommended"
        if score >= 25:
            return "High — Low confidence; significant false positive risk"
        return "Very High — Insufficient evidence; treat as informational only"

    def _format_final_decision(self, raw_decision: str, classification: str) -> str:
        raw = raw_decision.upper()
        return raw  # Retourne le verdict brut pour le journal de décision
