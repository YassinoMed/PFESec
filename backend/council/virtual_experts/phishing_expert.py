"""Expert 1 — Phishing & Social Engineering Specialist."""
from typing import Dict, List
from backend.council.virtual_experts.base import VirtualExpert


class PhishingExpert(VirtualExpert):
    expert_id = "phishing_expert"
    expert_name = "Phishing Analyst"
    category = "phishing"
    capabilities = ["phishing_detection", "social_engineering", "email_fraud", "credential_harvesting"]
    MITRE_TECHNIQUES = ["T1566 - Phishing", "T1566.001 - Spearphishing Attachment", "T1566.002 - Spearphishing Link"]

    HIGH_CONF_KEYWORDS = [
        "phishing", "spearphishing", "credential", "verify your account",
        "click here", "urgent", "suspend", "vérifiez", "cliquez", "mot de passe",
        "compte suspendu", "paypal", "bank", "login", "password reset",
        "confirm your identity", "immediate action",
    ]
    MED_CONF_KEYWORDS = [
        "email", "link", "attachment", "sender", "domain", "impersonat",
        "fake", "spoofing", "suspicious", "unusual activity", "verify",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        recommendations = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        high_hits = [kw for kw in self.HIGH_CONF_KEYWORDS if kw in query]
        if high_hits:
            evidence.append(f"Indicateurs phishing détectés: {', '.join(high_hits[:5])}")

        # Urgency patterns
        urgency_words = ["urgent", "immediate", "suspend", "cliquez", "vérifiez", "immédiatement"]
        urgency_found = [w for w in urgency_words if w in query]
        if urgency_found:
            evidence.append(f"Urgence artificielle: {', '.join(urgency_found)}")
            confidence = min(confidence + 20, 95)

        # Credential harvesting
        cred_words = ["password", "mot de passe", "login", "credential", "compte", "verify your"]
        if any(w in query for w in cred_words):
            evidence.append("Demande de credentials ou informations sensibles")
            confidence = min(confidence + 15, 95)

        # Suspicious domains
        if iocs and any(i["type"] in ("url", "domain") for i in iocs):
            suspicious_iocs = [i for i in iocs if i["type"] in ("url", "domain")]
            evidence.append(f"IOC URL/Domaine suspect: {suspicious_iocs[0]['value'][:60]}")
            confidence = min(confidence + 10, 95)

        if confidence >= 60:
            conclusion = "BLOCK"
            severity = "HIGH" if confidence >= 80 else "MEDIUM"
            recommendations = [
                "Supprimer le message et bloquer l'expéditeur",
                "Vérifier si d'autres utilisateurs ont reçu le même email",
                "Réinitialiser les mots de passe si interaction avec le lien",
                "Signaler à l'équipe anti-phishing",
            ]
        elif confidence >= 30:
            conclusion = "UNKNOWN"
            severity = "LOW"
            recommendations = ["Analyser les headers email pour valider l'origine", "Soumettre à un sandbox pour analyse"]
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"
            recommendations = ["Email semble légitime — surveiller par précaution"]

        return {
            "response": f"Analyse phishing: {conclusion}. Confiance: {confidence:.0f}%. "
                        f"{'Indicateurs confirmés: ' + ', '.join(high_hits[:3]) if high_hits else 'Aucun indicateur fort.'}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Analyse statique — sans accès au serveur de phishing"] if conclusion == "BLOCK" else [],
            "recommendations": recommendations,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
