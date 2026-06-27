"""Expert 15 — Risk Assessment & Business Impact Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class RiskAssessmentVirtualExpert(VirtualExpert):
    expert_id = "risk_assessment_virtual_expert"
    expert_name = "Risk Assessment Expert"
    category = "risk_assessment"
    capabilities = ["business_risk", "regulatory_impact", "asset_criticality", "risk_scoring"]
    MITRE_TECHNIQUES = ["T1591 - Gather Victim Org Information"]

    HIGH_CONF_KEYWORDS = [
        "critical asset", "critical infrastructure", "pii", "gdpr", "rgpd",
        "data protection", "regulatory", "compliance", "nis2", "iso 27001",
        "pci dss", "hipaa", "financial data", "customer data", "personal data",
        "reputational damage", "business continuity", "rto", "rpo",
    ]
    MED_CONF_KEYWORDS = [
        "risk", "impact", "asset", "business", "loss", "damage",
        "exposure", "threat", "vulnerability", "attack surface",
    ]

    _REGULATIONS = {
        "gdpr": ("RGPD — notification obligatoire sous 72h en cas de violation", "HIGH"),
        "rgpd": ("RGPD — notification obligatoire sous 72h en cas de violation", "HIGH"),
        "nis2": ("NIS2 — signalement aux autorités compétentes requis", "HIGH"),
        "pci dss": ("PCI DSS — audit de conformité requis après incident", "HIGH"),
        "hipaa": ("HIPAA — notification des patients affectés obligatoire", "HIGH"),
        "iso 27001": ("ISO 27001 — enregistrement dans le registre des incidents requis", "MEDIUM"),
    }

    _CRITICAL_ASSETS = {
        "active directory": ("Active Directory compromis — impact critique sur toute l'infrastructure", "CRITICAL"),
        "domain controller": ("Domain Controller affecté — perte de contrôle potentielle", "CRITICAL"),
        "financial data": ("Données financières exposées — risque réglementaire et financier", "CRITICAL"),
        "pii": ("Données personnelles (PII) exposées — obligation RGPD", "HIGH"),
        "customer data": ("Données clients exposées — impact réputationnel et légal", "HIGH"),
        "production server": ("Serveur de production impacté — risque de continuité d'activité", "HIGH"),
    }

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # Regulatory impact
        for reg_kw, (desc, sev) in self._REGULATIONS.items():
            if reg_kw in query:
                evidence.append(f"Obligation réglementaire: {desc}")
                confidence = min(confidence + 15, 95)
                if sev == "HIGH" and severity not in ("CRITICAL",):
                    severity = "HIGH"

        # Critical assets
        for asset_kw, (desc, sev) in self._CRITICAL_ASSETS.items():
            if asset_kw in query:
                evidence.append(f"Actif critique: {desc}")
                confidence = min(confidence + 20, 95)
                if sev == "CRITICAL":
                    severity = "CRITICAL"
                elif sev == "HIGH" and severity not in ("CRITICAL",):
                    severity = "HIGH"

        if not severity or severity == "UNKNOWN":
            severity = "MEDIUM" if confidence > 30 else "INFORMATIONAL"

        if confidence >= 45:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"

        recs = []
        if "gdpr" in query or "rgpd" in query:
            recs.append("Notifier la CNIL / DPA dans les 72h si violation de données personnelles")
        if "nis2" in query:
            recs.append("Signaler l'incident à l'ANSSI (France) ou autorité NIS2 compétente")
        if severity == "CRITICAL":
            recs.append("Activer le Plan de Continuité d'Activité (PCA/BCP)")
        recs.append("Quantifier les pertes financières et réputationnelles potentielles")
        recs.append("Engager le département juridique pour évaluation de la responsabilité")

        return {
            "response": f"Évaluation du risque: {severity}. {len(evidence)} facteur(s) d'impact métier identifié(s).",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Évaluation sans accès au registre des risques de l'organisation"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
