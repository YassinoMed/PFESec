"""Tests pour les corrections P2 — T04, T05, T07, T09, T10, T72 + BONUS anti-deadlock."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class MockRegistry:
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


def run(coro):
    return asyncio.run(coro)


def test_t04_empty_artifact():
    """T04: Artefact vide → ERREUR_INPUT immédiat."""
    orch = get_orchestrator()
    result = run(orch.run(query="", user_role="analyst"))
    assert result.classification == "ERREUR_INPUT"
    assert result.final_response["conclusion"] == "ERREUR_INPUT"
    assert result.selected_models == []
    assert result.metrics["experts_total"] == 0
    print("  [PASS] T04: empty_artifact")


def test_t04_none_artifact():
    """T04: Artefact None → ERREUR_INPUT."""
    orch = get_orchestrator()
    result = run(orch.run(query=None, user_role="analyst"))
    assert result.classification == "ERREUR_INPUT"
    assert result.final_response["conclusion"] == "ERREUR_INPUT"
    print("  [PASS] T04: none_artifact")


def test_t05_arabic_phishing():
    """T05: Email en arabe → détection langue + classification phishing."""
    from backend.agents.query_classifier import QueryClassifierAgent
    from backend.agents.base import AgentContext
    agent = QueryClassifierAgent()
    query = "مرحبا، يرجى التحقق من حسابك البنكي على الرابط التالي : http://alrajhi-verify-secure.net/login"
    lang = agent._detect_language(query)
    assert lang == "AR", f"Langue non détectée: {lang}"
    ctx = AgentContext(query=query)
    result = run(agent.execute(ctx))
    assert result.success
    # Doit passer le filtre CYBER_KEYWORDS (URL présent)
    assert result.output["primary_category"] != "HORS_DOMAINE"
    print(f"  [PASS] T05: arabic_phishing — langue={lang}, classification={result.output['primary_category']}")


def test_t07_double_extension():
    """T07: Pièce jointe avec double extension → détection + scorification."""
    from backend.council.virtual_experts.email_expert import _extract_all_urls, _score_url
    orch = get_orchestrator()
    query = "Veuillez signer le document en PJ. Fichier : contrat.pdf.exe (2.3 MB)"
    # Test detector directly
    info = orch._detect_attachment(query)
    assert info["detected"], "Pièce jointe non détectée"
    assert any("contrat.pdf" in f for f in info["filenames"]), f"Fichier non trouvé dans {info['filenames']}"
    assert info["double_extension"], "Double extension non détectée"
    print(f"  [PASS] T07: double_extension — fichiers={info['filenames']}, double_ext={info['double_extension']}")


def test_t09_multi_url():
    """T09: Email avec 2 URLs → les deux sont extraites et analysées."""
    from backend.council.virtual_experts.email_expert import _extract_all_urls, _score_url
    query = "Votre colis est disponible sur http://tracking-dhl.xyz/abc et confirmez sur http://dhl-livraison.net/confirm"
    urls = _extract_all_urls(query)
    assert len(urls) == 2, f"Attendu 2 URLs, obtenu {len(urls)}: {urls}"
    scores = [_score_url(u)["score_risque"] for u in urls]
    global_score = max(scores)
    assert global_score >= 0
    print(f"  [PASS] T09: multi_url — {len(urls)} URLs extraites, score max={global_score}")


def test_t10_spearphishing_microsoft():
    """T10: Spearphishing par usurpation Microsoft."""
    from backend.council.virtual_experts.email_expert import _extract_sender_domain, _detect_spearphishing, _extract_all_urls, _score_url
    query = """From: support@microsoftsupport-fr.com
Subject: Votre compte Microsoft 365 sera désactivé dans 24h
Body: Cliquez ici pour vérifier : http://ms365-verify.xyz/login"""
    sender_domain = _extract_sender_domain(query)
    assert sender_domain == "microsoftsupport-fr.com"
    urls = _extract_all_urls(query)
    url_details = [_score_url(u) for u in urls]
    is_spear, bonus, signals = _detect_spearphishing(sender_domain, query, url_details)
    assert is_spear, f"Spearphishing non détecté: {signals}"
    assert bonus >= 85.0, f"Bonus trop faible: {bonus}"
    signal_texts = " ".join(signals)
    assert "marque" in signal_texts or "Microsoft" in signal_texts or "similarité" in signal_texts
    print(f"  [PASS] T10: spearphishing — signals={len(signals)}, bonus={bonus:.0f}%")


def test_t72_short_email():
    """T72: Email court sans indicateurs → calibration appliquée."""
    from backend.council.virtual_experts.email_expert import _calibrate_short_email
    query = "Bonjour, rappeler le 06XXXXXXXX"
    confidence, verdict, needs_escalation, calib = _calibrate_short_email(query, 80.0)
    assert calib["calibration_appliquee"], "Calibration non appliquée"
    assert calib["confiance_plafonnee_a"] <= 45.0, f"Plafond trop haut: {calib['confiance_plafonnee_a']}"
    assert verdict == "INCONCLUSIVE"
    assert needs_escalation
    print(f"  [PASS] T72: short_email — confiance plafonnée à {calib['confiance_plafonnee_a']}%")


def test_bonus_anti_deadlock():
    """BONUS: Anti-deadlock — vérification logique pipeline phishing sans models explicites."""
    orch = get_orchestrator()
    # Appel sans models explicites → anti-deadlock doit ajouter un 3e expert
    query = ("URGENT: Votre compte bancaire a été suspendu suite à une activité suspecte. "
             "Veuillez vérifier vos informations en cliquant sur le lien ci-dessous pour éviter "
             "la fermeture définitive de votre compte. Merci de votre compréhension. "
             "Lien de vérification: http://banque-secure.xyz/login")
    result = run(orch.run(query=query, user_role="analyst"))
    # Au moins 3 experts sélectionnés
    assert len(result.selected_models) >= 3, f"Anti-deadlock: {len(result.selected_models)} experts: {result.selected_models}"
    print(f"  [PASS] BONUS: anti_deadlock — {len(result.selected_models)} experts: {result.selected_models}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Corrections P2 — Tests de validation")
    print("=" * 70 + "\n")

    tests = [
        ("T04 — Artefact vide", test_t04_empty_artifact),
        ("T04 — Artefact None", test_t04_none_artifact),
        ("T05 — Email en arabe", test_t05_arabic_phishing),
        ("T07 — Double extension PJ", test_t07_double_extension),
        ("T09 — Multi-URL", test_t09_multi_url),
        ("T10 — Spearphishing Microsoft", test_t10_spearphishing_microsoft),
        ("T72 — Email court", test_t72_short_email),
        ("BONUS — Anti-deadlock", test_bonus_anti_deadlock),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  [FAIL] {name} — {e}")
            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print(f"  P2 Results: {passed} passed, {len(tests) - passed} failed / {len(tests)} total")
    print(f"{'=' * 70}\n")
    sys.exit(0 if passed == len(tests) else 1)
