"""Tests for AI Security Council v2 — 13 scenarios + resilience tests (pure ASCII logging to avoid codec issues)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class MockRegistry:
    """Minimal registry mock — no GPU models needed for virtual expert tests."""
    def get_model(self, mid): return None
    def list_ids(self): return []
    def list_models(self): return []


def get_orchestrator():
    from backend.council.orchestrator import MasterAIOrchestrator
    from backend.council.config import CouncilConfig
    config = CouncilConfig.default()
    config.expert_timeout_s = 10.0
    config.max_selected_experts = 8
    return MasterAIOrchestrator(MockRegistry(), config)


SCENARIOS = [
    # (name, query, expected_classification_keywords, expected_conclusion)
    ("phishing_fr", "URGENT: Votre compte a été suspendu. Cliquez ici pour vérifier votre identité: http://banque-secure.xyz/login", ["phishing"], "BLOCK"),
    ("phishing_en", "Dear customer, your PayPal account is limited. Please verify your credentials at http://paypal-verify.xyz immediately.", ["phishing"], "BLOCK"),
    ("malware_powershell", "PowerShell -EncodedCommand UwB0AGEAcgB0AC0AUAByAG8AYwBlAHMAcwAgbQBzAGYAdABlAGQAaQB0AC4AZQB4AGUA", ["malware"], "BLOCK"),
    ("ransomware", "All files have been encrypted by LockBit 3.0. Your Shadow Copies have been deleted. Pay 5 BTC to recover your data.", ["ransomware", "malware"], "BLOCK"),
    ("mitre_apt", "Analysis of APT28 TTP. Initial Access via spearphishing (T1566.001), Execution via PowerShell (T1059.001), Lateral Movement via PtH (T1550.002).", ["threat"], "BLOCK"),
    ("cve_critical", "CVE-2021-44228 Log4Shell critical vulnerability detected. Remote code execution without authentication. CVSS 10.0.", ["cve", "vulnerability"], "BLOCK"),
    ("sigma_rule", "Sigma rule for detecting LSASS memory access: EventID 10, TargetImage endswith lsass.exe. Mapped to T1003.001.", ["sigma"], "BLOCK"),
    ("cloud_s3", "AWS S3 bucket 'prod-customer-data' has public read access enabled. No encryption at rest. CloudTrail disabled.", ["cloud"], "BLOCK"),
    ("k8s_privileged", "Kubernetes deployment with privileged: true, hostNetwork: true, runAsRoot: true. ClusterRole admin bound to default service account.", ["kubernetes"], "BLOCK"),
    ("devsecops_secret", "Found hardcoded AWS access key AKIAIOSFODNN7EXAMPLE in repository commit a1b2c3d. Password 'P@ssw0rd123' in config.yml.", ["devsecops"], "BLOCK"),
    ("threat_intel_c2", "Cobalt Strike beacon detected communicating to 192.168.1.100:443. APT29 TTPs identified. MISP IOC confirmed.", ["threat_intel"], "BLOCK"),
    ("ir_breach", "Data breach detected: 50,000 customer PII records exfiltrated. GDPR notification required within 72h. Domain controller compromised.", ["incident"], "BLOCK"),
    ("safe_query", "What is the MITRE ATT&CK framework and how does it help SOC analysts?", ["general", "rag"], "UNKNOWN"),
]


def run_scenario(orchestrator, name: str, query: str):
    """Run a single scenario and return pass/fail."""
    try:
        result = asyncio.run(orchestrator.run(query=query, user_role="analyst"))
        result_dict = result.to_dict()

        # Validate core fields
        assert "classification" in result_dict, "Missing classification"
        assert "experts" in result_dict, "Missing experts"
        assert "consensus" in result_dict, "Missing consensus"
        assert "final_response" in result_dict, "Missing final_response"

        # v2 fields
        assert "reasoning_trace" in result_dict, "Missing reasoning_trace"
        assert "attack_timeline" in result_dict, "Missing attack_timeline"
        assert "risk_assessment" in result_dict, "Missing risk_assessment"
        assert "response_plan" in result_dict, "Missing response_plan"
        assert "decision_journal" in result_dict, "Missing decision_journal"

        # Validate reasoning trace structure
        rt = result_dict["reasoning_trace"]
        assert len(rt["steps"]) >= 8, f"Expected 8+ reasoning steps, got {len(rt['steps'])}"

        # Validate response plan has 4 phases
        rp = result_dict["response_plan"]
        assert "containment" in rp, "Response plan missing containment"
        assert "eradication" in rp, "Response plan missing eradication"
        assert "recovery" in rp, "Response plan missing recovery"
        assert "prevention" in rp, "Response plan missing prevention"

        # Validate decision journal
        dj = result_dict["decision_journal"]
        assert dj["final_decision"] in ("BLOCK", "ACCEPT", "UNKNOWN"), f"Invalid decision: {dj['final_decision']}"
        assert len(dj["decision_justification"]) > 10, "Decision justification too short"

        # Validate attack timeline
        at = result_dict["attack_timeline"]
        assert "attack_vector" in at, "Attack timeline missing attack_vector"
        assert "phases" in at, "Attack timeline missing phases"

        experts_count = len(result_dict["experts"])
        consensus_score = result_dict["consensus"].get("global_score", 0)
        decision = dj["final_decision"]

        print(f"  [PASS] [{name}] -- {experts_count} experts, consensus={consensus_score:.1f}%, decision={decision}")
        return True
    except Exception as exc:
        import traceback
        print(f"  [FAIL] [{name}] -- {exc}")
        traceback.print_exc()
        return False


def test_resilience_no_experts(orchestrator):
    """Test with a query that matches no specific category."""
    result = asyncio.run(orchestrator.run(
        query="Hello world",
        user_role="analyst",
    ))
    assert result.to_dict()["reasoning_trace"] is not None
    print("  [PASS] [resilience_no_category]")


def test_decision_journal_completeness(orchestrator):
    """Test that decision journal is always complete."""
    result = asyncio.run(orchestrator.run(
        query="Test query",
        user_role="analyst",
    ))
    dj = result.decision_journal
    assert dj is not None
    assert dj.session_id
    assert dj.timestamp
    assert dj.final_decision in ("BLOCK", "ACCEPT", "UNKNOWN")
    print("  [PASS] [decision_journal_completeness]")


def test_evidence_fusion_present(orchestrator):
    """Test that evidence fusion is always computed."""
    result = asyncio.run(orchestrator.run(
        query="CVE-2021-44228 critical vulnerability",
        user_role="analyst",
    ))
    ef = result.evidence_fusion
    assert ef is not None
    assert "total_sources" in ef
    assert "unified_evidence" in ef
    print("  [PASS] [evidence_fusion_present]")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  AI Security Council v2 -- Test Suite")
    print("=" * 70)

    orch = get_orchestrator()
    passed = 0
    failed = 0

    print("\nScenario Tests:")
    for scenario_name, query, _, _ in SCENARIOS:
        ok = run_scenario(orch, scenario_name, query)
        if ok:
            passed += 1
        else:
            failed += 1

    print("\nResilience Tests:")
    try:
        test_resilience_no_experts(orch)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] [resilience_no_category] -- {e}")
        failed += 1

    try:
        test_decision_journal_completeness(orch)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] [decision_journal_completeness] -- {e}")
        failed += 1

    try:
        test_evidence_fusion_present(orch)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] [evidence_fusion_present] -- {e}")
        failed += 1

    print(f"\n{'=' * 70}")
    print(f"  Results: {passed} passed, {failed} failed / {passed + failed} total")
    print(f"{'=' * 70}\n")

    sys.exit(0 if failed == 0 else 1)
