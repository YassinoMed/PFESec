"""Virtual Experts Package — 15 specialized AI security expert agents.

Each VirtualExpert implements CouncilExpert using heuristic rules + RAG local knowledge.
No additional GPU required — runs in pure Python with low latency.
"""

from backend.council.virtual_experts.phishing_expert import PhishingExpert
from backend.council.virtual_experts.email_expert import EmailHeaderExpert
from backend.council.virtual_experts.malware_expert import MalwareExpert
from backend.council.virtual_experts.threat_intel_expert import ThreatIntelExpert
from backend.council.virtual_experts.ioc_expert import IOCExpert
from backend.council.virtual_experts.mitre_expert import MitreAttackExpert
from backend.council.virtual_experts.sigma_expert import SigmaExpert
from backend.council.virtual_experts.incident_response_expert import IncidentResponseExpert
from backend.council.virtual_experts.soc_analyst_expert import SOCAnalystExpert
from backend.council.virtual_experts.rag_knowledge_expert import RAGKnowledgeExpert
from backend.council.virtual_experts.vulnerability_expert import VulnerabilityExpert
from backend.council.virtual_experts.cloud_security_expert import CloudSecurityExpert
from backend.council.virtual_experts.kubernetes_security_expert import KubernetesSecurityExpert
from backend.council.virtual_experts.devsecops_expert import DevSecOpsExpert
from backend.council.virtual_experts.risk_assessment_expert import RiskAssessmentVirtualExpert
from backend.council.virtual_experts.url_expert import URLReputationExpert
from backend.council.virtual_experts.governance_expert import GovernanceExpert

ALL_VIRTUAL_EXPERTS = [
    PhishingExpert,
    EmailHeaderExpert,
    MalwareExpert,
    ThreatIntelExpert,
    IOCExpert,
    MitreAttackExpert,
    SigmaExpert,
    IncidentResponseExpert,
    SOCAnalystExpert,
    RAGKnowledgeExpert,
    VulnerabilityExpert,
    CloudSecurityExpert,
    KubernetesSecurityExpert,
    DevSecOpsExpert,
    RiskAssessmentVirtualExpert,
    URLReputationExpert,
    GovernanceExpert,
]

__all__ = [
    "ALL_VIRTUAL_EXPERTS",
    "PhishingExpert",
    "EmailHeaderExpert",
    "MalwareExpert",
    "ThreatIntelExpert",
    "IOCExpert",
    "MitreAttackExpert",
    "SigmaExpert",
    "IncidentResponseExpert",
    "SOCAnalystExpert",
    "RAGKnowledgeExpert",
    "VulnerabilityExpert",
    "CloudSecurityExpert",
    "KubernetesSecurityExpert",
    "DevSecOpsExpert",
    "RiskAssessmentVirtualExpert",
    "URLReputationExpert",
    "GovernanceExpert",
]
