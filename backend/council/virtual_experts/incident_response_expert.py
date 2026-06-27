"""Expert 8 — Incident Response & DFIR Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class IncidentResponseExpert(VirtualExpert):
    expert_id = "incident_response_expert"
    expert_name = "IR & DFIR Specialist"
    category = "incident_response"
    capabilities = ["incident_classification", "playbook_selection", "forensics_guidance", "containment_strategy"]
    MITRE_TECHNIQUES = [
        "T1490 - Inhibit System Recovery",
        "T1486 - Data Encrypted for Impact",
        "T1055 - Process Injection",
    ]

    HIGH_CONF_KEYWORDS = [
        "incident", "breach", "compromise", "intrusion", "data leak", "data breach",
        "ransom", "ransomware", "containment", "eradication", "recovery", "dfir",
        "forensic", "triage", "playbook", "runbook", "ioc", "artifact",
    ]
    MED_CONF_KEYWORDS = [
        "alert", "investigation", "log", "siem", "edr", "endpoint", "lateral",
        "access", "persistence", "exfiltrat",
    ]

    _INCIDENT_TYPES = {
        "ransomware": ["ransom", "encrypt", "wipe", "shadow copy", "backup delete"],
        "data_breach": ["data breach", "exfiltrat", "data leak", "steal", "exfil"],
        "phishing": ["phishing", "spearphishing", "credential harvest", "email scam"],
        "malware": ["malware", "trojan", "backdoor", "dropper", "loader", "shellcode"],
        "insider_threat": ["insider", "privileged user", "data theft", "unauthorized access"],
        "ddos": ["ddos", "dos", "denial of service", "flood", "amplification"],
    }

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        incident_type = "unknown"
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # Incident classification
        for inc_type, keywords in self._INCIDENT_TYPES.items():
            if any(kw in query for kw in keywords):
                incident_type = inc_type
                evidence.append(f"Incident classifié: {inc_type.replace('_', ' ').title()}")
                confidence = min(confidence + 20, 95)
                break

        # Severity from incident type
        severity_map = {
            "ransomware": "CRITICAL",
            "data_breach": "HIGH",
            "malware": "HIGH",
            "phishing": "MEDIUM",
            "insider_threat": "HIGH",
            "ddos": "MEDIUM",
        }
        severity = severity_map.get(incident_type, "UNKNOWN")

        if "lateral" in query or "persistence" in query:
            evidence.append("Mouvement latéral ou persistance → incident étendu")
            confidence = min(confidence + 15, 95)

        if "forensic" in query or "image" in query or "artifact" in query:
            evidence.append("Phase forensique identifiée → préservation des preuves requise")

        if confidence >= 45:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = [
            f"Activer le playbook IR pour: {incident_type.replace('_', ' ')}",
            "Documenter la chaîne de custody des artefacts forensiques",
            "Notifier le CISO et les parties prenantes selon la politique d'escalade",
            "Ouvrir un ticket de tracking dans le système ITSM",
        ]

        return {
            "response": f"Incident Response: type={incident_type}, sévérité={severity}. "
                        f"Actions prioritaires: {recs[0]}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Sans accès aux logs live et télémétrie SOC"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
