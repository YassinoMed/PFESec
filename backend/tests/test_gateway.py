"""Tests pour la Security AI Gateway"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.gateway.api import SecurityAIGateway


def test_gateway_phishing_query():
    gateway = SecurityAIGateway()
    result = asyncio.run(gateway.handle_query({
        "query": "Analyse cet email: Votre compte PayPal a ete suspendu. Cliquez ici: http://paypa1-secure.xyz/verify",
        "user_role": "analyst",
    }))
    assert result.get("success", False), f"Erreur: {result.get('error', 'inconnue')}"
    assert "classification" in result
    assert "evidence" in result
    assert "response" in result
    print(f"[PASS] Phishing query classified as: {result['classification']}")
    print(f"[PASS] Agents used: {result['agents_used']}")
    print(f"[PASS] Confidence: {result['confidence']}")


def test_gateway_soc_query():
    gateway = SecurityAIGateway()
    result = asyncio.run(gateway.handle_query({
        "query": "Alerte SOC: Tentative de brute force SSH sur 192.168.1.100 avec 47 echecs en 3 minutes",
        "user_role": "soc",
    }))
    assert result.get("success", False), f"Erreur: {result.get('error', 'inconnue')}"
    assert result["classification"] in ("soc_assistance", "incident_response", "general_security_question")
    print(f"[PASS] SOC query classified as: {result['classification']}")


def test_gateway_intel_query():
    gateway = SecurityAIGateway()
    result = asyncio.run(gateway.handle_query({
        "query": "Enrichis cet IOC: 185.234.72.18 et le domaine malicious-site.xyz",
        "user_role": "analyst",
    }))
    assert result.get("success", False)
    evidence = result.get("evidence", {})
    intel_output = evidence.get("agents", {}).get("threat_intelligence", {})
    print(f"[PASS] Intel query processed: {evidence.get('summary', {})}")


def test_gateway_empty_query():
    gateway = SecurityAIGateway()
    result = asyncio.run(gateway.handle_query({"query": ""}))
    assert result.get("success") is False
    assert result.get("status") == 400
    print("[PASS] Empty query correctly rejected")


if __name__ == "__main__":
    test_gateway_phishing_query()
    test_gateway_soc_query()
    test_gateway_intel_query()
    test_gateway_empty_query()
    print("\n[OK] Tous les tests gateway passes!")
