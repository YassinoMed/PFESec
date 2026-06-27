"""Expert 12 — Cloud Security Specialist (AWS / Azure / GCP)."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class CloudSecurityExpert(VirtualExpert):
    expert_id = "cloud_security_expert"
    expert_name = "Cloud Security Analyst"
    category = "cloud_security"
    capabilities = ["aws_security", "azure_security", "gcp_security", "cloud_misconfiguration", "iam_analysis"]
    MITRE_TECHNIQUES = [
        "T1078.004 - Cloud Accounts",
        "T1537 - Transfer Data to Cloud Account",
        "T1580 - Cloud Infrastructure Discovery",
    ]

    HIGH_CONF_KEYWORDS = [
        "s3 bucket", "public bucket", "aws", "azure", "gcp", "cloud",
        "iam role", "iam policy", "access key", "secret key", "cloud trail",
        "cloudwatch", "storage account", "blob", "cloud function", "lambda",
        "misconfiguration", "public exposure", "open bucket",
    ]
    MED_CONF_KEYWORDS = [
        "cloud", "saas", "iaas", "paas", "kubernetes", "docker", "container",
        "registry", "ecr", "gcr", "acr", "managed service",
    ]

    _MISCONFIGS = {
        "s3 bucket public": ("S3 bucket accessible publiquement", "HIGH", "T1530 - Data from Cloud Storage"),
        "iam": ("Politique IAM permissive ou excessive", "HIGH", "T1078.004 - Cloud Accounts"),
        "root": ("Compte root AWS utilisé directement", "CRITICAL", "T1078 - Valid Accounts"),
        "access key": ("Access key exposée", "CRITICAL", "T1552.005 - Cloud Instance Metadata API"),
        "security group": ("Security Group trop permissif (0.0.0.0/0)", "HIGH", "T1190 - Exploit Public-Facing"),
        "mfa disabled": ("MFA désactivé sur compte cloud", "HIGH", "T1556 - Modify Authentication Process"),
        "cloudtrail disabled": ("CloudTrail désactivé — logs d'audit manquants", "HIGH", "T1562.008 - Disable Cloud Logs"),
    }

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"
        mitre_found = list(self.MITRE_TECHNIQUES)

        for keyword, (desc, sev, technique) in self._MISCONFIGS.items():
            if keyword in query:
                evidence.append(f"Misconfiguration détectée: {desc} ({sev})")
                if technique not in mitre_found:
                    mitre_found.append(technique)
                if sev == "CRITICAL":
                    confidence = min(confidence + 35, 95)
                    severity = "CRITICAL"
                elif sev == "HIGH" and severity not in ("CRITICAL",):
                    confidence = min(confidence + 25, 95)
                    severity = "HIGH"

        if not severity or severity == "UNKNOWN":
            severity = "MEDIUM" if confidence > 30 else "INFORMATIONAL"

        if confidence >= 50:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if severity in ("CRITICAL", "HIGH"):
            recs.append("Audit de sécurité cloud immédiat (ScoutSuite, Prowler, CloudSploit)")
            recs.append("Appliquer les benchmarks CIS pour AWS/Azure/GCP")
        if "access key" in query:
            recs.append("Révoquer et renouveler les access keys exposées immédiatement")
        if "s3" in query and "public" in query:
            recs.append("Désactiver l'accès public aux buckets S3 concernés")
        recs.append("Activer CloudTrail et les alertes de configuration Change")

        return {
            "response": f"Analyse cloud: {len(evidence)} misconfiguration(s) détectée(s). Sévérité: {severity}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Sans accès direct aux consoles cloud et aux logs"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": mitre_found[:5],
            "severity": severity,
        }
