from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult
from backend.config import CONFIG


CATEGORY_MODEL_MAP: Dict[str, List[str]] = {
    "phishing_analysis": ["cysecbert", "secbert", "phishsense", "securityllm"],
    "email_analysis": ["cysecbert", "secbert", "phishsense", "securityllm"],
    "malware_analysis": ["securityllm"],
    "url_analysis": ["cysecbert", "secbert", "phishsense"],
    "ioc_analysis": ["securityllm"],
    "cve_analysis": ["securityllm", "rag"],
    "sigma_analysis": ["securityllm"],
    "incident_response": ["securityllm", "security_rag"],
    "threat_hunting": ["securityllm", "security_rag"],
    "log_analysis": ["securityllm", "security_rag"],
    "kubernetes_security": ["securityllm", "rag"],
    "cloud_security": ["securityllm", "rag"],
    "devsecops_review": ["securityllm"],
    "rag_question": ["rag"],
    "general_security_question": ["securityllm"],
}

TYPE_MAP: Dict[str, str] = {
    "cysecbert": "bert",
    "secbert": "bert",
    "phishsense": "lora",
    "phishsense-merged": "llm",
    "securityllm": "llm",
    "securityllm-merged": "llm",
    "rag": "rag",
    "threat_intel": "threat_intel",
}


class ModelRouterAgent(BaseAgent):
    def __init__(self):
        super().__init__("model_router")

    async def execute(self, context: AgentContext) -> AgentResult:
        classification = context.intermediate_results.get("query_classifier", {})
        primary_category = classification.get("primary_category", "general_security_question")
        alternatives = classification.get("alternatives", [])

        models = list(CATEGORY_MODEL_MAP.get(primary_category, []))
        for alt in alternatives:
            for m in CATEGORY_MODEL_MAP.get(alt, []):
                if m not in models:
                    models.append(m)

        resolved = []
        for model_id in models:
            resolved.append({
                "model_id": model_id,
                "type": TYPE_MAP.get(model_id, "unknown"),
                "priority": CONFIG.model_router.priority_order.get(model_id, 99),
            })

        resolved.sort(key=lambda m: m["priority"])

        return AgentResult(
            agent_name=self.name,
            success=True,
            output={
                "models": resolved,
                "primary_category": primary_category,
                "total_selected": len(resolved),
                "strategy": "priority_based",
            },
            confidence=0.95,
            metadata={"category": primary_category, "models_selected": [m["model_id"] for m in resolved]},
        )
