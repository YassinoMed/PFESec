from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


IR_PHASES = ["Preparation", "Identification", "Containment", "Eradication", "Recovery", "Lessons Learned"]

SEVERITY_TEMPLATES = {
    "critical": {
        "sla_minutes": 15,
        "escalation": "CISO + SOC Manager + Legal",
        "containment": "Isoler immediatement l'actif compromis. Desactiver les comptes. Bloquer les IOC au perimeter.",
        "eradication": "Reinstallation complete depuis backup sain. Rotation de tous les secrets et credentials.",
        "recovery": "Retour progressif avec monitoring renforce. Validation par equipe securite avant reouverture.",
    },
    "high": {
        "sla_minutes": 60,
        "escalation": "SOC Manager + On-Call Analyst",
        "containment": "Segmenter le reseau affecte. Appliquer les regles de blocage temporaires.",
        "eradication": "Supprimer les artefacts malveillants. Corriger les configurations vulnerees.",
        "recovery": "Retour en service normal apres validation des corrections.",
    },
    "medium": {
        "sla_minutes": 240,
        "escalation": "SOC Analyst Senior",
        "containment": "Surveillance renforcee. Preparation des mesures de containment si necessaire.",
        "eradication": "Correction programmee dans le cycle de patch standard.",
        "recovery": "Retour en service normal apres verification.",
    },
    "low": {
        "sla_minutes": 720,
        "escalation": "SOC Analyst",
        "containment": "Documenter et surveiller. Aucune action immediate requise.",
        "eradication": "Planifier la correction dans le prochain cycle de maintenance.",
        "recovery": "Aucune action de recuperation necessaire.",
    },
}


class IncidentResponseAgent(BaseAgent):
    def __init__(self):
        super().__init__("incident_response")

    def _determine_severity(self, context: AgentContext) -> str:
        query_lower = context.query.lower()
        critical_kw = ["ransomware", "data breach", "pii", "exfiltration", "root", "admin compromise",
                       "domain admin", "dc compromise", "critical", "p0", "sev0", "active breach"]
        high_kw = ["malware", "trojan", "backdoor", "lateral", "privilege escalation",
                   "persistence", "c2", "beacon", "phishing success", "compromised"]
        medium_kw = ["phishing", "scan", "recon", "enumeration", "suspicious", "alert", "ticket"]

        for kw in critical_kw:
            if kw in query_lower:
                return "critical"
        for kw in high_kw:
            if kw in query_lower:
                return "high"
        for kw in medium_kw:
            if kw in query_lower:
                return "medium"
        return "low"

    def _extract_assets(self, query: str) -> List[str]:
        import re
        assets = []
        ip_pattern = r"(?:\d{1,3}\.){3}\d{1,3}"
        assets.extend(re.findall(ip_pattern, query))
        host_pattern = r"(?:host|server|endpoint|workstation|server)\s*[:\s]+([a-zA-Z0-9_-]+)"
        assets.extend(re.findall(host_pattern, query, re.IGNORECASE))
        return assets if assets else ["Asset non specifie"]

    async def execute(self, context: AgentContext) -> AgentResult:
        severity = self._determine_severity(context)
        template = SEVERITY_TEMPLATES.get(severity, SEVERITY_TEMPLATES["low"])
        assets = self._extract_assets(context.query)

        plan = {
            "incident": {
                "severity": severity.upper(),
                "sla_minutes": template["sla_minutes"],
                "escalation": template["escalation"],
                "assets_affected": assets,
                "requires_legal": severity in ("critical", "high"),
            },
            "phases": {},
            "runbook_reference": f"IR-{severity.upper()}-{hash(context.query[:50]) % 10000:04d}",
        }

        for phase in IR_PHASES:
            phase_key = phase.lower().replace(" ", "_")
            if phase_key == "containment":
                plan["phases"][phase_key] = template["containment"]
            elif phase_key == "eradication":
                plan["phases"][phase_key] = template["eradication"]
            elif phase_key == "recovery":
                plan["phases"][phase_key] = template["recovery"]
            else:
                plan["phases"][phase_key] = self._default_phase_action(phase, severity, context.query)

        plan["investigation_actions"] = self._generate_investigation_actions(context.query)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=plan,
            confidence=0.85,
            metadata={
                "severity": severity,
                "phases": len(plan["phases"]),
                "assets": len(assets),
            },
        )

    def _default_phase_action(self, phase: str, severity: str, query: str) -> str:
        actions = {
            "Preparation": "Verifier que les runbooks sont a jour. Sensibiliser les equipes. Valider les sauvegardes.",
            "Identification": "Analyser les logs et alertes. Confirmer le perimetre de l'incident. Collecter les evidences.",
            "Lessons Learned": "Debriefer l'incident. Mettre a jour les runbooks. Ameliorer les regles de detection.",
        }
        return actions.get(phase, f"Phase {phase}: actions standard selon procedure {severity.upper()}")

    def _generate_investigation_actions(self, query: str) -> List[str]:
        return [
            "Collecter les logs systeme et reseau pertinents",
            "Analyser les connexions reseau suspectes",
            "Verifier l'integrite des fichiers critiques",
            "Rechercher des IOC complementaires",
            "Documenter la chronologie des evenements",
        ]
