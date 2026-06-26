import re
from typing import List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


QUERY_CATEGORIES = {
    "phishing_analysis": {
        "keywords": ["phish", "phishing", "spear", "whale", "spoof", "deceptive email",
                     "suspicious email", "malicious email", "email scam", "email fraud",
                     "paypal", "bank login", "verify account", "reset password email"],
        "description": "Analyse de tentatives de phishing",
        "priority": 1,
    },
    "email_analysis": {
        "keywords": ["email", "mail", "message", "inbox", "outlook", "gmail",
                     "header", "spf", "dkim", "dmarc", "email security"],
        "description": "Analyse d'email generique",
        "priority": 2,
    },
    "malware_analysis": {
        "keywords": ["malware", "virus", "trojan", "ransomware", "worm", "rootkit",
                     "backdoor", "dropper", "loader", "shellcode", "payload",
                     "powershell -enc", "encoded command", "suspicious process"],
        "description": "Analyse de code malveillant",
        "priority": 1,
    },
    "incident_response": {
        "keywords": ["incident", "breach", "compromise", "data leak", "data breach",
                     "intrusion", "containment", "eradication", "recovery",
                     "remediation", "playbook", "runbook"],
        "description": "Reponse a incident de securite",
        "priority": 1,
    },
    "threat_hunting": {
        "keywords": ["threat hunt", "hunting", "proactive", "ioc", "indicator",
                     "ttp", "tactic", "technique", "procedure", "lateral movement",
                     "persistence", "privilege escalation"],
        "description": "Chasse aux menaces proactive",
        "priority": 2,
    },
    "sigma_analysis": {
        "keywords": ["sigma", "sigma rule", "detection rule", "rule analysis",
                     "sigma validation", "sigma conversion", "splunk query",
                     "kql", "eql", "detection logic"],
        "description": "Analyse et validation de regles Sigma",
        "priority": 2,
    },
    "threat_intelligence": {
        "keywords": ["threat intel", "threat intelligence", "cti", "ioc enrichment",
                     "ip reputation", "domain reputation", "hash lookup",
                     "url scan", "osint", "dark web", "feeds", "ttp"],
        "description": "Renseignement sur les menaces",
        "priority": 2,
    },
    "cve_analysis": {
        "keywords": ["cve", "vulnerability", "exploit", "cvss", "cwe", "cpe",
                     "nvd", "cisa", "kev", "zero-day", "0-day", "patch",
                     "advisory", "security bulletin"],
        "description": "Analyse de vulnerabilites et CVE",
        "priority": 2,
    },
    "vulnerability_assessment": {
        "keywords": ["vulnerability assessment", "vuln scan", "pentest",
                     "penetration test", "security assessment", "risk assessment",
                     "finding", "remediation", "compliance", "audit"],
        "description": "Evaluation de vulnerabilites",
        "priority": 3,
    },
    "soc_assistance": {
        "keywords": ["soc", "alert", "triage", "ticket", "case", "analyst",
                     "investigation", "log analysis", "correlation", "siem",
                     "edr", "xdr", "mdr", "security operation"],
        "description": "Assistance analyste SOC",
        "priority": 1,
    },
    "rag_question": {
        "keywords": ["mitre", "att&ck", "attck", "nist", "owasp", "framework",
                     "standard", "best practice", "guideline", "regulation",
                     "gdpr", "hipaa", "pci", "iso 27001", "soc 2"],
        "description": "Question base de connaissances securite",
        "priority": 3,
    },
    "general_security_question": {
        "keywords": [],
        "description": "Question securite generale",
        "priority": 4,
    },
}


class QueryClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("query_classifier")
        self._compile_patterns()

    def _compile_patterns(self):
        self.patterns = {}
        for category, config in QUERY_CATEGORIES.items():
            if config["keywords"]:
                pattern = r"(?i)(" + "|".join(re.escape(kw) for kw in config["keywords"]) + ")"
                self.patterns[category] = re.compile(pattern)

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        scores = {}

        for category, pattern in self.patterns.items():
            matches = pattern.findall(query)
            if matches:
                scores[category] = len(matches)

        if not scores:
            scores["general_security_question"] = 1

        ranked = sorted(scores.items(), key=lambda x: (-x[1], QUERY_CATEGORIES[x[0]]["priority"]))
        primary = ranked[0][0]
        alternatives = [c for c, _ in ranked[1:]]

        confidence = min(0.5 + 0.1 * ranked[0][1], 0.99)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "primary_category": primary,
                "categories": ranked,
                "alternatives": alternatives,
                "description": QUERY_CATEGORIES[primary]["description"],
                "all_scores": scores,
            },
            confidence=confidence,
            metadata={"pattern_matches": {c: s for c, s in scores.items()}},
        )
