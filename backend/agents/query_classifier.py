import re
from typing import List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult

QUERY_CATEGORIES = {
    "phishing_analysis": {
        "keywords": ["phish", "phishing", "spear", "whale", "spoof", "deceptive email",
                     "suspicious email", "malicious email", "email scam", "email fraud",
                     "paypal", "bank login", "verify account", "reset password email",
                     "urgent", "suspend", "suspendu", "bloqué", "cliquez", "compte",
                     "vérifier", "login", "identite", "identité"],
        "description": "Analyse de tentatives de phishing",
        "priority": 1,
    },
    "email_analysis": {
        "keywords": ["email", "mail", "message", "inbox", "outlook", "gmail",
                     "header", "spf", "dkim", "dmarc", "email security"],
        "description": "Analyse d'email generique",
        "priority": 1,
    },
    "malware_analysis": {
        "keywords": ["malware", "virus", "trojan", "ransomware", "worm", "rootkit",
                     "backdoor", "dropper", "loader", "shellcode", "payload",
                     "powershell -enc", "encoded command", "suspicious process",
                     "executable", "exec", "binary", "dll injection", "process hollowing"],
        "description": "Analyse de code malveillant",
        "priority": 1,
    },
    "url_analysis": {
        "keywords": ["url", "domain", "link", "http", "https", "web link", "uri",
                     "typosquat", "redirect", "shortener", "bit.ly", "tinyurl"],
        "description": "Analyse de réputation d'URL",
        "priority": 1,
    },
    "ioc_analysis": {
        "keywords": ["ioc", "indicator of compromise", "hash", "md5", "sha256", "sha1",
                     "ip address", "reputation", "misp", "blacklist", "malicious ip"],
        "description": "Analyse d'indicateurs de compromission (IOC)",
        "priority": 1,
    },
    "cve_analysis": {
        "keywords": ["cve", "vulnerability", "exploit", "cvss", "cwe", "cpe",
                     "nvd", "cisa", "kev", "zero-day", "0-day", "patch",
                     "advisory", "security bulletin"],
        "description": "Analyse de vulnerabilites et CVE",
        "priority": 2,
    },
    "sigma_analysis": {
        "keywords": ["sigma", "sigma rule", "detection rule", "rule analysis",
                     "sigma validation", "sigma conversion", "splunk query",
                     "kql", "eql", "detection logic", "correlation rule"],
        "description": "Analyse et validation de regles Sigma",
        "priority": 2,
    },
    "incident_response": {
        "keywords": ["incident", "breach", "compromise", "data leak", "data breach",
                     "intrusion", "containment", "eradication", "recovery",
                     "remediation", "playbook", "runbook"],
        "description": "Reponse a incident de securite",
        "priority": 1,
    },
    "threat_hunting": {
        "keywords": ["threat hunt", "hunting", "proactive", "ttp", "tactic",
                     "technique", "procedure", "lateral movement", "persistence",
                     "privilege escalation", "mitre att&ck"],
        "description": "Chasse aux menaces proactive",
        "priority": 2,
    },
    "log_analysis": {
        "keywords": ["log", "event log", "syslog", "sysmon", "audit", "winlog",
                     "splunk query", "kql", "elastic query", "correlation"],
        "description": "Analyse de journaux d'événements et logs",
        "priority": 2,
    },
    "kubernetes_security": {
        "keywords": ["kubernetes", "k8s", "kubectl", "pod", "namespace", "clusterrole",
                     "rolebinding", "service account", "privileged container", "hostpath",
                     "hostnetwork", "etcd", "kubelet", "calico", "cilium"],
        "description": "Sécurité des orchestrateurs conteneurs (Kubernetes/Docker)",
        "priority": 2,
    },
    "cloud_security": {
        "keywords": ["aws", "s3", "iam role", "iam policy", "access key", "secret key",
                     "cloud trail", "cloudtrail", "cloudwatch", "storage account",
                     "azure", "gcp", "bucket", "blob", "cloud security"],
        "description": "Sécurité des infrastructures cloud (AWS/Azure/GCP)",
        "priority": 2,
    },
    "devsecops_review": {
        "keywords": ["devsecops", "sast", "dast", "cicd", "ci/cd", "secret scanning",
                     "trufflehog", "gitleaks", "hardcoded", "dependency confusion",
                     "pipeline", "gitlab ci", "github actions", "jenkins"],
        "description": "Revue de sécurité CI/CD et DevSecOps",
        "priority": 2,
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
                pattern = r"(?i)\b(" + "|".join(re.escape(kw) for kw in config["keywords"]) + r")\b"
                self.patterns[category] = re.compile(pattern)

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        scores = {}

        # 1. Base keyword scoring
        for category, pattern in self.patterns.items():
            matches = pattern.findall(query)
            if matches:
                scores[category] = len(matches)

        # 2. Heuristics & Boosting rules
        query_lower = query.lower()
        
        # Boost phishing if specific keywords or domain mimicry is seen
        if "phish" in query_lower:
            scores["phishing_analysis"] = scores.get("phishing_analysis", 0) + 3
        if "email" in query_lower or "mail" in query_lower:
            scores["email_analysis"] = scores.get("email_analysis", 0) + 2
        
        # Boost URL analysis if explicit URLs or domain patterns are found
        if re.search(r"https?://", query_lower) or any(x in query_lower for x in (".xyz", ".ru", ".cn", "evil-phish")):
            scores["url_analysis"] = scores.get("url_analysis", 0) + 2
            
        # Boost CVE analysis if CVE patterns are matched
        if re.search(r"\bcve-\d{4}-\d{4,7}\b", query_lower):
            scores["cve_analysis"] = scores.get("cve_analysis", 0) + 3

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
