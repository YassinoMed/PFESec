"""Expert 2 — Email Header & Protocol Analysis Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class EmailHeaderExpert(VirtualExpert):
    expert_id = "email_header_expert"
    expert_name = "Email Protocol Analyst"
    category = "email_security"
    capabilities = ["spf_dkim_dmarc", "email_headers", "sender_analysis", "email_authentication"]
    MITRE_TECHNIQUES = ["T1566 - Phishing", "T1534 - Internal Spearphishing"]

    HIGH_CONF_KEYWORDS = [
        "dmarc fail", "spf fail", "dkim fail", "no-reply", "noreply",
        "spoofed", "forged", "header", "from:", "reply-to:", "return-path:",
        "x-mailer", "x-originating", "received:", "envelope-from",
    ]
    MED_CONF_KEYWORDS = [
        "email", "smtp", "imap", "outlook", "gmail", "mail", "sender",
        "recipient", "subject", "body", "attachment", "inbox",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        if "dmarc" in query:
            if "fail" in query or "none" in query:
                evidence.append("DMARC: politique défaillante — risque de spoofing")
                confidence = min(confidence + 20, 95)
        if "spf" in query and "fail" in query:
            evidence.append("SPF: echec de validation — expéditeur non autorisé")
            confidence = min(confidence + 20, 95)
        if "dkim" in query and "fail" in query:
            evidence.append("DKIM: signature invalide — email potentiellement altéré")
            confidence = min(confidence + 20, 95)

        email_iocs = [i for i in iocs if i["type"] == "email"]
        if email_iocs:
            evidence.append(f"Adresse email suspecte: {email_iocs[0]['value']}")

        if confidence >= 55:
            conclusion = "BLOCK"
            severity = "HIGH"
        elif confidence >= 25:
            conclusion = "UNKNOWN"
            severity = "MEDIUM"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if conclusion == "BLOCK":
            recs = ["Vérifier la configuration DMARC du domaine expéditeur",
                    "Mettre à jour les règles SPF/DKIM", "Bloquer le domaine si spoofing confirmé"]
        elif "email" in query:
            recs = ["Analyser les en-têtes complets de l'email", "Vérifier les enregistrements DNS du domaine"]

        return {
            "response": f"Analyse protocolaire email: {conclusion}. Evidence: {'; '.join(evidence[:3]) or 'Insuffisante pour analyse header.'}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Analyse sans accès aux en-têtes bruts complets"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
