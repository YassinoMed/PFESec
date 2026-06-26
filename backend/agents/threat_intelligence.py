import re
import json
from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


class ThreatIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("threat_intelligence")
        self.enrichers = {
            "ip": self._enrich_ip,
            "url": self._enrich_url,
            "domain": self._enrich_domain,
            "hash": self._enrich_hash,
        }

    def _extract_iocs(self, text: str) -> Dict[str, List[str]]:
        iocs = {"ip": [], "url": [], "domain": [], "hash": []}

        ip_pattern = r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
        iocs["ip"] = list(set(re.findall(ip_pattern, text)))

        url_pattern = r"https?://[^\s<>\"']+|(?:hxxps?://[^\s<>\"']+)"
        iocs["url"] = list(set(re.findall(url_pattern, text, re.IGNORECASE)))

        domain_pattern = r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?)"
        found_domains = re.findall(domain_pattern, text)
        iocs["domain"] = list(set(d for d in found_domains if len(d) > 4 and "." in d))

        hash_pattern = r"\b(?:[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b"
        iocs["hash"] = list(set(re.findall(hash_pattern, text)))

        return iocs

    def _classify_hash(self, h: str) -> str:
        length = len(h)
        if length == 32:
            return "MD5"
        elif length == 40:
            return "SHA1"
        elif length == 64:
            return "SHA256"
        return "UNKNOWN"

    def _enrich_ip(self, ip: str) -> Dict:
        return {
            "ioc": ip,
            "type": "IP",
            "reputation": "unknown",
            "source": "local_analysis",
            "is_private": ip.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                                         "172.20.", "172.21.", "172.22.", "172.23.",
                                         "172.24.", "172.25.", "172.26.", "172.27.",
                                         "172.28.", "172.29.", "172.30.", "172.31.",
                                         "192.168.", "127.")),
            "risk_score": 50,
        }

    def _enrich_url(self, url: str) -> Dict:
        obfuscated = "hxxp" in url.lower()
        return {
            "ioc": url,
            "type": "URL",
            "obfuscated": obfuscated,
            "risk_score": 70 if obfuscated else 50,
            "source": "local_analysis",
        }

    def _enrich_domain(self, domain: str) -> Dict:
        suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".loan"]
        tld = domain[domain.rfind("."):].lower() if "." in domain else ""
        return {
            "ioc": domain,
            "type": "DOMAIN",
            "suspicious_tld": tld in suspicious_tlds,
            "risk_score": 65 if tld in suspicious_tlds else 40,
            "source": "local_analysis",
        }

    def _enrich_hash(self, h: str) -> Dict:
        return {
            "ioc": h,
            "type": "HASH",
            "hash_type": self._classify_hash(h),
            "risk_score": 50,
            "source": "local_analysis",
        }

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        iocs = self._extract_iocs(query)

        total_found = sum(len(v) for v in iocs.values())
        enrichments = {}

        for ioc_type, ioc_list in iocs.items():
            if ioc_list and ioc_type in self.enrichers:
                enrichments[ioc_type] = [self.enrichers[ioc_type](ioc) for ioc in ioc_list]

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "iocs_found": total_found,
                "iocs": {k: v for k, v in iocs.items() if v},
                "enrichments": enrichments,
                "risk_summary": self._summarize_risk(enrichments),
                "note": "Enrichissement local - sources externes desactivees (MISP, VT, AbuseIPDB)",
            },
            confidence=0.85 if total_found > 0 else 0.5,
            metadata={"ioc_counts": {k: len(v) for k, v in iocs.items()}},
        )

    def _summarize_risk(self, enrichments: Dict) -> Dict:
        scores = []
        for ioc_type, items in enrichments.items():
            for item in items:
                scores.append(item.get("risk_score", 50))
        avg = sum(scores) / max(len(scores), 1)
        max_score = max(scores) if scores else 0
        return {
            "average_risk": round(avg, 1),
            "max_risk": max_score,
            "total_iocs": len(scores),
            "assessment": "HIGH" if max_score >= 70 else ("MEDIUM" if max_score >= 40 else "LOW"),
        }
