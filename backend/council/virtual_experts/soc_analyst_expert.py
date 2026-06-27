"""Expert 9 — SOC Analyst & Alert Triage Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class SOCAnalystExpert(VirtualExpert):
    expert_id = "soc_analyst_expert"
    expert_name = "SOC Triage Analyst"
    category = "soc_operations"
    capabilities = ["alert_triage", "false_positive_analysis", "priority_scoring", "soc_workflow"]
    MITRE_TECHNIQUES = ["T1078 - Valid Accounts", "T1110 - Brute Force"]

    HIGH_CONF_KEYWORDS = [
        "soc", "alert", "triage", "false positive", "true positive",
        "ticket", "case", "priority", "p1", "p2", "critical alert",
        "correlation", "siem rule", "edr alert", "xdr",
    ]
    MED_CONF_KEYWORDS = [
        "log", "event", "anomaly", "unusual", "suspicious", "detection",
        "monitoring", "investigate", "escalate",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # False positive indicators
        fp_keywords = ["test", "demo", "scan authorized", "pentest", "approved", "false positive"]
        tp_keywords = ["confirmed", "verified", "malicious", "attack", "exploit"]

        fp_hits = [kw for kw in fp_keywords if kw in query]
        tp_hits = [kw for kw in tp_keywords if kw in query]

        if fp_hits:
            evidence.append(f"Indicateurs de faux positif potentiel: {', '.join(fp_hits)}")
            confidence = max(confidence - 20, 5)
        if tp_hits:
            evidence.append(f"Indicateurs de vrai positif: {', '.join(tp_hits)}")
            confidence = min(confidence + 20, 95)

        # Priority scoring
        priority = "P3 - Standard"
        if any(kw in query for kw in ["critical", "p1", "urgent", "ransom", "breach"]):
            priority = "P1 - Critique"
            severity = "CRITICAL"
            confidence = min(confidence + 25, 95)
        elif any(kw in query for kw in ["high", "p2", "malware", "intrusion"]):
            priority = "P2 - Haute"
            severity = "HIGH"
        else:
            severity = "MEDIUM" if confidence > 30 else "LOW"

        if confidence >= 50:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        evidence.append(f"Priorité SOC évaluée: {priority}")

        recs = [
            f"Assigner au niveau {priority} dans le système de ticketing",
            "Documenter les preuves initiales dans le case management",
            "Vérifier si l'alerte est liée à des incidents récents (corrélation)",
            "Déterminer si une escalade Tier 2/3 est requise",
        ]
        if fp_hits:
            recs.insert(0, "Vérifier avec l'équipe IT — possible faux positif")

        return {
            "response": f"Triage SOC: {priority}. Conclusion: {conclusion}. "
                        f"{'Faux positif possible.' if fp_hits else 'Analyse standard.'}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Triage automatique — revue humaine recommandée"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
