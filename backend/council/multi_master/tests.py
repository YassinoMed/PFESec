import asyncio
import os
import sys
from typing import Dict, List, Optional
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.council.config import CouncilConfig
from backend.council.expert import CouncilExpert, ExpertModelManager
from backend.council.types import ExpertAnalysis

from backend.council.multi_master.global_coordinator import GlobalCoordinator
from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.types import MasterVerdict, MasterPlan


class DummyRegistry:
    def list_ids(self):
        return []

    def get_model(self, model_id):
        return None


class DummyExpert(CouncilExpert):
    def __init__(self, expert_id: str, conclusion: str, confidence: float, category: str = "test"):
        self.expert_id = expert_id
        self.expert_name = expert_id.replace("_", " ").title()
        self.category = category
        self.capabilities = [category]
        self.conclusion = conclusion
        self.confidence = confidence

    async def analyze(self, query: str, context: Optional[Dict] = None) -> ExpertAnalysis:
        return ExpertAnalysis(
            expert_id=self.expert_id,
            expert_name=self.expert_name,
            category=self.category,
            status="completed",
            response=self.conclusion,
            conclusion=self.conclusion,
            confidence=self.confidence,
            evidence=[f"indicator:{self.conclusion.lower()}"],
            limitations=[],
            inference_ms=1.0,
            recommendations=["Rec dummy"],
            iocs=[],
            mitre_techniques=[],
            severity="MEDIUM" if self.conclusion == "BLOCK" else "LOW",
        )


def make_coordinator(*experts: DummyExpert) -> GlobalCoordinator:
    registry = DummyRegistry()
    manager = ExpertModelManager(registry)
    for expert in experts:
        manager.register_expert(expert)
        
    config = CouncilConfig(
        enabled=True,
        max_debate_rounds=2,
        min_confidence_for_no_debate=80,
        expert_timeout_s=1.0,
        max_selected_experts=10,
        log_dir="/tmp/multi-master-tests",
    )
    
    manager._virtual_registered = True
    
    journal = DiscussionJournal(log_dir="/tmp/multi-master-logs")
    return GlobalCoordinator(registry, config, manager, journal)


def run(coro):
    return asyncio.run(coro)


def test_multi_master_conflict_and_resolution():
    # Threat Expert says BLOCK, SOC Analyst says ACCEPT -> Contradiction!
    coord = make_coordinator(
        DummyExpert("phishing_expert", "BLOCK", 98, "phishing"),
        DummyExpert("email_header_expert", "BLOCK", 95, "phishing"),
        DummyExpert("soc_analyst_expert", "ACCEPT", 92, "soc"),
        DummyExpert("rag_knowledge_expert", "BLOCK", 85, "knowledge"),
        DummyExpert("governance_expert", "ACCEPT", 90, "governance"),
    )
    
    # We query something that activates phishing_analysis
    # CLASSIFICATION_TO_MASTERS: phishing_analysis activates threat_master, rag_master, soc_master, governance_master
    result = run(coord.run("Analyse de tentative de phishing dans cet email urgent avec un lien banque-secure.xyz", context={"primary_category": "phishing_analysis"}))
    
    print("ALL REGISTERED EXPERTS:", list(coord.experts._dynamic.keys()))
    print(f"Classification: {result.classification}")
    print(f"Activated Masters: {result.activated_masters}")
    print("SOC MASTER PLAN EXPERTS:", coord.soc_master.build_plan("Analyse de tentative de phishing dans cet email urgent avec un lien banque-secure.xyz", "phishing_analysis").selected_experts)
    print(f"Master Verdicts:")
    for mid, verd in result.weighted_consensus.master_verdicts.items():
        print(f"  - {mid}: conclusion={verd.conclusion}, score={verd.score:.1f}%, evidence={verd.evidence}")
        print(f"    expert_analyses: {[(a.expert_id, a.status, a.conclusion, a.confidence) for a in verd.expert_analyses]}")
    
    print("\n--- Test Multi-Master logs ---")
    for log in result.discussion_log:
        print(f"Round {log.round} | {log.speaker_name} -> {log.target_name or 'All'}: {log.message}")
        
    # Check that a discussion occurred
    assert result.discussion_rounds > 0
    assert len(result.activated_masters) == 4
    
    # Check that consensus final contains weighted decision
    consensus = result.weighted_consensus
    assert consensus is not None
    assert consensus.verdict_final == "BLOCK"  # Threat (0.40) + RAG (0.20) > SOC (0.30) + Gov (0.10)
    assert consensus.score > 70.0
    
    # Check that re-evaluations are reflected in the discussion journal
    assert any("Nouvelle vérification. Merci de justifier vos conclusions." in entry["message"] for entry in coord.journal.get_all())
    assert any("Ré-évaluation CTI:" in ev for v in consensus.master_verdicts.values() for ev in v.evidence)
    
    print("  PASS: test_multi_master_conflict_and_resolution")


if __name__ == "__main__":
    print("\n=== Multi-Master AI Architecture Tests ===\n")
    try:
        test_multi_master_conflict_and_resolution()
        print("\n=== All Multi-Master tests passed! ===\n")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        sys.exit(1)
