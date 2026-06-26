import re
from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


MITRE_MAPPING = {
    "t1566": "Phishing",
    "t1566.001": "Spearphishing Attachment",
    "t1566.002": "Spearphishing Link",
    "t1059": "Command and Scripting Interpreter",
    "t1059.001": "PowerShell",
    "t1059.003": "Windows Command Shell",
    "t1059.006": "Python",
    "t1547": "Boot or Logon Autostart Execution",
    "t1547.001": "Registry Run Keys / Startup Folder",
    "t1071": "Application Layer Protocol",
    "t1071.001": "Web Protocols",
    "t1071.004": "DNS",
    "t1003": "OS Credential Dumping",
    "t1003.001": "LSASS Memory",
    "t1486": "Data Encrypted for Impact",
    "t1485": "Data Destruction",
    "t1562": "Impair Defenses",
    "t1562.001": "Disable or Modify Tools",
    "t1078": "Valid Accounts",
    "t1078.003": "Local Accounts",
    "t1133": "External Remote Services",
    "t1190": "Exploit Public-Facing Application",
    "t1040": "Network Sniffing",
    "t1046": "Network Service Discovery",
    "t1057": "Process Discovery",
    "t1082": "System Information Discovery",
    "t1083": "File and Directory Discovery",
    "t1482": "Domain Trust Discovery",
    "t1550": "Use Alternate Authentication Material",
    "t1550.002": "Pass the Hash",
    "t1555": "Credentials from Password Stores",
    "t1204": "User Execution",
    "t1204.002": "Malicious File",
    "t1203": "Exploitation for Client Execution",
    "t1068": "Exploitation for Privilege Escalation",
}


class SigmaAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("sigma_analysis")

    def _parse_sigma_rule(self, text: str) -> Dict:
        rule = {
            "title": "",
            "id": "",
            "status": "",
            "description": "",
            "author": "",
            "logsource": {},
            "detection": {},
            "false_positives": [],
            "level": "",
            "tags": [],
            "mitre_techniques": [],
        }

        title_match = re.search(r"(?:title|Title)\s*:\s*(.+)", text)
        if title_match:
            rule["title"] = title_match.group(1).strip()

        id_match = re.search(r"(?:id|Id)\s*:\s*([a-fA-F0-9-]+)", text)
        if id_match:
            rule["id"] = id_match.group(1).strip()

        status_match = re.search(r"(?:status|Status)\s*:\s*(.+)", text)
        if status_match:
            rule["status"] = status_match.group(1).strip()

        desc_match = re.search(r"(?:description|Description)\s*:\s*(.+)", text)
        if desc_match:
            rule["description"] = desc_match.group(1).strip()

        level_match = re.search(r"(?:level|Level)\s*:\s*(.+)", text)
        if level_match:
            rule["level"] = level_match.group(1).strip()

        tags = re.findall(r"(?:tags|Tags)\s*\.?\w*\s*:\s*(.+)", text)
        rule["tags"] = [t.strip() for ts in tags for t in ts.split(",")]

        for tag in rule["tags"]:
            t_match = re.match(r"(?:attack\.)?(t\d{4}(?:\.\d{3})?)", tag.lower())
            if t_match:
                tid = t_match.group(1).lower()
                rule["mitre_techniques"].append({
                    "id": tid,
                    "name": MITRE_MAPPING.get(tid, "Unknown Technique"),
                })

        detection_match = re.search(r"(?:detection|Detection)\s*:\s*(.+)", text, re.DOTALL)
        if detection_match:
            rule["detection"]["raw"] = detection_match.group(1).strip()[:200]

        return rule

    def _assess_rule_quality(self, rule: Dict) -> Dict:
        issues = []
        score = 100

        if not rule["title"]:
            issues.append("Titre manquant")
            score -= 20
        if not rule["description"]:
            issues.append("Description manquante")
            score -= 15
        if not rule["detection"]:
            issues.append("Section detection manquante")
            score -= 30
        if not rule["level"]:
            issues.append("Niveau de risque non defini")
            score -= 10
        elif rule["level"].lower() not in ("informational", "low", "medium", "high", "critical"):
            issues.append("Niveau de risque invalide")
            score -= 5

        return {"score": max(score, 0), "issues": issues}

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        rule = self._parse_sigma_rule(query)
        quality = self._assess_rule_quality(rule)
        has_sigma_keywords = any(kw in query.lower() for kw in ["sigma", "detection:", "logsource:", "title:", "status:"])

        analysis = {
            "is_sigma_rule": has_sigma_keywords,
            "parsed_rule": rule,
            "quality": quality,
            "mitre_coverage": {
                "techniques_mapped": len(rule["mitre_techniques"]),
                "techniques": rule["mitre_techniques"],
            },
            "recommendations": [],
        }

        if quality["score"] < 70:
            analysis["recommendations"].append("Ameliorer la qualite de la regle Sigma")
        if len(rule["mitre_techniques"]) == 0 and has_sigma_keywords:
            analysis["recommendations"].append("Ajouter un mapping MITRE ATT&CK (tags: attack.tXXXX)")
        if not rule["false_positives"] and has_sigma_keywords:
            analysis["recommendations"].append("Documenter les faux positifs potentiels")
        if rule["level"].lower() == "informational" and has_sigma_keywords:
            analysis["recommendations"].append("Le niveau 'informational' pourrait masquer des alertes importantes")

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=analysis,
            confidence=0.9 if has_sigma_keywords else 0.3,
            metadata={
                "has_sigma": has_sigma_keywords,
                "techniques_mapped": len(rule["mitre_techniques"]),
                "quality_score": quality["score"],
            },
        )
