"""Expert 6 — MITRE ATT&CK Framework Specialist."""
from typing import Dict, List
from backend.council.virtual_experts.base import VirtualExpert

_TACTIC_MAP = {
    "TA0001 - Initial Access": ["phishing", "drive-by", "exploit public-facing", "supply chain", "spearphishing"],
    "TA0002 - Execution": ["powershell", "wmi", "cmd", "cscript", "mshta", "macro", "vba", "rundll32"],
    "TA0003 - Persistence": ["registry", "scheduled task", "service", "startup", "autorun", "cron", "boot"],
    "TA0004 - Privilege Escalation": ["admin", "root", "uac bypass", "token", "exploit", "sudo", "elevation"],
    "TA0005 - Defense Evasion": ["obfuscat", "base64", "encode", "pack", "compress", "disable antivirus", "inject"],
    "TA0006 - Credential Access": ["credential", "password", "mimikatz", "lsass", "kerberos", "brute force"],
    "TA0007 - Discovery": ["whoami", "ipconfig", "netstat", "nmap", "scan", "enum", "tasklist", "systeminfo"],
    "TA0008 - Lateral Movement": ["rdp", "smb", "psexec", "pass-the-hash", "lateral", "pivot", "remote"],
    "TA0009 - Collection": ["collect", "harvest", "screenshot", "keylog", "clipboard", "steal"],
    "TA0010 - Exfiltration": ["exfiltrate", "upload", "transfer", "dns tunnel", "c2"],
    "TA0040 - Impact": ["ransom", "encrypt", "wipe", "destroy", "dos", "defacement", "delete"],
}


class MitreAttackExpert(VirtualExpert):
    expert_id = "mitre_expert"
    expert_name = "MITRE ATT&CK Analyst"
    category = "mitre_mapping"
    capabilities = ["mitre_attck_mapping", "ttp_analysis", "tactic_identification", "technique_classification"]
    MITRE_TECHNIQUES = [
        "T1566 - Phishing",
        "T1059 - Command and Scripting Interpreter",
        "T1486 - Data Encrypted for Impact",
    ]

    HIGH_CONF_KEYWORDS = [
        "mitre", "att&ck", "attck", "tactic", "technique", "procedure",
        "ttp", "kill chain", "diamond model",
    ]
    MED_CONF_KEYWORDS = [
        "phishing", "powershell", "persistence", "lateral", "exfiltrate",
        "credential", "ransom", "privilege",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        matched_tactics: List[str] = []
        all_techniques: List[str] = []
        evidence = []

        for tactic, keywords in _TACTIC_MAP.items():
            hits = [kw for kw in keywords if kw in query]
            if hits:
                matched_tactics.append(tactic)
                evidence.append(f"{tactic}: {', '.join(hits[:3])}")

        confidence = min(len(matched_tactics) * 18 + 10, 95.0)

        # Build technique list
        if "phishing" in query or "spearphishing" in query:
            all_techniques.append("T1566.001 - Spearphishing Attachment")
        if "powershell" in query and "enc" in query:
            all_techniques.append("T1059.001 - PowerShell (Encoded)")
        if "ransomware" in query or "encrypt" in query:
            all_techniques.append("T1486 - Data Encrypted for Impact")
        if "credential" in query or "mimikatz" in query:
            all_techniques.append("T1003.001 - LSASS Memory Dump")
        if "lateral" in query or "rdp" in query:
            all_techniques.append("T1021.001 - Remote Desktop Protocol")

        conclusion = "UNKNOWN"
        severity = "UNKNOWN"
        if len(matched_tactics) >= 3:
            conclusion = "BLOCK"
            severity = "HIGH"
            if len(matched_tactics) >= 5:
                severity = "CRITICAL"
        elif len(matched_tactics) >= 1:
            conclusion = "BLOCK" if any(t for t in matched_tactics if "Impact" in t or "Execution" in t) else "UNKNOWN"
            severity = "MEDIUM"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if matched_tactics:
            recs.append(f"Consulter les mitigations MITRE pour: {matched_tactics[0]}")
            recs.append("Créer des règles de détection basées sur les techniques identifiées")

        return {
            "response": f"Mapping MITRE ATT&CK: {len(matched_tactics)} tactique(s) détectée(s). "
                        f"Techniques: {', '.join(all_techniques[:3]) or 'Non spécifiées'}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence[:5],
            "limitations": ["Analyse textuelle uniquement — sans télémétrie endpoint"],
            "recommendations": recs,
            "iocs": self._extract_iocs(query),
            "mitre_techniques": (all_techniques + self.MITRE_TECHNIQUES)[:6],
            "severity": severity,
        }
