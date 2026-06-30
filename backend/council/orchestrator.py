"""MasterAIOrchestrator v2 — Full AI Security Council with Reasoning Engine.

Orchestrates: Classification → Expert Selection → Parallel Analysis → Discussion →
Evidence Fusion → Debate → Cross-validation → Fact-check → Consensus →
Attack Reconstruction → Risk Assessment → Response Plan → Decision Journal.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime
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
from backend.council.reasoning_engine import ReasoningEngine
from backend.council.types import CouncilMessage, CouncilResult


# ── Expert Alias Map ──── resolves user-friendly names → actual expert_ids  ──

EXPERT_ALIAS_MAP: Dict[str, List[str]] = {
    "email_expert": ["email_header_expert", "phishing_expert"],
    "cloud_expert": ["cloud_security_expert"],
    "ir_expert": ["incident_response_expert"],
    "kubernetes_expert": ["kubernetes_security_expert"],
    "devsecops_expert": ["devsecops_expert"],
}

# ── Bloc 1 — ROUTING TABLE (remplace intégralement l'ancienne) ──────────────

ROUTING_TABLE: Dict[str, Dict[str, Any]] = {
    "phishing_analysis": {
        "obligatoires": ["email_expert", "threat_intel_expert"],
        "optionnels": ["ioc_expert", "mitre_expert"],
        "description": "Analyse de tentatives de phishing",
    },
    "url_analysis": {
        "obligatoires": ["ioc_expert", "threat_intel_expert"],
        "optionnels": ["email_expert"],
        "description": "Analyse de réputation d'URL",
    },
    "ioc_analysis": {
        "obligatoires": ["ioc_expert", "threat_intel_expert"],
        "optionnels": ["malware_expert"],
        "description": "Analyse d'indicateurs de compromission",
    },
    "cve_analysis": {
        "obligatoires": ["mitre_expert", "ioc_expert"],
        "optionnels": ["devsecops_expert", "cloud_expert"],
        "description": "Analyse de vulnérabilités et CVE",
    },
    "malware_analysis": {
        "obligatoires": ["malware_expert", "ioc_expert"],
        "optionnels": ["mitre_expert", "threat_intel_expert"],
        "description": "Analyse de code malveillant",
    },
    "cloud_incident": {
        "obligatoires": ["cloud_expert", "ir_expert"],
        "optionnels": ["mitre_expert", "devsecops_expert"],
        "description": "Incident de sécurité cloud (AWS/Azure/GCP)",
    },
    "kubernetes_incident": {
        "obligatoires": ["kubernetes_expert", "ir_expert"],
        "optionnels": ["cloud_expert", "sigma_expert"],
        "description": "Incident de sécurité Kubernetes",
    },
    "siem_investigation": {
        "obligatoires": ["soc_analyst_expert", "sigma_expert", "mitre_expert"],
        "optionnels": ["threat_intel_expert", "ir_expert"],
        "description": "Analyse d'alertes SIEM, logs réseau, événements de sécurité structurés",
        "triggers": [
            "contient: 'EventID'",
            "contient: 'src_ip' ou 'dst_ip'",
            "contient: 'Syslog' ou 'CEF' ou 'LEEF'",
            "contient: 'failed login' ou 'authentication'",
            "contient: 'process_name' ou 'CommandLine'",
            "contient: 'alert' + champs réseau",
            "format: JSON avec champs timestamp + severity",
        ],
    },
    "incident_active": {
        "obligatoires": ["ir_expert", "soc_analyst_expert", "threat_intel_expert"],
        "optionnels": ["mitre_expert", "cloud_expert", "kubernetes_expert"],
        "description": "Incident de sécurité en cours nécessitant une réponse immédiate",
        "triggers": [
            "contient: 'incident en cours'",
            "contient: 'compromis' ou 'compromission'",
            "contient: 'breach' ou 'intrusion active'",
            "contient: 'ransomware actif'",
            "contient: 'exfiltration en cours'",
            "contient: 'lateral movement détecté'",
            "urgence explicitement déclarée par l'analyste",
        ],
        "priorite": "CRITIQUE",
        "sla_reponse": "< 2s",
    },
    "general_security_question": {
        "obligatoires": ["soc_analyst_expert"],
        "optionnels": [],
        "escalade": True,
        "description": "Question sécurité générale",
    },
}

# ── Catégories legacy (conservées pour compatibilité du classificateur) ──────
# Ces catégories ne sont pas explicitement dans la table mais existent
# dans QUERY_CATEGORIES et peuvent être produites par le classificateur.
LEGACY_CATEGORY_MAP: Dict[str, Dict[str, Any]] = {
    "email_analysis": {
        "obligatoires": ["email_expert"],
        "optionnels": ["threat_intel_expert"],
    },
    "sigma_analysis": {
        "obligatoires": ["sigma_expert", "soc_analyst_expert"],
        "optionnels": ["mitre_expert"],
    },
    "incident_response": {
        "obligatoires": ["incident_response_expert", "soc_analyst_expert"],
        "optionnels": ["threat_intel_expert"],
    },
    "threat_hunting": {
        "obligatoires": ["threat_intel_expert", "mitre_expert"],
        "optionnels": ["sigma_expert", "soc_analyst_expert"],
    },
    "log_analysis": {
        "obligatoires": ["soc_analyst_expert", "sigma_expert"],
        "optionnels": ["mitre_expert"],
    },
    "cloud_security": {
        "obligatoires": ["cloud_expert"],
        "optionnels": ["ir_expert"],
    },
    "kubernetes_security": {
        "obligatoires": ["kubernetes_expert"],
        "optionnels": ["cloud_expert"],
    },
    "devsecops_review": {
        "obligatoires": ["devsecops_expert"],
        "optionnels": [],
    },
    "rag_question": {
        "obligatoires": ["rag_knowledge_expert"],
        "optionnels": ["mitre_expert"],
    },
    "HORS_DOMAINE": {
        "obligatoires": [],
        "optionnels": [],
        "escalade": False,
    },
}


class MasterAIOrchestrator:
    def __init__(
        self,
        registry,
        config: Optional[CouncilConfig] = None,
        expert_manager: Optional[ExpertModelManager] = None,
    ):
        self.registry = registry
        self.config = config or CouncilConfig.default()
        self.experts = expert_manager or ExpertModelManager(registry)
        # Register all 15 virtual experts at startup
        self.experts.register_all_virtual_experts()
        self.classifier = QueryClassifierAgent()
        self.discussion = DiscussionEngine()
        self.debate = DebateEngine()
        self.cross_validation = CrossValidationEngine()
        self.fact_check = LocalFactCheckEngine()
        self.consensus = CouncilConsensusEngine()
        self.reflection = ReflectionEngine()
        self.explainability = ExplainabilityEngine()
        self.metrics = MetricsCollector()
        # v2 — Master AI Reasoning Engine
        self.reasoning_engine = ReasoningEngine()

    # ── T07: Extensions dangereuses ────────────────────────────────────────
    DANGEROUS_EXTENSIONS = {
        ".exe", ".dll", ".bat", ".cmd", ".com", ".scr", ".pif",
        ".js", ".vbs", ".ps1", ".py", ".sh", ".hta", ".wsf",
        ".zip", ".rar", ".7z", ".iso", ".img",
        ".docx", ".xlsx", ".pdf", ".rtf", ".pptx",
        ".lnk", ".url",
    }

    def _detect_attachment(self, query: str) -> Dict:
        """T07: Détecte les références à des pièces jointes avec extensions dangereuses."""
        exts = '|'.join(re.escape(e.lstrip('.')) for e in self.DANGEROUS_EXTENSIONS)
        word_pattern = re.compile(rf'(\S+?\.(?:{exts}))(?:\s|$|\.)', re.IGNORECASE)
        matches = word_pattern.findall(query)
        if not matches:
            return {"detected": False}

        filenames = list(set(m.rstrip('.') for m in matches))

        # Détection robuste double extension
        has_double_ext = False
        for f in filenames:
            dots = [i for i, c in enumerate(f) if c == '.']
            if len(dots) >= 2:
                has_double_ext = True
                break
            # Vérifier aussi si le pattern trouve des extensions consécutives
            consecutive = re.findall(rf'\.(?:{exts})\.(?:{exts})', query, re.IGNORECASE)
            if consecutive:
                has_double_ext = True
                break

        return {
            "detected": True,
            "filenames": filenames,
            "double_extension": has_double_ext,
        }

    async def run(
        self,
        query: str,
        user_role: str = "analyst",
        context: Optional[Dict] = None,
        models: Optional[List[str]] = None,
    ) -> CouncilResult:
        started_at = time.time()
        stage_times: Dict[str, float] = {}
        timeline = []
        conversation = [CouncilMessage("Master AI", None, "start", "Initialisation du AI Security Council v2.")]

        if not self.config.enabled:
            raise RuntimeError("AI Security Council disabled by configuration")

        # ── T04: Détection artefact vide ─────────────────────────────────
        if query is None or query.strip() == "":
            audit_entry = {
                "type": "INPUT_ERROR",
                "sous_type": "ARTEFACT_VIDE",
                "timestamp": datetime.utcnow().isoformat(),
                "action": "pipeline_stoppe",
            }
            self._log_audit(audit_entry)
            return CouncilResult(
                query=query or "",
                classification="ERREUR_INPUT",
                selected_models=[],
                experts=[],
                conversation=conversation + [CouncilMessage("Master AI", None, "error", "Artefact vide ou non analysable")],
                contradictions=[],
                cross_validations=[],
                fact_check=self.fact_check.check("", []),
                consensus={"global_score": 0.0, "confidence_level": "N/A",
                           "final_response": "ERREUR_INPUT: Artefact vide ou non analysable"},
                reflection={"passed": False, "issues": ["input_empty"], "action": "rejected"},
                final_response={"conclusion": "ERREUR_INPUT", "answer": "Artefact vide ou non analysable. Veuillez soumettre un artefact valide."},
                timeline=timeline + [_stage("input_validation", "rejected", 0),
                                     _stage("classification", "skipped", 0),
                                     _stage("expert_selection", "skipped", 0),
                                     _stage("analysis", "skipped", 0),
                                     _stage("consensus", "skipped", 0)],
                metrics={"total_execution_ms": round((time.time() - started_at) * 1000, 2),
                         "stage_times_ms": {"input_validation": 0},
                         "experts_total": 0, "experts_completed": 0, "experts_failed": 0},
                config=self.config.to_dict(),
            )

        # ── Stage 1: Classification ──────────────────────────────────────
        t = time.time()
        agent_ctx = AgentContext(query=query, user_role=user_role, metadata=context or {})
        classification_result = await self.classifier.run(agent_ctx)
        classification = classification_result.output.get("primary_category", "general_security_question")
        classification_confidence = classification_result.confidence
        query_lang = classification_result.output.get("langue_detectee", "UNKNOWN")
        stage_times["classification"] = (time.time() - t) * 1000
        timeline.append(_stage("classification", "completed", stage_times["classification"]))

        # ── T05: Ajouter la langue au contexte pipeline ─────────────────
        pipeline_context = dict(context or {})
        pipeline_context["langue_detectee"] = query_lang

        # ── Bloc 2 — Étape 1 (T32): OUT OF SCOPE → STOP pipeline ──
        if classification == "HORS_DOMAINE":
            audit_entry = {
                "type": "OUT_OF_SCOPE",
                "input_hash": hashlib.sha256(query.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._log_audit(audit_entry)
            return CouncilResult(
                query=query,
                classification="HORS_DOMAINE",
                selected_models=[],
                experts=[],
                conversation=conversation,
                contradictions=[],
                cross_validations=[],
                fact_check=self.fact_check.check("", []),
                consensus={"global_score": 0.0, "confidence_level": "N/A",
                           "final_response": "Cette requête ne relève pas du périmètre cybersécurité de SecureRAG Hub."},
                reflection={"passed": True, "issues": [], "action": "out_of_scope"},
                final_response={"conclusion": "HORS_DOMAINE", "answer": "Requête hors domaine cybersécurité."},
                timeline=timeline + [_stage("expert_selection", "skipped", 0),
                                     _stage("analysis", "skipped", 0),
                                     _stage("consensus", "skipped", 0)],
                metrics={"total_execution_ms": round((time.time() - started_at) * 1000, 2),
                         "stage_times_ms": {"classification": stage_times["classification"]},
                         "experts_total": 0, "experts_completed": 0, "experts_failed": 0},
                config=self.config.to_dict(),
            )

        # ── Stage 2: Expert Selection ────────────────────────────────────
        t = time.time()
        selected = self._select_experts(classification, classification_confidence, models)
        stage_times["selection"] = (time.time() - t) * 1000
        timeline.append(_stage("selection", "completed", stage_times["selection"], {"models": selected}))

        # ── BONUS: Anti-deadlock pour phishing avec < 3 experts (auto-routing only) ──
        if models is None and classification in ("phishing_analysis", "email_analysis") and len(selected) < 3:
            anti_deadlock_pool = ["soc_analyst_expert", "ioc_expert", "mitre_expert"]
            for candidate in anti_deadlock_pool:
                if candidate not in selected:
                    selected.append(candidate)
                    self._log_audit({
                        "type": "ANTI_DEADLOCK",
                        "raison": f"{classification} avec {len(selected)-1} experts — ajout de {candidate}",
                        "expert_ajoute": candidate,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    break

        # ── T07: Détection pièces jointes → forcer malware_expert + email_expert ──
        attachment_info = self._detect_attachment(query)
        if attachment_info["detected"]:
            pipeline_context["attachment_analysis"] = attachment_info
            for required in ("malware_expert", "email_header_expert"):
                resolved = self._resolve_expert_name(required)
                for mid in resolved:
                    if mid not in selected:
                        selected.append(mid)
                        self._log_audit({
                            "type": "ATTACHMENT_FORCE",
                            "fichiers": attachment_info["filenames"],
                            "expert_ajoute": mid,
                            "timestamp": datetime.utcnow().isoformat(),
                        })

        # ── Audit trail: routing ─────────────────────────────────────────
        self._log_audit({
            "type": "routing",
            "classification": classification,
            "experts_selectionnes": selected,
            "timestamp": datetime.utcnow().isoformat(),
        })

        conversation.append(CouncilMessage(
            "Master AI", None, "selection",
            f"Experts selectionnes: {', '.join(selected) or 'aucun'}",
        ))

        # ── Stage 3: Parallel Expert Analysis ───────────────────────────
        t = time.time()
        analyses = await self.experts.run_parallel(query, selected, self.config.expert_timeout_s, pipeline_context)
        stage_times["parallel_analysis"] = (time.time() - t) * 1000
        timeline.append(_stage("parallel_analysis", "completed", stage_times["parallel_analysis"]))

        # ── Stage 4: Discussion ──────────────────────────────────────────
        t = time.time()
        conversation.extend(await self.discussion.interview(self.experts, analyses))
        stage_times["discussion"] = (time.time() - t) * 1000
        timeline.append(_stage("discussion", "completed", stage_times["discussion"]))

        # ── Stage 5: Debate ──────────────────────────────────────────────
        t = time.time()
        contradictions = detect_contradictions(analyses, self.config.disagreement_threshold)
        if debate_needed(analyses, contradictions, self.config.min_confidence_for_no_debate):
            conversation.extend(await self.debate.debate(
                self.experts, analyses, contradictions, self.config.max_debate_rounds
            ))
            debate_status = "completed"
        else:
            debate_status = "skipped"
        stage_times["debate"] = (time.time() - t) * 1000
        timeline.append(_stage("debate", debate_status, stage_times["debate"], {"contradictions": len(contradictions)}))

        # ── Stage 6: Cross-validation ────────────────────────────────────
        t = time.time()
        validations = []
        if self.config.cross_validation_enabled:
            validations = await self.cross_validation.validate(self.experts, analyses)
        stage_times["cross_validation"] = (time.time() - t) * 1000
        timeline.append(_stage(
            "cross_validation",
            "completed" if validations else "skipped",
            stage_times["cross_validation"],
            {"items": len(validations)},
        ))

        # ── Stage 7: Fact-check ──────────────────────────────────────────
        t = time.time()
        fact_check = (
            self.fact_check.check(query, analyses)
            if self.config.fact_check_enabled
            else self.fact_check.check("", [])
        )
        stage_times["fact_check"] = (time.time() - t) * 1000
        timeline.append(_stage(
            "fact_check",
            "completed" if self.config.fact_check_enabled else "skipped",
            stage_times["fact_check"],
            {"references": len(fact_check.references)},
        ))

        # ── Stage 8: Consensus ───────────────────────────────────────────
        t = time.time()
        consensus = self.consensus.compute(query, analyses, contradictions, fact_check=fact_check)
        stage_times["consensus"] = (time.time() - t) * 1000
        timeline.append(_stage(
            "consensus", "completed", stage_times["consensus"],
            {"score": consensus.get("global_score", 0.0)},
        ))

        # ── Stage 9: Final Response + Reflection ─────────────────────────
        t = time.time()
        final_response = self.explainability.build(query, analyses, consensus, fact_check, contradictions)
        reflection = (
            self.reflection.reflect(final_response, contradictions, fact_check)
            if self.config.reflection_enabled
            else {"passed": True, "issues": [], "action": "disabled"}
        )
        stage_times["reflection"] = (time.time() - t) * 1000
        timeline.append(_stage(
            "reflection",
            "completed" if self.config.reflection_enabled else "skipped",
            stage_times["reflection"],
            reflection,
        ))

        # ── v2: Master AI Reasoning Engine ──────────────────────────────
        t = time.time()
        reasoning_artifacts = self.reasoning_engine.execute(
            query=query,
            classification=classification,
            classification_confidence=classification_confidence,
            selected_experts=selected,
            analyses=analyses,
            contradictions=contradictions,
            cross_validations=validations,
            fact_check=fact_check,
            consensus=consensus,
        )
        stage_times["reasoning_engine"] = (time.time() - t) * 1000
        timeline.append(_stage("reasoning_engine", "completed", stage_times["reasoning_engine"]))

        metrics = self.metrics.collect(started_at, stage_times, analyses)
        result = CouncilResult(
            query=query,
            classification=classification,
            selected_models=selected,
            experts=analyses,
            conversation=conversation,
            contradictions=contradictions,
            cross_validations=validations,
            fact_check=fact_check,
            consensus=consensus,
            reflection=reflection,
            final_response=final_response,
            timeline=timeline,
            metrics=metrics,
            config=self.config.to_dict(),
            # v2 extensions
            reasoning_trace=reasoning_artifacts.get("reasoning_trace"),
            attack_timeline=reasoning_artifacts.get("attack_timeline"),
            risk_assessment=reasoning_artifacts.get("risk_assessment"),
            response_plan=reasoning_artifacts.get("response_plan"),
            decision_journal=reasoning_artifacts.get("decision_journal"),
            evidence_fusion=reasoning_artifacts.get("evidence_fusion"),
        )
        self._log(result)
        return result

    def _resolve_expert_name(self, name: str) -> List[str]:
        """Resolve an expert name (possibly an alias) to actual expert_ids."""
        if name in EXPERT_ALIAS_MAP:
            return list(EXPERT_ALIAS_MAP[name])
        return [name]

    def _select_experts(self, classification: str, confidence: float = 0.0, models: Optional[List[str]] = None) -> List[str]:
        def is_active_model(mid: str) -> bool:
            if mid in self.experts._dynamic:
                return True
            model = self.registry.get_model(mid)
            if not model:
                return False
            from backend.models_registry.base_model import ModelStatus
            return model.status() == ModelStatus.LOADED

        # If explicit models requested, use those directly
        if models:
            return [m for m in models if is_active_model(m)]

        # 1. Resolve routing entry for this classification
        route = ROUTING_TABLE.get(classification)
        if route is None:
            # Try legacy categories
            legacy = LEGACY_CATEGORY_MAP.get(classification)
            if legacy is not None:
                route = legacy
            else:
                route = ROUTING_TABLE["general_security_question"]
                classification = "general_security_question"

        # 2. Always activate ALL obligatoires (resolve aliases)
        raw_obligatoires = route.get("obligatoires", [])
        resolved = []
        for name in raw_obligatoires:
            resolved.extend(self._resolve_expert_name(name))
        selected = [m for m in resolved if is_active_model(m)]

        # 3. Activate optionnels if confidence < 70% (needs more viewpoints)
        if confidence < 0.70:
            for name in route.get("optionnels", []):
                for mid in self._resolve_expert_name(name):
                    if mid not in selected and is_active_model(mid):
                        selected.append(mid)

        # 4. Ensure minimum 2 experts
        if len(selected) < 2:
            fallback_bucket = [
                "phishing_expert", "soc_analyst_expert", "ioc_expert",
                "mitre_expert", "threat_intel_expert",
            ]
            for mid in fallback_bucket:
                if mid not in selected and is_active_model(mid):
                    selected.append(mid)
                    if len(selected) >= 2:
                        break

        return selected[: self.config.max_selected_experts]

    def _log_audit(self, entry: Dict):
        try:
            log_dir = os.getenv("COUNCIL_LOG_DIR", self.config.log_dir)
            os.makedirs(log_dir, exist_ok=True)
            audit_log = os.path.join(log_dir, "audit_trail.jsonl")
            with open(audit_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def _log(self, result: CouncilResult):
        try:
            log_dir = os.getenv("COUNCIL_LOG_DIR", self.config.log_dir)
            os.makedirs(log_dir, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            with open(os.path.join(log_dir, f"council_v2_{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass


def _stage(name: str, status: str, elapsed_ms: float, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "elapsed_ms": round(elapsed_ms, 2),
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
