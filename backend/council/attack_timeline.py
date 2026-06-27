"""Attack Timeline Builder — Reconstructs the attack chronology from expert analyses.

Maps findings to MITRE ATT&CK phases, extracts IOCs, and identifies TTPs.
Never exposes raw model chain-of-thought — produces structured, explainable output.
"""

import re
from typing import Any, Dict, List, Optional

from backend.council.types import AttackPhase, AttackTimeline, ExpertAnalysis


# ── MITRE ATT&CK Tactic Mapping ─────────────────────────────────────────────

MITRE_TACTICS = {
    "TA0001": {
        "name": "Initial Access",
        "keywords": [
            "phishing", "spearphishing", "link", "attachment", "email",
            "drive-by", "watering hole", "supply chain", "exploit public-facing",
            "urgent", "verify", "credential", "login", "password", "suspend",
        ],
        "techniques": {
            "phishing": "T1566 - Phishing",
            "spearphishing": "T1566.001 - Spearphishing Attachment",
            "link": "T1566.002 - Spearphishing Link",
            "drive-by": "T1189 - Drive-by Compromise",
            "supply chain": "T1195 - Supply Chain Compromise",
        },
    },
    "TA0002": {
        "name": "Execution",
        "keywords": [
            "powershell", "cmd", "wscript", "cscript", "mshta", "rundll32",
            "regsvr32", "certutil", "bitsadmin", "macro", "vba", "wmi",
            "encoded", "base64", "invoke-expression", "iex",
        ],
        "techniques": {
            "powershell": "T1059.001 - PowerShell",
            "cmd": "T1059.003 - Windows Command Shell",
            "wmi": "T1047 - Windows Management Instrumentation",
            "macro": "T1566.001 - Malicious Macro",
            "base64": "T1027 - Obfuscated Files or Information",
        },
    },
    "TA0003": {
        "name": "Persistence",
        "keywords": [
            "registry", "startup", "scheduled task", "service", "cron",
            "autorun", "startup folder", "run key", "boot", "backdoor",
            "rootkit", "implant", "persistence",
        ],
        "techniques": {
            "registry": "T1547.001 - Registry Run Keys",
            "scheduled task": "T1053.005 - Scheduled Task",
            "service": "T1543.003 - Windows Service",
            "cron": "T1053.003 - Cron Job",
            "backdoor": "T1505 - Server Software Component",
        },
    },
    "TA0004": {
        "name": "Privilege Escalation",
        "keywords": [
            "admin", "root", "privilege", "escalation", "sudo", "uac bypass",
            "token", "impersonation", "runas", "elevation", "exploit",
        ],
        "techniques": {
            "uac bypass": "T1548.002 - Bypass User Account Control",
            "token": "T1134 - Access Token Manipulation",
            "exploit": "T1068 - Exploitation for Privilege Escalation",
        },
    },
    "TA0005": {
        "name": "Defense Evasion",
        "keywords": [
            "obfuscate", "encode", "encrypt", "pack", "compress", "hide",
            "disable", "antivirus", "sandbox", "vm", "debug", "timestamp",
            "masquerade", "rename", "inject",
        ],
        "techniques": {
            "obfuscate": "T1027 - Obfuscated Files or Information",
            "disable": "T1562 - Impair Defenses",
            "inject": "T1055 - Process Injection",
            "masquerade": "T1036 - Masquerading",
        },
    },
    "TA0006": {
        "name": "Credential Access",
        "keywords": [
            "credential", "password", "hash", "kerberos", "ticket", "lsass",
            "mimikatz", "dump", "brute force", "spray", "keylog", "phishing",
        ],
        "techniques": {
            "lsass": "T1003.001 - LSASS Memory",
            "kerberos": "T1558 - Steal or Forge Kerberos Tickets",
            "brute force": "T1110 - Brute Force",
            "keylog": "T1056.001 - Keylogging",
        },
    },
    "TA0007": {
        "name": "Discovery",
        "keywords": [
            "scan", "enum", "network", "host", "service", "port", "nmap",
            "whoami", "ipconfig", "netstat", "tasklist", "systeminfo",
        ],
        "techniques": {
            "scan": "T1046 - Network Service Discovery",
            "enum": "T1087 - Account Discovery",
            "systeminfo": "T1082 - System Information Discovery",
        },
    },
    "TA0008": {
        "name": "Lateral Movement",
        "keywords": [
            "lateral", "pivot", "rdp", "smb", "wmi", "pass-the-hash",
            "pass-the-ticket", "remote service", "ssh", "psexec",
        ],
        "techniques": {
            "rdp": "T1021.001 - Remote Desktop Protocol",
            "smb": "T1021.002 - SMB/Windows Admin Shares",
            "pass-the-hash": "T1550.002 - Pass the Hash",
            "psexec": "T1569.002 - Service Execution",
        },
    },
    "TA0009": {
        "name": "Collection",
        "keywords": [
            "collect", "steal", "harvest", "exfiltrate", "data", "file",
            "document", "email", "clipboard", "screenshot", "keylog",
        ],
        "techniques": {
            "collect": "T1005 - Data from Local System",
            "clipboard": "T1115 - Clipboard Data",
            "screenshot": "T1113 - Screen Capture",
        },
    },
    "TA0010": {
        "name": "Exfiltration",
        "keywords": [
            "exfiltrate", "upload", "transfer", "dns", "http", "ftp",
            "cloud", "dropbox", "pastebin", "c2", "c&c", "command and control",
        ],
        "techniques": {
            "dns": "T1048.003 - Exfiltration Over Unencrypted/Obfuscated Non-C2 Protocol",
            "http": "T1041 - Exfiltration Over C2 Channel",
            "cloud": "T1567 - Exfiltration Over Web Service",
        },
    },
    "TA0040": {
        "name": "Impact",
        "keywords": [
            "ransom", "encrypt", "destroy", "wipe", "disrupt", "dos", "ddos",
            "defacement", "sabotage", "lock", "delete",
        ],
        "techniques": {
            "ransom": "T1486 - Data Encrypted for Impact",
            "wipe": "T1561 - Disk Wipe",
            "dos": "T1499 - Endpoint Denial of Service",
        },
    },
}


# ── IOC Extraction Patterns ──────────────────────────────────────────────────

_IOC_PATTERNS = [
    ("url", re.compile(r"https?://[^\s\"\'>]+", re.IGNORECASE)),
    ("ip", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("domain", re.compile(r"\b(?:[a-z0-9\-]+\.)+(?:xyz|com|org|net|io|ru|cn|tk|pw|cc|top|club|online|site|web|info|biz)\b", re.IGNORECASE)),
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("hash_md5", re.compile(r"\b[0-9a-fA-F]{32}\b")),
    ("hash_sha1", re.compile(r"\b[0-9a-fA-F]{40}\b")),
    ("hash_sha256", re.compile(r"\b[0-9a-fA-F]{64}\b")),
    ("cve", re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)),
]

_SIGMA_TEMPLATES = {
    "powershell_encoded": "sigma:detect_powershell_encoded_command",
    "mimikatz": "sigma:detect_lsass_memory_access",
    "ransomware": "sigma:detect_mass_file_encryption",
    "phishing": "sigma:detect_suspicious_email_attachment",
    "lateral_movement": "sigma:detect_lateral_movement_smb",
}


class AttackTimelineBuilder:
    """
    Reconstructs the attack chronology from aggregated expert analyses.
    Maps findings to MITRE ATT&CK tactics/techniques and extracts IOCs.
    """

    def build(
        self,
        query: str,
        classification: str,
        analyses: List[ExpertAnalysis],
        fact_check_refs: Optional[List[Dict]] = None,
    ) -> AttackTimeline:
        corpus = self._build_corpus(query, analyses)
        iocs = self._extract_iocs(corpus)
        phases = self._build_phases(corpus, analyses)
        lateral = self._detect_lateral_movement(corpus)
        persistence = self._detect_persistence(corpus)
        exfil = self._detect_exfiltration(corpus)
        attack_vector = self._classify_attack_vector(classification, corpus)
        entry_point = self._identify_entry_point(classification, corpus, iocs)
        impact = self._assess_impact(corpus, phases)
        tactics = [p.phase_id + " - " + p.phase_name for p in phases if p.confidence >= 0.3]
        sigma_rules = self._suggest_sigma_rules(corpus)

        return AttackTimeline(
            attack_vector=attack_vector,
            entry_point=entry_point,
            phases=phases,
            iocs_extracted=iocs,
            lateral_movement=lateral,
            persistence_mechanism=persistence,
            exfiltration_detected=exfil,
            estimated_impact=impact,
            mitre_tactics=tactics,
            sigma_rules=sigma_rules,
        )

    # ── Internal helpers ──────────────────────────────────────────────────

    def _build_corpus(self, query: str, analyses: List[ExpertAnalysis]) -> str:
        parts = [query.lower()]
        for a in analyses:
            if a.response:
                parts.append(str(a.response).lower())
            parts.extend(e.lower() for e in a.evidence)
            parts.extend(str(ioc).lower() for ioc in a.iocs)
        return " ".join(parts)

    def _extract_iocs(self, corpus: str) -> List[Dict]:
        iocs = []
        for ioc_type, pattern in _IOC_PATTERNS:
            for match in pattern.findall(corpus):
                iocs.append({"type": ioc_type, "value": match, "confidence": 0.8})
        # Deduplicate
        seen = set()
        unique = []
        for ioc in iocs:
            key = f"{ioc['type']}:{ioc['value']}"
            if key not in seen:
                seen.add(key)
                unique.append(ioc)
        return unique[:20]

    def _build_phases(self, corpus: str, analyses: List[ExpertAnalysis]) -> List[AttackPhase]:
        phases = []
        for tactic_id, tactic in MITRE_TACTICS.items():
            hits = [kw for kw in tactic["keywords"] if kw in corpus]
            if not hits:
                continue
            confidence = min(0.3 + len(hits) * 0.1, 0.98)
            techniques = []
            for kw, tech in tactic["techniques"].items():
                if kw in corpus:
                    techniques.append(tech)
            if not techniques:
                techniques = [f"{list(tactic['techniques'].values())[0]} (inferred)"]
            evidence = [f"Keyword match: '{h}'" for h in hits[:4]]
            # add analyst evidence if available
            for a in analyses:
                if a.status == "completed":
                    for m in a.mitre_techniques:
                        if tactic["name"].lower() in m.lower():
                            evidence.append(f"Expert {a.expert_name}: {m}")
            phases.append(AttackPhase(
                phase_id=tactic_id,
                phase_name=tactic["name"],
                techniques=techniques[:5],
                evidence=evidence[:5],
                confidence=confidence,
            ))
        # Sort by natural kill-chain order
        order = list(MITRE_TACTICS.keys())
        phases.sort(key=lambda p: order.index(p.phase_id) if p.phase_id in order else 99)
        return phases

    def _detect_lateral_movement(self, corpus: str) -> bool:
        keywords = ["lateral", "pivot", "rdp", "smb", "pass-the-hash", "psexec", "ssh tunnel"]
        return any(kw in corpus for kw in keywords)

    def _detect_persistence(self, corpus: str) -> Optional[str]:
        if "registry" in corpus or "run key" in corpus:
            return "Registry Run Key (T1547.001)"
        if "scheduled task" in corpus or "cron" in corpus:
            return "Scheduled Task (T1053.005)"
        if "service" in corpus and "startup" in corpus:
            return "Windows Service (T1543.003)"
        if "backdoor" in corpus:
            return "Backdoor implant (T1505)"
        return None

    def _detect_exfiltration(self, corpus: str) -> bool:
        keywords = ["exfiltrate", "upload", "transfer", "c2", "command and control", "dns tunnel"]
        return any(kw in corpus for kw in keywords)

    def _classify_attack_vector(self, classification: str, corpus: str) -> str:
        if "phishing" in classification or "email" in classification or "phish" in corpus:
            return "Email / Phishing"
        if "malware" in classification or "ransomware" in corpus:
            return "Malware Delivery"
        if "cve" in corpus or "exploit" in corpus:
            return "Vulnerability Exploitation"
        if "supply chain" in corpus:
            return "Supply Chain Attack"
        if "kubernetes" in corpus or "k8s" in corpus:
            return "Container / Kubernetes Compromise"
        if "cloud" in corpus or "s3" in corpus or "azure" in corpus:
            return "Cloud Infrastructure Attack"
        return "Unknown Vector"

    def _identify_entry_point(self, classification: str, corpus: str, iocs: List[Dict]) -> str:
        urls = [i["value"] for i in iocs if i["type"] == "url"]
        if urls:
            return f"Malicious URL: {urls[0]}"
        emails = [i["value"] for i in iocs if i["type"] == "email"]
        if emails:
            return f"Suspicious email: {emails[0]}"
        domains = [i["value"] for i in iocs if i["type"] == "domain"]
        if domains:
            return f"Malicious domain: {domains[0]}"
        if "phishing" in classification:
            return "Phishing email (no explicit IOC extracted)"
        if "malware" in classification:
            return "Malicious payload delivery"
        return "Entry point undetermined"

    def _assess_impact(self, corpus: str, phases: List[AttackPhase]) -> str:
        if "ransom" in corpus or "encrypt" in corpus:
            return "Data Encryption / Ransomware — Critical"
        if "exfiltrate" in corpus or "steal" in corpus:
            return "Data Exfiltration — High"
        if "credential" in corpus or "password" in corpus:
            return "Credential Compromise — High"
        if "lateral" in corpus:
            return "Internal Network Compromise — High"
        if len(phases) >= 5:
            return "Advanced Persistent Threat — High"
        if len(phases) >= 2:
            return "Multi-stage Attack — Medium"
        return "Initial Access / Phishing Attempt — Medium"

    def _suggest_sigma_rules(self, corpus: str) -> List[str]:
        rules = []
        for kw, rule in _SIGMA_TEMPLATES.items():
            if kw in corpus:
                rules.append(rule)
        return rules
