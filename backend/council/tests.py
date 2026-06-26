import asyncio
from typing import Dict, Optional

from backend.council import CouncilConfig, CouncilExpert, ExpertAnalysis, ExpertModelManager, MasterAIOrchestrator


class DummyRegistry:
    def list_ids(self):
        return []

    def get_model(self, model_id):
        return None


class DummyExpert(CouncilExpert):
    def __init__(self, expert_id: str, conclusion: str, confidence: float, delay: float = 0.0, error: Optional[str] = None):
        self.expert_id = expert_id
        self.expert_name = expert_id.title()
        self.category = "test"
        self.capabilities = ["test"]
        self.conclusion = conclusion
        self.confidence = confidence
        self.delay = delay
        self.error = error

    async def analyze(self, query: str, context: Optional[Dict] = None) -> ExpertAnalysis:
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            return ExpertAnalysis(
                expert_id=self.expert_id,
                expert_name=self.expert_name,
                category=self.category,
                status="error",
                confidence=0.0,
                error=self.error,
            )
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
            inference_ms=self.delay * 1000,
        )


def make_orchestrator(*experts: DummyExpert, timeout_s: float = 0.2) -> MasterAIOrchestrator:
    registry = DummyRegistry()
    manager = ExpertModelManager(registry)
    for expert in experts:
        manager.register_expert(expert)
    config = CouncilConfig(
        enabled=True,
        max_debate_rounds=1,
        min_confidence_for_no_debate=80,
        expert_timeout_s=timeout_s,
        max_selected_experts=10,
        log_dir="/tmp/council-tests",
    )
    return MasterAIOrchestrator(registry, config, manager)


def run(coro):
    return asyncio.run(coro)


def test_immediate_consensus():
    orch = make_orchestrator(DummyExpert("a", "BLOCK", 95), DummyExpert("b", "BLOCK", 92))
    result = run(orch.run("phishing password click", models=["a", "b"]))
    assert result.final_response["conclusion"] == "BLOCK"
    assert result.consensus["global_score"] >= 90
    assert result.contradictions == []
    print("  PASS: immediate_consensus")


def test_disagreement_triggers_debate():
    orch = make_orchestrator(DummyExpert("a", "BLOCK", 94), DummyExpert("b", "ACCEPT", 91))
    result = run(orch.run("ambiguous alert", models=["a", "b"]))
    assert result.contradictions
    assert any(m.phase == "debate" for m in result.conversation)
    print("  PASS: disagreement_triggers_debate")


def test_absence_of_consensus():
    orch = make_orchestrator(DummyExpert("a", "UNKNOWN", 55), DummyExpert("b", "UNKNOWN", 50))
    result = run(orch.run("unclear sample", models=["a", "b"]))
    assert result.consensus["confidence_level"] == "Low"
    assert result.final_response["conclusion"] == "UNKNOWN"
    print("  PASS: absence_of_consensus")


def test_timeout_expert():
    orch = make_orchestrator(DummyExpert("slow", "BLOCK", 95, delay=0.5), DummyExpert("fast", "BLOCK", 90), timeout_s=0.05)
    result = run(orch.run("phishing", models=["slow", "fast"]))
    timed_out = [e for e in result.experts if e.status == "timeout"]
    assert len(timed_out) == 1
    assert result.metrics["experts_failed"] == 1
    print("  PASS: timeout_expert")


def test_error_expert():
    orch = make_orchestrator(DummyExpert("bad", "BLOCK", 0, error="boom"), DummyExpert("good", "BLOCK", 91))
    result = run(orch.run("malware", models=["bad", "good"]))
    assert any(e.status == "error" for e in result.experts)
    assert result.final_response["conclusion"] == "BLOCK"
    print("  PASS: error_expert")


def test_dynamic_expert_addition():
    orch = make_orchestrator()
    orch.experts.register_expert(DummyExpert("new_expert", "ACCEPT", 88))
    result = run(orch.run("normal activity", models=["new_expert"]))
    assert result.selected_models == ["new_expert"]
    assert result.experts[0].expert_id == "new_expert"
    print("  PASS: dynamic_expert_addition")


def test_concurrent_requests():
    orch = make_orchestrator(DummyExpert("a", "BLOCK", 90), DummyExpert("b", "BLOCK", 85))

    async def scenario():
        results = await asyncio.gather(
            orch.run("phishing 1", models=["a", "b"]),
            orch.run("phishing 2", models=["a", "b"]),
            orch.run("phishing 3", models=["a", "b"]),
        )
        return results

    results = run(scenario())
    assert len(results) == 3
    assert all(r.final_response["conclusion"] == "BLOCK" for r in results)
    print("  PASS: concurrent_requests")


if __name__ == "__main__":
    print("\n=== AI Security Council Tests ===\n")
    tests = [
        test_immediate_consensus,
        test_disagreement_triggers_debate,
        test_absence_of_consensus,
        test_timeout_expert,
        test_error_expert,
        test_dynamic_expert_addition,
        test_concurrent_requests,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL: {test.__name__} -> {exc}")
        except Exception as exc:
            print(f"  ERROR: {test.__name__} -> {exc}")
    print(f"\n=== {passed}/{len(tests)} tests passed ===\n")
