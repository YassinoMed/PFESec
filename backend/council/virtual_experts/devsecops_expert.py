"""Expert 14 — DevSecOps & CI/CD Security Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class DevSecOpsExpert(VirtualExpert):
    expert_id = "devsecops_expert"
    expert_name = "DevSecOps Analyst"
    category = "devsecops"
    capabilities = ["cicd_security", "secret_scanning", "sast_dast", "dependency_security", "supply_chain"]
    MITRE_TECHNIQUES = [
        "T1195.002 - Compromise Software Supply Chain",
        "T1552.001 - Credentials In Files",
        "T1078 - Valid Accounts",
    ]

    HIGH_CONF_KEYWORDS = [
        "secret", "api key", "password in code", "hardcoded", "token in",
        "github actions", "gitlab ci", "jenkins", "pipeline", "ci/cd",
        "dependency confusion", "typosquatting", "malicious package",
        "sast", "dast", "iac", "terraform", "ansible",
        "dockerfile", "docker image", "base image", "supply chain",
    ]
    MED_CONF_KEYWORDS = [
        "code", "repository", "repo", "git", "commit", "merge request",
        "pull request", "artifact", "build", "deploy", "package",
        "npm", "pip", "maven", "gradle", "requirements.txt",
    ]

    _DEVSECOPS_RISKS = {
        "hardcoded": ("Secret/credential hardcodé dans le code", "CRITICAL", "T1552.001 - Credentials In Files"),
        "api key": ("API key exposée dans le code ou logs", "CRITICAL", "T1552.001 - Credentials In Files"),
        "password in code": ("Mot de passe en clair dans le code source", "CRITICAL", "T1552.001 - Credentials In Files"),
        "dependency confusion": ("Attaque dependency confusion possible", "HIGH", "T1195.002 - Supply Chain"),
        "typosquatting": ("Typosquatting de package détecté", "HIGH", "T1195.002 - Supply Chain"),
        "malicious package": ("Package malveillant identifié", "CRITICAL", "T1195.002 - Supply Chain"),
        "iac": ("Misconfiguration Infrastructure as Code", "HIGH", "T1190 - Exploit Public-Facing"),
        "dockerfile": ("Dockerfile non sécurisé (root, latest tag)", "MEDIUM", "T1610 - Deploy Container"),
    }

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"
        mitre_found = list(self.MITRE_TECHNIQUES)

        for keyword, (desc, sev, technique) in self._DEVSECOPS_RISKS.items():
            if keyword in query:
                evidence.append(f"Risque DevSecOps: {desc}")
                if technique not in mitre_found:
                    mitre_found.append(technique)
                if sev == "CRITICAL":
                    confidence = min(confidence + 35, 95)
                    severity = "CRITICAL"
                elif sev == "HIGH" and severity not in ("CRITICAL",):
                    confidence = min(confidence + 20, 95)
                    severity = "HIGH"
                elif sev == "MEDIUM" and severity not in ("CRITICAL", "HIGH"):
                    confidence = min(confidence + 10, 95)
                    severity = "MEDIUM"

        if not severity or severity == "UNKNOWN":
            severity = "MEDIUM" if confidence > 30 else "INFORMATIONAL"

        if confidence >= 45:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if any(kw in query for kw in ["secret", "api key", "hardcoded", "password in code"]):
            recs.append("Scanner le code avec truffleHog ou GitLeaks pour les secrets exposés")
            recs.append("Révoquer immédiatement les credentials exposés")
        if "pipeline" in query or "cicd" in query or "ci/cd" in query:
            recs.append("Auditer les permissions des pipelines CI/CD (least privilege)")
        if "package" in query or "dependency" in query:
            recs.append("Scanner les dépendances avec OWASP Dependency-Check ou Snyk")
        recs.append("Intégrer SAST/DAST et Secret Scanning dans le pipeline CI/CD")

        return {
            "response": f"Analyse DevSecOps: {len(evidence)} risque(s) détecté(s). Sévérité: {severity}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Sans accès au dépôt de code et aux logs CI/CD"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": mitre_found[:5],
            "severity": severity,
        }
