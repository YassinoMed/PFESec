"""Expert 5 — IOC Extraction & Classification Specialist."""
import re
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert

_SUSPICIOUS_TLDS = {"xyz", "ru", "cn", "tk", "pw", "cc", "top", "club", "online", "site", "web"}
_SUSPICIOUS_DOMAINS = [
    "banque-secure", "paypal-verify", "amazon-login", "microsoft-login",
    "apple-id", "google-verify", "facebook-login", "netflix-cancel",
]


class IOCExpert(VirtualExpert):
    expert_id = "ioc_expert"
    expert_name = "IOC Specialist"
    category = "ioc_analysis"
    capabilities = ["ioc_extraction", "ioc_classification", "hash_analysis", "domain_reputation"]
    MITRE_TECHNIQUES = [
        "T1071 - Application Layer Protocol",
        "T1048 - Exfiltration Over Alternative Protocol",
    ]

    HIGH_CONF_KEYWORDS = [
        "indicator", "ioc", "hash", "md5", "sha256", "sha1", "ip address",
        "malicious domain", "c2", "botnet", "known bad",
    ]
    MED_CONF_KEYWORDS = [
        "url", "link", "domain", "ip", "address", "email", "payload", "artifact",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        iocs = self._extract_iocs(query)
        confidence = min(len(iocs) * 18 + self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS), 95.0)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # Domain reputation check (heuristic)
        suspicious_domain_hits = []
        for domain_kw in _SUSPICIOUS_DOMAINS:
            if domain_kw in query:
                suspicious_domain_hits.append(domain_kw)

        # TLD check
        suspicious_tld_hits = [tld for tld in _SUSPICIOUS_TLDS if f".{tld}" in query]

        if suspicious_domain_hits:
            evidence.append(f"Domaines à pattern malveillant: {', '.join(suspicious_domain_hits)}")
            confidence = min(confidence + 25, 95)
        if suspicious_tld_hits:
            evidence.append(f"TLD suspects: .{', .'.join(suspicious_tld_hits)}")
            confidence = min(confidence + 15, 95)

        # IOC summary
        if iocs:
            ioc_summary = {}
            for ioc in iocs:
                ioc_summary.setdefault(ioc["type"], 0)
                ioc_summary[ioc["type"]] += 1
            evidence.append(f"IOC extraits: {', '.join(f'{v} {k}' for k, v in ioc_summary.items())}")

        cve_matches = re.findall(r"CVE-\d{4}-\d{4,7}", query, re.IGNORECASE)
        if cve_matches:
            evidence.append(f"CVE référencés: {', '.join(cve_matches[:3])}")
            confidence = min(confidence + 20, 95)

        if confidence >= 50:
            conclusion = "BLOCK"
            severity = "HIGH"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
            severity = "MEDIUM"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if iocs:
            recs.append("Vérifier les IOC sur VirusTotal / OTX / Shodan")
            recs.append("Ajouter les IOC à la threat intelligence platform")
        if cve_matches:
            recs.append(f"Consulter les advisories NVD pour {cve_matches[0]}")

        return {
            "response": f"Analyse IOC: {len(iocs)} indicateur(s) extraits. Conclusion: {conclusion}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Pas d'accès aux bases de réputation en ligne"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
