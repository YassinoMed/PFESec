"""Expert 7 — Sigma Rule Analysis & Generation Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert

_SIGMA_TEMPLATES = {
    "powershell_encoded": {
        "title": "Suspicious PowerShell Encoded Command",
        "detection": "CommandLine|contains: '-EncodedCommand'",
        "level": "high",
    },
    "lsass_access": {
        "title": "LSASS Memory Access",
        "detection": "TargetImage|endswith: 'lsass.exe' AND GrantedAccess: '0x1010'",
        "level": "critical",
    },
    "mass_file_rename": {
        "title": "Mass File Rename (Ransomware Behavior)",
        "detection": "EventID: 4663 AND count_file_renames > 100",
        "level": "critical",
    },
    "phishing_email": {
        "title": "Suspicious Email Attachment Opening",
        "detection": "ParentImage|endswith: 'outlook.exe' AND Image|endswith: '.exe'",
        "level": "medium",
    },
    "scheduled_task": {
        "title": "Suspicious Scheduled Task Creation",
        "detection": "CommandLine|contains|all: ['schtasks', '/create', 'cmd']",
        "level": "high",
    },
}


class SigmaExpert(VirtualExpert):
    expert_id = "sigma_expert"
    expert_name = "Sigma Rules Analyst"
    category = "sigma_analysis"
    capabilities = ["sigma_detection", "sigma_generation", "siem_rules", "detection_engineering"]
    MITRE_TECHNIQUES = [
        "T1059.001 - PowerShell",
        "T1003.001 - LSASS Memory",
        "T1486 - Data Encrypted for Impact",
    ]

    HIGH_CONF_KEYWORDS = [
        "sigma", "sigma rule", "detection rule", "splunk", "kql", "eql",
        "siem", "alert", "detection logic", "event id", "eventid",
    ]
    MED_CONF_KEYWORDS = [
        "log", "event", "audit", "winlog", "windows event", "sysmon",
        "process creation", "network connection", "file create",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        evidence = []
        sigma_rules_generated = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # Match sigma templates to query content
        if "powershell" in query and ("enc" in query or "base64" in query):
            evidence.append("Pattern PowerShell encodé → règle Sigma applicable")
            sigma_rules_generated.append(_SIGMA_TEMPLATES["powershell_encoded"]["title"])
            confidence = min(confidence + 25, 95)
        if "lsass" in query or "mimikatz" in query:
            evidence.append("Accès LSASS détecté → règle Sigma anti-dump credentials")
            sigma_rules_generated.append(_SIGMA_TEMPLATES["lsass_access"]["title"])
            confidence = min(confidence + 25, 95)
        if "ransom" in query or "encrypt" in query:
            evidence.append("Pattern ransomware → règle Sigma mass file rename")
            sigma_rules_generated.append(_SIGMA_TEMPLATES["mass_file_rename"]["title"])
            confidence = min(confidence + 30, 95)
        if "phishing" in query or "attachment" in query:
            evidence.append("Pattern phishing email → règle Sigma attachment execution")
            sigma_rules_generated.append(_SIGMA_TEMPLATES["phishing_email"]["title"])
            confidence = min(confidence + 20, 95)
        if "scheduled task" in query or "schtask" in query:
            evidence.append("Scheduled task suspect → règle Sigma persistence")
            sigma_rules_generated.append(_SIGMA_TEMPLATES["scheduled_task"]["title"])
            confidence = min(confidence + 20, 95)

        if sigma_rules_generated:
            evidence.append(f"Règles Sigma correspondantes: {', '.join(sigma_rules_generated)}")

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
        if sigma_rules_generated:
            recs.append(f"Déployer dans le SIEM: {sigma_rules_generated[0]}")
            recs.append("Convertir les règles Sigma pour votre SIEM (Splunk/QRadar/Elastic)")
        recs.append("Tester les règles sur les logs historiques pour valider le taux de détection")

        return {
            "response": f"Analyse Sigma: {len(sigma_rules_generated)} règle(s) applicables. "
                        f"Conclusion: {conclusion}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Sans accès aux logs réels pour valider les règles"],
            "recommendations": recs,
            "iocs": self._extract_iocs(query),
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
