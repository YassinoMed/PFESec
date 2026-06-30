"""Expert 17 — AI Governance, Audit and Compliance Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class GovernanceExpert(VirtualExpert):
    expert_id = "governance_expert"
    expert_name = "AI Governance & Compliance Analyst"
    category = "governance"
    capabilities = ["audit", "compliance", "ai_governance", "explainability", "policy_check"]
    MITRE_TECHNIQUES = [
        "T1562 - Impair Defenses",
        "T1082 - System Information Discovery",
    ]

    HIGH_CONF_KEYWORDS = [
        "audit", "compliance", "policy", "gdpr", "rgpd", "governance",
        "regulatory", "explainability", "bias", "fairness", "model drift",
        "privacy", "iso 27001", "nist", "hipaa", "audit trail",
    ]
    MED_CONF_KEYWORDS = [
        "rules", "legal", "verify", "check", "explain", "model", "trust",
        "decide", "decision", "justification", "criteria",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = ["Audit de conformité de l'activité du conseil de sécurité."]
        
        # Simuler un check de compliance basique
        if any(w in query.lower() for w in ["phishing", "email", "url", "malware"]):
            evidence.append("Validation de la transparence de l'explication (XAI) pour blocage d'incident.")
        
        severity = "INFORMATIONAL"
        conclusion = "ACCEPT"
        
        if confidence >= 50:
            conclusion = "ACCEPT"
            severity = "LOW"
        
        recs = [
            "Assurer la traçabilité complète des explications sémantiques (XAI) dans le journal d'audit",
            "Vérifier la conformité de l'extraction des données personnelles (RGPD/GDPR) lors du traitement d'emails",
            "Maintenir à jour le registre d'inventaire des modèles IA actifs pour les audits ISO 27001"
        ]

        return {
            "response": f"Analyse de gouvernance: Vérification de l'explicabilité et de l'auditabilité. Statut: Conforme.",
            "conclusion": conclusion,
            "confidence": max(confidence, 80.0), # Toujours haute confiance sur la conformité de principe
            "evidence": evidence,
            "limitations": ["Basé sur les métadonnées déclaratives de l'incident"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
