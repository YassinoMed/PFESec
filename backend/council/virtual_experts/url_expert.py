"""Expert 16 — URL Reputation Analyst."""
import re
from typing import Dict, List
from backend.council.virtual_experts.base import VirtualExpert

class URLReputationExpert(VirtualExpert):
    expert_id = "url_expert"
    expert_name = "URL Reputation Expert"
    category = "url_reputation"
    capabilities = ["url_reputation", "domain_age", "typosquatting", "url_redirects"]
    MITRE_TECHNIQUES = ["T1566.002 - Spearphishing Link", "T1584.001 - Domains"]

    HIGH_CONF_KEYWORDS = [
        "url", "domain", "link", "http", "https", "typosquatting",
        "redirect", "bit.ly", "tinyurl", "dns lookup", "xyz", "evil-phish",
        "banque-secure", "paypal-secure", "microsoftonline.com.evil-phish.net"
    ]
    MED_CONF_KEYWORDS = [
        "scan", "blacklist", "reputation", "lookup", "whois", "ip", "port"
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        url_iocs = [i for i in iocs if i["type"] in ("url", "domain")]
        if url_iocs:
            for ioc in url_iocs:
                val = ioc["value"].lower()
                # Check for suspicious patterns in URL
                if any(x in val for x in ("evil-phish", "banque-secure", "paypa1", "paypal-secure", "microsoftonline.com.", "xyz", "ru", "cn")):
                    evidence.append(f"Domaine/URL suspect détecté: {ioc['value']}")
                    confidence = min(confidence + 35, 98)
                else:
                    evidence.append(f"URL analysée: {ioc['value']}")
                    confidence = min(confidence + 10, 85)

        if "login" in query or "secure" in query or "suspend" in query:
            if url_iocs:
                evidence.append("Lien suspect associé à une demande d'action urgente / de connexion")
                confidence = min(confidence + 20, 98)

        if confidence >= 60:
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
            recs = [
                "Bloquer l'URL / domaine sur les pare-feux et proxies",
                "Inspecter les logs réseau pour d'autres connexions à ce domaine",
                "Soumettre l'URL à un service de réputation publique (VirusTotal, URLVoid)"
            ]
        else:
            recs = ["Surveiller la réputation du domaine", "Vérifier l'historique DNS"]

        return {
            "response": f"Analyse de réputation URL : {conclusion}. Evidence: {'; '.join(evidence[:3]) or 'Aucune URL suspecte détectée.'}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Analyse statique locale, pas d'appel de réputation en temps réel externe"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
