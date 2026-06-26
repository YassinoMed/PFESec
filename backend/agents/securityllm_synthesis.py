import json
from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult


TEMPLATES = {
    "analyst": {
        "title": "Security Analysis Report — Analyst View",
        "sections": ["classification", "findings", "evidence", "recommendations"],
        "style": "technical_detailed",
    },
    "soc": {
        "title": "SOC Incident Summary",
        "sections": ["verdict", "triage", "actions", "timeline"],
        "style": "operational",
    },
    "ciso": {
        "title": "Executive Security Briefing",
        "sections": ["executive_summary", "risk_assessment", "business_impact", "strategic_recommendations"],
        "style": "executive",
    },
    "user": {
        "title": "Security Analysis Result",
        "sections": ["result", "explanation", "action_required"],
        "style": "simple",
    },
}


class SecurityLLMSynthesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("securityllm_synthesis")

    async def execute(self, context: AgentContext) -> AgentResult:
        user_role = context.user_role
        evidence = context.intermediate_results.get("evidence_fusion", {})
        query = context.query

        template_key = user_role if user_role in TEMPLATES else "user"
        template = TEMPLATES[template_key]

        report = self._build_report(template, query, evidence)

        return AgentResult(
            agent_name=self.name,
            success=True,
            output=report,
            confidence=0.9,
            metadata={
                "template_used": template_key,
                "role": user_role,
                "output_formats": ["markdown", "json", "html"],
            },
        )

    def _build_report(self, template: Dict, query: str, evidence: Dict) -> Dict:
        report = {
            "title": template["title"],
            "query": query[:200],
            "generated_at": __import__("datetime").datetime.now().isoformat(),
            "style": template["style"],
            "sections": {},
            "formats": {
                "markdown": "",
                "json": "",
                "html": "",
            },
        }

        if "executive_summary" in template["sections"]:
            threat = evidence.get("threat_assessment", {})
            report["sections"]["executive_summary"] = {
                "verdict": threat.get("verdict", "ANALYSIS_COMPLETE"),
                "confidence": f"{threat.get('confidence', 0.5)*100:.1f}%",
                "assets_at_risk": "A determiner",
                "business_impact": self._assess_business_impact(threat),
            }

        if "findings" in template["sections"]:
            models = evidence.get("models", {})
            findings = []
            for model_id, m_data in models.items():
                findings.append({
                    "model": model_id,
                    "verdict": m_data.get("verdict", "N/A"),
                    "threat_score": m_data.get("threat_score", "N/A"),
                    "confidence": f"{m_data.get('confidence', 0.5)*100:.1f}%" if m_data.get("confidence") else "N/A",
                })
            report["sections"]["findings"] = findings

        if "evidence" in template["sections"]:
            report["sections"]["evidence"] = {
                "models_analyzed": list(evidence.get("models", {}).keys()),
                "agents_executed": list(evidence.get("agents", {}).keys()),
                "models_contributing": evidence.get("evidence_summary", {}).get("total_models", 0),
                "agents_contributing": evidence.get("evidence_summary", {}).get("total_agents", 0),
            }

        if "recommendations" in template["sections"]:
            report["sections"]["recommendations"] = self._generate_recommendations(evidence)

        report["formats"]["markdown"] = self._to_markdown(report)
        report["formats"]["json"] = json.dumps(report, indent=2, ensure_ascii=False)
        report["formats"]["html"] = self._to_html(report)

        return report

    def _assess_business_impact(self, threat: Dict) -> str:
        verdict = threat.get("verdict", "UNKNOWN")
        if verdict == "BLOCK":
            return "CRITICAL — Impact potentiel sur la confidentialite, integrite et disponibilite"
        elif verdict == "UNCERTAIN":
            return "MODERE — Investigation supplementaire requise pour evaluer l'impact"
        return "FAIBLE — Aucun impact commercial identifie"

    def _generate_recommendations(self, evidence: Dict) -> List[str]:
        recs = []
        threat = evidence.get("threat_assessment", {})
        if threat.get("verdict") == "BLOCK":
            recs.append("ACTIONS IMMEDIATES: Isoler les actifs concernes")
            recs.append("Lancer le playbook d'incident response")
            recs.append("Escalader vers le SOC Manager")
        elif threat.get("verdict") == "UNCERTAIN":
            recs.append("Analyse manuelle approfondie recommandee")
            recs.append("Collecter des evidences complementaires")
            recs.append("Surveillance renforcee sur les actifs concernes")
        else:
            recs.append("Aucune action immediate requise")
            recs.append("Surveillance standard maintenue")
        recs.append("Documenter les resultats dans le SIEM")
        return recs

    def _to_markdown(self, report: Dict) -> str:
        lines = [f"# {report['title']}", f"**Requete:** {report['query']}", f"**Date:** {report['generated_at']}", ""]
        for section_name, content in report["sections"].items():
            title = section_name.replace("_", " ").title()
            lines.append(f"## {title}")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        lines.append(f"- {item.get('model', item.get('verdict', str(item)))}")
                    else:
                        lines.append(f"- {item}")
            elif isinstance(content, dict):
                for k, v in content.items():
                    lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            else:
                lines.append(str(content))
            lines.append("")
        return "\n".join(lines)

    def _to_html(self, report: Dict) -> str:
        md = self._to_markdown(report)
        title = report["title"]
        html = f"<h1>{title}</h1><pre>{md}</pre>"
        return f"<div class='security-report'>{html}</div>"
