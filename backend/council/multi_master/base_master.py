"""Base Master AI — Classe de base pour tous les Masters spécialisés.

Chaque Master AI :
1. Reçoit une requête et une classification
2. Construit un plan d'analyse (experts + modèles)
3. Exécute les experts en parallèle
4. Synthétise un verdict (conclusion, confiance, preuves)
5. Retourne un MasterResult pour la discussion inter-Masters
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.council.expert import ExpertModelManager
from backend.council.types import ExpertAnalysis

from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.types import MasterPlan, MasterVerdict


class MasterResult:
    """Résultat complet produit par un Master AI après analyse."""
    def __init__(
        self,
        verdict: MasterVerdict,
        analyses: List[ExpertAnalysis],
        plan: MasterPlan,
        elapsed_ms: float,
    ):
        self.verdict = verdict
        self.analyses = analyses
        self.plan = plan
        self.elapsed_ms = elapsed_ms


class BaseMaster(ABC):
    """Classe de base pour tous les Master AI spécialisés."""

    def __init__(
        self,
        master_id: str,
        master_name: str,
        expert_manager: ExpertModelManager,
        journal: Optional[DiscussionJournal] = None,
        expert_timeout_s: float = 30.0,
    ):
        self.master_id = master_id
        self.master_name = master_name
        self.experts = expert_manager
        self.journal = journal
        self.expert_timeout_s = expert_timeout_s

    @abstractmethod
    def build_plan(self, query: str, classification: str, context: Optional[Dict] = None) -> MasterPlan:
        """Construit le plan d'analyse : quels experts et modèles interroger."""

    @abstractmethod
    def synthesize_verdict(
        self,
        query: str,
        plan: MasterPlan,
        analyses: List[ExpertAnalysis],
    ) -> MasterVerdict:
        """Synthétise les analyses des experts en un verdict unique."""

    async def analyze(self, query: str, classification: str,
                      context: Optional[Dict] = None) -> MasterResult:
        """Point d'entrée : plan → exécution parallèle → verdict."""
        t0 = time.time()

        self._journal(f"🧠 {self.master_name}: Construction du plan d'analyse.")

        plan = self.build_plan(query, classification, context)
        if self.journal:
            self.journal.master_activated(self.master_id, self.master_name)
            self.journal.master_plan(self.master_id, self.master_name, plan.reasoning_steps)

        if not plan.selected_experts:
            self._journal(f"⚠️ {self.master_name}: Aucun expert sélectionné.")
            empty = MasterVerdict(
                master_id=self.master_id,
                master_name=self.master_name,
                conclusion="UNKNOWN",
                confidence=0.0,
                score=0.0,
                evidence=[],
                plan=plan,
                reasoning_summary="Aucun expert disponible pour l'analyse.",
            )
            return MasterResult(verdict=empty, analyses=[], plan=plan,
                                elapsed_ms=(time.time() - t0) * 1000)

        self._journal(f"🎯 {self.master_name}: Interrogation de {len(plan.selected_experts)} expert(s).")

        for eid in plan.selected_experts:
            expert = self.experts.get_expert(eid)
            if expert and self.journal:
                self.journal.expert_queried(
                    self.master_id, expert.expert_name,
                    f"Analyse requise: {plan.classification}"
                )

        analyses = await self.experts.run_parallel(
            query, plan.selected_experts, self.expert_timeout_s, context
        )

        for a in analyses:
            if a.status == "completed" and self.journal:
                self.journal.expert_responded(
                    self.master_id, a.expert_name,
                    f"{a.conclusion} (confiance: {a.confidence:.1f}%)"
                )

        self._journal(f"⚖ {self.master_name}: Synthèse du verdict.")

        verdict = self.synthesize_verdict(query, plan, analyses)
        if self.journal:
            self.journal.master_completed(
                self.master_id, self.master_name, verdict.conclusion, verdict.score
            )

        return MasterResult(
            verdict=verdict,
            analyses=analyses,
            plan=plan,
            elapsed_ms=(time.time() - t0) * 1000,
        )

    async def reevaluate(self, query: str, verdict: MasterVerdict, target_conclusion: str, context: Optional[Dict] = None) -> MasterVerdict:
        """Méthode de ré-évaluation appelée en cas de contradiction inter-Masters."""
        return verdict

    def _resolve_experts(self, names: List[str]) -> List[str]:
        """Résout les noms d'experts (alias compris) en expert_ids réels."""
        resolved = []
        from backend.council.orchestrator import EXPERT_ALIAS_MAP
        for name in names:
            if name in EXPERT_ALIAS_MAP:
                resolved.extend(EXPERT_ALIAS_MAP[name])
            else:
                resolved.append(name)
        return resolved

    def _active_experts(self, expert_ids: List[str]) -> List[str]:
        """Filtre les experts actifs dans le registre."""
        active = []
        for eid in expert_ids:
            if eid in self.experts._dynamic:
                active.append(eid)
                continue
            model = self.experts.registry.get_model(eid)
            if model:
                from backend.models_registry.base_model import ModelStatus
                if model.status() == ModelStatus.LOADED:
                    active.append(eid)
        return active

    def _journal(self, message: str):
        if self.journal:
            self.journal.error(self.master_id, message)
