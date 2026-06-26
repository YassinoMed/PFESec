from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class WorkflowStep:
    agent_name: str
    depends_on: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    timeout_s: int = 60
    optional: bool = False


@dataclass
class WorkflowDefinition:
    name: str
    steps: List[WorkflowStep]
    description: str = ""
    category: str = "general"


SECURITY_WORKFLOWS = {
    "phishing_analysis": WorkflowDefinition(
        name="phishing_analysis",
        description="Analyse complete de phishing multi-modeles",
        category="analysis",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("threat_intelligence", depends_on=[]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["model_router", "threat_intelligence", "security_rag"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
    "soc_assistance": WorkflowDefinition(
        name="soc_assistance",
        description="Assistance SOC avec analyse multi-couche",
        category="analysis",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("sigma_analysis", depends_on=[]),
            WorkflowStep("threat_intelligence", depends_on=[]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["model_router", "sigma_analysis", "threat_intelligence", "security_rag"]),
            WorkflowStep("incident_response", depends_on=["evidence_fusion"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
    "threat_intelligence": WorkflowDefinition(
        name="threat_intelligence",
        description="Renseignement sur les menaces avec enrichissement IOC",
        category="intel",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("threat_intelligence", depends_on=[]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["threat_intelligence", "security_rag"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
    "malware_analysis": WorkflowDefinition(
        name="malware_analysis",
        description="Analyse de code malveillant et classification",
        category="analysis",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("malware_analysis", depends_on=[]),
            WorkflowStep("threat_intelligence", depends_on=[]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["model_router", "malware_analysis", "threat_intelligence", "security_rag"]),
            WorkflowStep("incident_response", depends_on=["evidence_fusion"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
    "incident_response": WorkflowDefinition(
        name="incident_response",
        description="Reponse a incident avec plan d'action complet",
        category="response",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("incident_response", depends_on=[]),
            WorkflowStep("threat_intelligence", depends_on=[]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("sigma_analysis", depends_on=[]),
            WorkflowStep("malware_analysis", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["model_router", "incident_response", "threat_intelligence", "security_rag"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
    "general_security_question": WorkflowDefinition(
        name="general_security_question",
        description="Question securite generale avec RAG et LLM",
        category="general",
        steps=[
            WorkflowStep("query_classifier", depends_on=[]),
            WorkflowStep("model_router", depends_on=["query_classifier"]),
            WorkflowStep("security_rag", depends_on=[]),
            WorkflowStep("evidence_fusion", depends_on=["model_router", "security_rag"]),
            WorkflowStep("securityllm_synthesis", depends_on=["evidence_fusion"]),
            WorkflowStep("ai_governance", depends_on=["securityllm_synthesis"]),
        ],
    ),
}
