"""Risk Assessment Engine — Calculates composite risk score based on fused evidence.

Produces severity, probability, impact, criticality, and priority scores.
Uses a CVSS-inspired scoring model adapted for AI SOC analysis.
"""

from typing import Dict, List, Optional

from backend.council.types import ExpertAnalysis, RiskAssessment


# ── Severity Thresholds ──────────────────────────────────────────────────────

_SEVERITY_MAP = [
    (90.0, "CRITICAL", 9.5, 1),
    (75.0, "HIGH", 7.5, 2),
    (50.0, "MEDIUM", 5.0, 3),
    (25.0, "LOW", 2.5, 4),
    (0.0, "INFORMATIONAL", 1.0, 5),
]

_IMPACT_KEYWORDS = {
    "CRITICAL": ["ransom", "encrypt", "wipe", "destroy", "shutdown", "critical infrastructure"],
    "HIGH": ["exfiltrate", "data breach", "credential", "backdoor", "lateral movement", "admin", "root"],
    "MEDIUM": ["phishing", "malware", "trojan", "unauthorized access", "compromise"],
    "LOW": ["reconnaissance", "scan", "probe", "suspicious", "anomaly"],
}

_ASSET_KEYWORDS = {
    "email_server": ["email", "smtp", "imap", "exchange", "outlook", "mail server"],
    "active_directory": ["active directory", "ldap", "kerberos", "domain controller", "ad"],
    "web_application": ["web", "http", "url", "browser", "injection", "xss", "sqli"],
    "endpoint": ["workstation", "laptop", "desktop", "endpoint", "host", "user machine"],
    "cloud_infrastructure": ["aws", "azure", "gcp", "s3", "cloud", "bucket"],
    "kubernetes_cluster": ["kubernetes", "k8s", "pod", "container", "docker"],
    "database": ["database", "sql", "mongo", "redis", "postgresql", "mysql"],
    "network_device": ["router", "switch", "firewall", "vpn", "network"],
    "ci_cd_pipeline": ["ci/cd", "jenkins", "github actions", "pipeline", "artifact"],
}


class RiskAssessmentEngine:
    """
    Produces a structured risk assessment from aggregated expert analyses.
    Scores are computed algorithmically — no raw model internals exposed.
    """

    def assess(
        self,
        query: str,
        classification: str,
        analyses: List[ExpertAnalysis],
        consensus_score: float,
    ) -> RiskAssessment:
        corpus = self._build_corpus(query, analyses)

        # Compute component scores
        avg_confidence = self._average_confidence(analyses)
        impact_str, impact_score = self._assess_impact(corpus)
        probability = self._assess_probability(avg_confidence, consensus_score, corpus)
        severity_str, severity_score, priority = self._assess_severity(consensus_score, probability, impact_score)
        criticality = self._assess_criticality(severity_str, impact_str)
        risk_score = self._compute_risk_score(probability, impact_score, consensus_score)
        affected_assets = self._identify_assets(corpus)
        business_impact = self._describe_business_impact(severity_str, impact_str, classification)
        technical_impact = self._describe_technical_impact(corpus, impact_str)
        cvss_vector = self._build_cvss_like_vector(corpus, probability, impact_score)
        exploitability = self._assess_exploitability(corpus, probability)

        return RiskAssessment(
            severity=severity_str,
            severity_score=severity_score,
            probability=probability,
            impact=impact_str,
            impact_score=impact_score,
            criticality=criticality,
            priority=priority,
            risk_score=risk_score,
            affected_assets=affected_assets,
            business_impact=business_impact,
            technical_impact=technical_impact,
            cvss_vector=cvss_vector,
            exploitability=exploitability,
        )

    # ── Internal helpers ──────────────────────────────────────────────────

    def _build_corpus(self, query: str, analyses: List[ExpertAnalysis]) -> str:
        parts = [query.lower()]
        for a in analyses:
            if a.response:
                parts.append(str(a.response).lower())
            parts.extend(e.lower() for e in a.evidence)
            parts.extend(r.lower() for r in a.recommendations)
        return " ".join(parts)

    def _average_confidence(self, analyses: List[ExpertAnalysis]) -> float:
        completed = [a for a in analyses if a.status == "completed" and a.confidence > 0]
        if not completed:
            return 0.0
        return sum(a.confidence for a in completed) / len(completed)

    def _assess_impact(self, corpus: str) -> tuple:
        for level, keywords in _IMPACT_KEYWORDS.items():
            if any(kw in corpus for kw in keywords):
                score_map = {"CRITICAL": 9.8, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 2.5}
                return level, score_map[level]
        return "LOW", 2.0

    def _assess_probability(
        self, avg_confidence: float, consensus_score: float, corpus: str
    ) -> float:
        base = (avg_confidence + consensus_score) / 2.0
        # boost if strong IOC evidence
        if any(kw in corpus for kw in ["cve-", "exploit", "confirmed", "detected"]):
            base = min(base * 1.1, 100.0)
        return round(base, 2)

    def _assess_severity(
        self, consensus_score: float, probability: float, impact_score: float
    ) -> tuple:
        composite = (consensus_score * 0.4 + probability * 0.3 + impact_score * 10 * 0.3)
        for threshold, label, score, priority in _SEVERITY_MAP:
            if composite >= threshold:
                return label, score, priority
        return "INFORMATIONAL", 1.0, 5

    def _assess_criticality(self, severity: str, impact: str) -> str:
        if severity == "CRITICAL" or impact == "CRITICAL":
            return "CRITICAL — Immediate response required"
        if severity == "HIGH" or impact == "HIGH":
            return "HIGH — Response within 1 hour"
        if severity == "MEDIUM":
            return "MEDIUM — Response within 4 hours"
        return "LOW — Standard response process"

    def _compute_risk_score(
        self, probability: float, impact_score: float, consensus_score: float
    ) -> float:
        # RISK = (P × I × C) / normalization
        return round(min((probability / 100.0) * impact_score * 10 * (consensus_score / 100.0), 100.0), 2)

    def _identify_assets(self, corpus: str) -> List[str]:
        assets = []
        for asset, keywords in _ASSET_KEYWORDS.items():
            if any(kw in corpus for kw in keywords):
                assets.append(asset.replace("_", " ").title())
        return assets or ["Unknown / Undetermined"]

    def _describe_business_impact(self, severity: str, impact: str, classification: str) -> str:
        if severity == "CRITICAL":
            return "Service disruption possible. Data loss risk. Regulatory exposure (GDPR, NIS2). Reputational damage."
        if severity == "HIGH":
            return "Potential unauthorized data access. Customer impact possible. Incident notification may be required."
        if severity == "MEDIUM":
            return "Limited business disruption. Internal investigation required. No immediate external notification needed."
        return "Minimal business impact. Monitoring and tracking recommended."

    def _describe_technical_impact(self, corpus: str, impact: str) -> str:
        parts = []
        if "credential" in corpus or "password" in corpus:
            parts.append("Credential compromise → authentication bypass risk")
        if "lateral" in corpus:
            parts.append("Lateral movement → internal network exposure")
        if "exfiltrate" in corpus:
            parts.append("Data exfiltration → confidentiality breach")
        if "encrypt" in corpus or "ransom" in corpus:
            parts.append("File encryption → availability disruption")
        if "backdoor" in corpus:
            parts.append("Persistent backdoor → long-term compromise")
        if not parts:
            parts.append("Initial access attempt — scope limited to initial vector")
        return "; ".join(parts)

    def _build_cvss_like_vector(
        self, corpus: str, probability: float, impact_score: float
    ) -> str:
        # Simplified CVSS-like vector string
        av = "N" if any(kw in corpus for kw in ["email", "url", "network"]) else "L"
        ac = "L" if probability > 60 else "H"
        pr = "N" if "unauthenticated" in corpus or "phishing" in corpus else "L"
        ui = "R" if "click" in corpus or "open" in corpus or "user" in corpus else "N"
        s = "C" if "lateral" in corpus else "U"
        ci = "H" if impact_score >= 7 else "L"
        ii = "H" if impact_score >= 7 else "L"
        ai = "H" if "dos" in corpus or "encrypt" in corpus else "L"
        return f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{ci}/I:{ii}/A:{ai}"

    def _assess_exploitability(self, corpus: str, probability: float) -> str:
        if probability >= 80 and any(kw in corpus for kw in ["exploit", "cve", "0-day", "zero-day"]):
            return "HIGH — Active exploitation evidence"
        if probability >= 60:
            return "MEDIUM — Likely exploitation attempt"
        if probability >= 30:
            return "LOW — Potential exploitation vector"
        return "VERY LOW — No clear exploitation indicators"
