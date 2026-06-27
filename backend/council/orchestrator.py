import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.base import AgentContext
from backend.agents.model_router import CATEGORY_MODEL_MAP
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
from backend.council.types import CouncilMessage, CouncilResult


class MasterAIOrchestrator:
    def __init__(self, registry, config: Optional[CouncilConfig] = None, expert_manager: Optional[ExpertModelManager] = None):
        self.registry = registry
        self.config = config or CouncilConfig.default()
        self.experts = expert_manager or ExpertModelManager(registry)
        self.classifier = QueryClassifierAgent()
        self.discussion = DiscussionEngine()
        self.debate = DebateEngine()
        self.cross_validation = CrossValidationEngine()
        self.fact_check = LocalFactCheckEngine()
        self.consensus = CouncilConsensusEngine()
        self.reflection = ReflectionEngine()
        self.explainability = ExplainabilityEngine()
        self.metrics = MetricsCollector()

    async def run(self, query: str, user_role: str = "analyst", context: Optional[Dict] = None, models: Optional[List[str]] = None) -> CouncilResult:
        started_at = time.time()
        stage_times: Dict[str, float] = {}
        timeline = []
        conversation = [CouncilMessage("Master AI", None, "start", "Initialisation du AI Security Council.")]

        if not self.config.enabled:
            raise RuntimeError("AI Security Council disabled by configuration")

        t = time.time()
        agent_ctx = AgentContext(query=query, user_role=user_role, metadata=context or {})
        classification_result = await self.classifier.run(agent_ctx)
        classification = classification_result.output.get("primary_category", "general_security_question")
        stage_times["classification"] = (time.time() - t) * 1000
        timeline.append(_stage("classification", "completed", stage_times["classification"]))

        t = time.time()
        selected = self._select_experts(classification, models)
        stage_times["selection"] = (time.time() - t) * 1000
        timeline.append(_stage("selection", "completed", stage_times["selection"], {"models": selected}))
        conversation.append(CouncilMessage("Master AI", None, "selection", f"Experts selectionnes: {', '.join(selected) or 'aucun'}"))

        t = time.time()
        analyses = await self.experts.run_parallel(query, selected, self.config.expert_timeout_s, context)
        stage_times["parallel_analysis"] = (time.time() - t) * 1000
        timeline.append(_stage("parallel_analysis", "completed", stage_times["parallel_analysis"]))

        t = time.time()
        conversation.extend(await self.discussion.interview(self.experts, analyses))
        stage_times["discussion"] = (time.time() - t) * 1000
        timeline.append(_stage("discussion", "completed", stage_times["discussion"]))

        t = time.time()
        contradictions = detect_contradictions(analyses, self.config.disagreement_threshold)
        if debate_needed(analyses, contradictions, self.config.min_confidence_for_no_debate):
            conversation.extend(await self.debate.debate(self.experts, analyses, contradictions, self.config.max_debate_rounds))
            debate_status = "completed"
        else:
            debate_status = "skipped"
        stage_times["debate"] = (time.time() - t) * 1000
        timeline.append(_stage("debate", debate_status, stage_times["debate"], {"contradictions": len(contradictions)}))

        t = time.time()
        validations = []
        if self.config.cross_validation_enabled:
            validations = await self.cross_validation.validate(self.experts, analyses)
        stage_times["cross_validation"] = (time.time() - t) * 1000
        timeline.append(_stage("cross_validation", "completed" if validations else "skipped", stage_times["cross_validation"], {"items": len(validations)}))

        t = time.time()
        fact_check = self.fact_check.check(query, analyses) if self.config.fact_check_enabled else self.fact_check.check("", [])
        stage_times["fact_check"] = (time.time() - t) * 1000
        timeline.append(_stage("fact_check", "completed" if self.config.fact_check_enabled else "skipped", stage_times["fact_check"], {"references": len(fact_check.references)}))

        t = time.time()
        consensus = self.consensus.compute(query, analyses, contradictions)
        stage_times["consensus"] = (time.time() - t) * 1000
        timeline.append(_stage("consensus", "completed", stage_times["consensus"], {"score": consensus.get("global_score", 0.0)}))

        t = time.time()
        final_response = self.explainability.build(query, analyses, consensus, fact_check, contradictions)
        reflection = self.reflection.reflect(final_response, contradictions, fact_check) if self.config.reflection_enabled else {"passed": True, "issues": [], "action": "disabled"}
        stage_times["reflection"] = (time.time() - t) * 1000
        timeline.append(_stage("reflection", "completed" if self.config.reflection_enabled else "skipped", stage_times["reflection"], reflection))

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
        )
        self._log(result)
        return result

    def _select_experts(self, classification: str, models: Optional[List[str]]) -> List[str]:
        def is_active_model(mid: str) -> bool:
            model = self.registry.get_model(mid)
            if not model:
                return False
            from backend.models_registry.base_model import ModelStatus
            return model.status() == ModelStatus.LOADED

        if models:
            selected = [m for m in models if is_active_model(m)]
        else:
            selected = [m for m in CATEGORY_MODEL_MAP.get(classification, []) if is_active_model(m)]
            if not selected:
                selected = [m for m in self.registry.list_ids() if is_active_model(m)]
        return selected[: self.config.max_selected_experts]

    def _log(self, result: CouncilResult):
        try:
            log_dir = os.getenv("COUNCIL_LOG_DIR", self.config.log_dir)
            os.makedirs(log_dir, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            with open(os.path.join(log_dir, f"council_{ts}.json"), "w", encoding="utf-8") as f:
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
