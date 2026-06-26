"""Tests pour l'AI Orchestrator"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.orchestrator.orchestrator import AIOrchestrator
from backend.agents.base import AgentContext


def test_orchestrator_initialization():
    orch = AIOrchestrator()
    assert len(orch.agents) == 10
    expected = ["query_classifier", "model_router", "security_rag",
                "threat_intelligence", "sigma_analysis", "malware_analysis",
                "incident_response", "evidence_fusion", "securityllm_synthesis",
                "ai_governance"]
    for name in expected:
        assert name in orch.agents, f"Agent {name} manquant"
    print(f"[PASS] {len(orch.agents)} agents initialises")


def test_orchestrator_workflows():
    orch = AIOrchestrator()
    assert orch.get_workflow("phishing_analysis") is not None
    assert orch.get_workflow("soc_assistance") is not None
    assert orch.get_workflow("general_security_question") is not None
    assert orch.get_workflow("nonexistent") is None
    print("[PASS] Workflows disponibles: phishing_analysis, soc_assistance, incident_response, etc.")


def test_orchestrator_full_pipeline():
    orch = AIOrchestrator()
    result = asyncio.run(orch.orchestrate(
        "Analyser ce message: Felicitations! Vous avez gagne un iPhone. Cliquez ici: http://win-now.xyz",
        user_role="analyst",
    ))
    assert "classification" in result
    assert "workflow" in result
    assert "agents_used" in result
    assert "results" in result
    assert len(result["agents_used"]) > 0
    print(f"[PASS] Pipeline: {result['classification']} -> {result['workflow']} -> {len(result['agents_used'])} agents")


def test_orchestrator_soc_pipeline():
    orch = AIOrchestrator()
    result = asyncio.run(orch.orchestrate(
        "Incident: Ransomware detection sur serveur DC-01. Chiffrement de fichiers en cours.",
        user_role="soc",
    ))
    assert result["classification"] in ("incident_response", "malware_analysis", "soc_assistance")
    assert "incident_response" in result["agents_used"]
    print(f"[PASS] SOC pipeline: {result['classification']}")


if __name__ == "__main__":
    test_orchestrator_initialization()
    test_orchestrator_workflows()
    test_orchestrator_full_pipeline()
    test_orchestrator_soc_pipeline()
    print("\n[OK] Tous les tests orchestrator passes!")
