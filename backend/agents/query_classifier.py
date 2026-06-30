import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.base import BaseAgent, AgentContext, AgentResult

# ── Bloc 2 — Liste de référence des mots-clés cybersécurité (T32) ────────────

CYBER_KEYWORDS: List[str] = [
    "ioc", "cve", "malware", "phishing", "intrusion", "vulnerabilite",
    "vulnerability", "firewall", "siem", "incident", "exploit", "payload",
    "hash", "adresse ip", "domaine suspect", "alerte", "ransomware",
    "authentification", "chiffrement", "pentest", "cti", "soc",
    "apt", "zero-day", "patch", "credential", "token", "certificate",
    "log", "alert", "eventid", "sigma", "mitre", "att&ck", "sandbox",
    "reverse shell", "beacon", "c2", "exfiltration", "lateral movement",
    "spoof", "spearphishing", "whale", "virus", "trojan", "worm",
    "rootkit", "backdoor", "dropper", "shellcode", "powershell",
    "suspicious", "malicious", "blocked", "attack", "threat",
    "compromis", "compromission", "securite", "security",
    "mot de passe", "password", "login", "compte", "account",
    "bloque", "suspendu", "verifier", "verify",
    "ip", "url", "domain", "dns", "http", "https", "tcp", "udp",
    "botnet", "ddos", "phish", "scan", "brute force",
    "privilege escalation", "persistence", "defense evasion",
    "credential access", "discovery", "lateral movement",
    "collection", "command and control", "exfiltration", "impact",
    "snort", "suricata", "splunk", "qradar", "elastic",
    "kubernetes", "k8s", "docker", "container", "pod",
    "aws", "azure", "gcp", "cloud", "s3", "iam",
    "firewall", "proxy", "vpn", "ssh", "ssl", "tls",
    "EventID", "src_ip", "dst_ip", "rule_name", "alert_id",
    "severity", "timestamp", "process_name", "CommandLine",
    "failed login", "authentication failure",
    "payload", "shellcode", "encoded",
    "typosquat", "shortener", "bit.ly", "tinyurl",
]

# ── Bloc 2 — Étape 3: Signaux de détection SIEM (T31) ──────────────────────

SIEM_CHAMPS_STRUCTURES: List[str] = [
    "timestamp", "severity", "src_ip", "dst_ip",
    "port", "protocol", "action", "user", "host",
    "process_name", "CommandLine", "EventID",
    "alert_id", "rule_name", "signature", "LogLevel",
]

SIEM_FORMATS: List[str] = [
    "json", "cef", "leef", "syslog", "w3c",
    "windows event log", "elastic common schema",
]

SIEM_KEYWORDS: List[str] = [
    "EventID", "alert_id", "rule_name",
    "Suricata", "Snort", "Splunk", "QRadar",
    "Elastic", "failed login", "authentication failure",
    "brute force", "port scan",
]

SIEM_PATTERN_TIMESTAMP: re.Pattern = re.compile(
    r"\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}"
)

# ── Bloc 2 — Catégories de classification ───────────────────────────────────

QUERY_CATEGORIES = {
    "phishing_analysis": {
        "keywords": ["phish", "spear", "whale", "spoof", "deceptive email",
                     "suspicious email", "malicious email", "email scam",
                     "paypal", "bank login", "reset password",
                     "urgent", "suspend", "suspendu", "bloqué", "cliquez",
                     "compte", "vérifier", "login", "identite", "identité"],
        "description": "Analyse de tentatives de phishing",
        "priority": 1,
    },
    "email_analysis": {
        "keywords": ["email", "mail", "message", "inbox", "outlook", "gmail",
                     "header", "spf", "dkim", "dmarc"],
        "description": "Analyse d'email générique",
        "priority": 1,
    },
    "malware_analysis": {
        "keywords": ["malware", "virus", "trojan", "ransomware", "worm",
                     "rootkit", "backdoor", "dropper", "loader", "shellcode",
                     "payload", "powershell -enc", "encoded command",
                     "suspicious process", "executable", "exec", "binary",
                     "dll injection", "process hollowing"],
        "description": "Analyse de code malveillant",
        "priority": 1,
    },
    "url_analysis": {
        "keywords": ["url", "domain", "link", "http", "https", "web link",
                     "uri", "typosquat", "redirect", "shortener",
                     "bit.ly", "tinyurl"],
        "description": "Analyse de réputation d'URL",
        "priority": 1,
    },
    "ioc_analysis": {
        "keywords": ["ioc", "indicator of compromise", "hash", "md5", "sha256",
                     "sha1", "ip address", "reputation", "misp", "blacklist",
                     "malicious ip"],
        "description": "Analyse d'indicateurs de compromission (IOC)",
        "priority": 1,
    },
    "cve_analysis": {
        "keywords": ["cve", "vulnerability", "exploit", "cvss", "cwe", "cpe",
                     "nvd", "cisa", "kev", "zero-day", "0-day", "patch",
                     "advisory", "security bulletin"],
        "description": "Analyse de vulnérabilités et CVE",
        "priority": 2,
    },
    "siem_investigation": {
        "keywords": SIEM_KEYWORDS,
        "description": "Analyse d'alertes SIEM, logs réseau, événements de sécurité structurés",
        "priority": 1,
    },
    "incident_active": {
        "keywords": ["incident en cours", "compromis", "compromission", "breach",
                     "intrusion active", "ransomware actif", "exfiltration en cours",
                     "lateral movement detecte", "active threat", "attaque en cours",
                     "intrusion en cours", "incident actif", "cyberattaque en cours",
                     "critical security", "response immediate"],
        "description": "Incident de sécurité en cours nécessitant une réponse immédiate",
        "priority": 1,
    },
    "general_security_question": {
        "keywords": [],
        "description": "Question sécurité générale",
        "priority": 4,
    },
}


class QueryClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("query_classifier")
        self._compile_patterns()

    def _compile_patterns(self):
        self.keyword_patterns = {}
        for category, config in QUERY_CATEGORIES.items():
            if config["keywords"]:
                pattern = r"(?i)\b(" + "|".join(re.escape(kw) for kw in config["keywords"]) + r")\b"
                self.keyword_patterns[category] = re.compile(pattern)

    def _detect_language(self, query: str) -> str:
        """T05: Détection de la langue dominante par analyse Unicode."""
        arabic_chars = sum(1 for c in query if '\u0600' <= c <= '\u06FF')
        chinese_chars = sum(1 for c in query if '\u4E00' <= c <= '\u9FFF')
        latin_chars = sum(1 for c in query if '\u0041' <= c <= '\u024F')
        total = len(query)
        if total == 0:
            return "UNKNOWN"
        ratio_ar = arabic_chars / total
        ratio_zh = chinese_chars / total
        ratio_la = latin_chars / total
        if ratio_ar > 0.30:
            return "AR"
        if ratio_zh > 0.20:
            return "ZH"
        if ratio_la > 0.50:
            return "EN"
        return "UNKNOWN"

    def _has_cyber_keywords(self, query_lower: str) -> bool:
        """Bloc 2 — Étape 1 (T32): Vérifie si la requête contient des mots-clés cybersécurité."""
        for kw in CYBER_KEYWORDS:
            if kw in query_lower:
                return True
        return False

    def _has_email_headers(self, query: str) -> bool:
        """Détecte les en-têtes email (From:, To:, Subject:, Received:)."""
        return bool(re.search(r'(?im)^(?:from|to|subject|received|reply-to|return-path|envelope-from)\s*:', query))

    def _count_urls(self, query: str) -> int:
        """Compte les URLs dans la requête."""
        return len(re.findall(r'https?://[^\s<>"\'\]\)]+', query))

    def _count_words(self, query: str) -> int:
        """Compte les mots dans la requête."""
        return len(query.split())

    def _is_log_format(self, query: str) -> bool:
        """Détecte si la requête ressemble à un format structuré (JSON, log, etc.)."""
        # JSON detection
        stripped = query.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or \
           (stripped.startswith("[") and stripped.endswith("]")):
            try:
                json.loads(stripped)
                return True
            except (json.JSONDecodeError, ValueError):
                pass
        # CEF/LEEF format: contains key=value pairs
        if re.search(r'\b\w+=\w+.*\b\w+=\w+', query):
            return True
        return False

    def _detect_siem_signals(self, query: str, query_lower: str) -> int:
        """Bloc 2 — Étape 3 (T31): Compte les signaux SIEM."""
        signals = 0
        # Champs structurés
        for field in SIEM_CHAMPS_STRUCTURES:
            if re.search(r'\b' + re.escape(field) + r'\b', query_lower):
                signals += 1

        # Formats reconnus
        if self._is_log_format(query):
            signals += 1

        # Mots-clés SIEM
        for kw in SIEM_KEYWORDS:
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', query_lower):
                signals += 1

        # Patterns temporels (timestamp + IP + action)
        if SIEM_PATTERN_TIMESTAMP.search(query):
            if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', query):  # IP
                signals += 1
                if re.search(r'\b(?:blocked|allowed|denied|failed|success|dropped|rejected)\b', query_lower):
                    signals += 1

        return signals

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        query_lower = query.lower()
        lang = self._detect_language(query)
        word_count = self._count_words(query)
        url_count = self._count_urls(query)
        has_headers = self._has_email_headers(query)
        is_log = self._is_log_format(query)

        # ── Bloc 2 — Étape 1 (T32): DÉTECTION HORS DOMAINE ──────────────
        if not self._has_cyber_keywords(query_lower):
            return AgentResult(
                agent_name=self.name,
                success=True,
                output={
                    "primary_category": "HORS_DOMAINE",
                    "description": "Requête hors domaine cybersécurité",
                    "all_scores": {},
                },
                confidence=0.0,
                metadata={"out_of_scope": True,
                          "audit": {
                              "type": "OUT_OF_SCOPE",
                              "input_hash": hashlib.sha256(query.encode()).hexdigest(),
                              "timestamp": datetime.utcnow().isoformat(),
                          }},
            )

        # ── Bloc 2 — Étape 2: ARBRE DE DÉCISION (T28) ──────────────────
        classification = None
        confidence = 0.5

        # 1. Contient en-têtes email ? → phishing_analysis
        if has_headers:
            classification = "phishing_analysis"
            confidence = 0.85
        # 2. Corps message (>= 20 mots) + URL ? → phishing_analysis
        elif word_count >= 20 and url_count >= 1:
            classification = "phishing_analysis"
            confidence = 0.80
        # 3. URL seule sans contexte email ? → url_analysis
        elif url_count >= 1 and not has_headers:
            classification = "url_analysis"
            confidence = 0.75
        # 4. Hash MD5/SHA1/SHA256 ou IP isolée ? → ioc_analysis
        elif re.search(r'\b[a-f0-9]{32}\b|\b[a-f0-9]{40}\b|\b[a-f0-9]{64}\b', query_lower):
            classification = "ioc_analysis"
            confidence = 0.85
        elif re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', query) and url_count == 0 and not has_headers:
            # IP isolée sans URL ni email
            if word_count < 15:
                classification = "ioc_analysis"
                confidence = 0.80
        # 5. CVE-XXXX-XXXXX ? → cve_analysis
        if classification is None and re.search(r'\bcve-\d{4}-\d{4,7}\b', query_lower):
            classification = "cve_analysis"
            confidence = 0.85
        # 6. Log structuré ? (évalué par l'étape 3 après l'arbre)
        # 7. Signaux incident actif ? → incident_active
        if classification is None:
            incident_keywords = QUERY_CATEGORIES["incident_active"]["keywords"]
            incident_matches = sum(1 for kw in incident_keywords if kw in query_lower)
            if incident_matches >= 1:
                # Boost si urgence + compromis
                has_urgency = bool(re.search(r'(urgent|critique|immediat|active|en cours)', query_lower))
                has_compromise = any(w in query_lower for w in ["compromis", "ransomware", "breach", "exfiltration"])
                if has_urgency and has_compromise:
                    classification = "incident_active"
                    confidence = 0.85
        # 8. Binaire ou code malveillant ? → malware_analysis
        if classification is None:
            malware_keywords = QUERY_CATEGORIES["malware_analysis"]["keywords"]
            malware_matches = sum(1 for kw in malware_keywords if kw in query_lower)
            if malware_matches >= 2:
                classification = "malware_analysis"
                confidence = 0.75
        # 9. Kubernetes / pod / RBAC ? → kubernetes_incident
        if classification is None:
            k8s_keywords = QUERY_CATEGORIES.get("kubernetes_security", {}).get("keywords", [])
            k8s_matches = sum(1 for kw in k8s_keywords if kw in query_lower)
            if k8s_matches >= 1:
                classification = "kubernetes_incident"
                confidence = 0.75
        # 10. AWS / Azure / GCP + incident ? → cloud_incident
        if classification is None:
            cloud_keywords = QUERY_CATEGORIES.get("cloud_security", {}).get("keywords", [])
            cloud_matches = sum(1 for kw in cloud_keywords if kw in query_lower)
            if cloud_matches >= 1:
                classification = "cloud_incident"
                confidence = 0.70
        # 11. Domaine seul ? → ioc_analysis
        if classification is None:
            if re.search(r'\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.[a-z]{2,}\b', query_lower) and word_count < 10:
                classification = "ioc_analysis"
                confidence = 0.70

        # ── Bloc 2 — Étape 3 (T31): DÉTECTION LOG / SIEM ──────────────
        siem_signals = self._detect_siem_signals(query, query_lower)
        if siem_signals >= 2:
            classification = "siem_investigation"
            confidence = min(0.70 + 0.05 * siem_signals, 0.95)

        # ── Fallback: keyword scoring ──────────────────────────────────
        if classification is None:
            scores = {}
            for category, pattern in self.keyword_patterns.items():
                matches = pattern.findall(query)
                if matches:
                    scores[category] = len(matches)

            if "phish" in query_lower:
                scores["phishing_analysis"] = scores.get("phishing_analysis", 0) + 3
            if "email" in query_lower or "mail" in query_lower:
                scores["email_analysis"] = scores.get("email_analysis", 0) + 2

            if re.search(r"https?://", query_lower):
                scores["url_analysis"] = scores.get("url_analysis", 0) + 2

            if re.search(r"\bcve-\d{4}-\d{4,7}\b", query_lower):
                scores["cve_analysis"] = scores.get("cve_analysis", 0) + 3

            if re.search(r"\b[a-f0-9]{32}\b", query_lower) or \
               re.search(r"\b[a-f0-9]{40}\b", query_lower) or \
               re.search(r"\b[a-f0-9]{64}\b", query_lower):
                scores["ioc_analysis"] = scores.get("ioc_analysis", 0) + 3

            if not scores:
                classification = "general_security_question"
                confidence = 0.50
            else:
                ranked = sorted(scores.items(), key=lambda x: (-x[1], QUERY_CATEGORIES.get(x[0], {}).get("priority", 4)))
                classification = ranked[0][0]
                confidence = min(0.50 + 0.10 * ranked[0][1], 0.95)

        # ── Validation de classification (log) ─────────────────────────
        classification_log = {
            "classification": classification,
            "langue_detectee": lang,
            "signaux_detectes": {
                "siem_signals": siem_signals,
                "has_headers": has_headers,
                "url_count": url_count,
                "word_count": word_count,
                "is_log_format": is_log,
            },
            "confiance_classification": round(confidence, 2),
        }

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "primary_category": classification,
                "description": QUERY_CATEGORIES.get(classification, {}).get("description", "Classification inconnue"),
                "classification_log": classification_log,
                "langue_detectee": lang,
                "all_scores": {},
            },
            confidence=confidence,
            metadata={"classification_log": classification_log, "langue_detectee": lang},
        )
