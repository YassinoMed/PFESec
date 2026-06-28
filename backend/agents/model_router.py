from typing import Dict, List, Optional
from backend.agents.base import BaseAgent, AgentContext, AgentResult
from backend.config import CONFIG


CATEGORY_MODEL_MAP: Dict[str, List[str]] = {
    "phishing_analysis": ["cysecbert", "phishsense"],
    "email_analysis": ["cysecbert", "phishsense"],
    "malware_analysis": ["malbert", "malconv"],
    "url_analysis": ["urlbert", "urlnet"],
    "web_security": ["codebert", "graphcodebert"],
    "network_security": ["netbert", "flowtransformer"],
    "log_analysis": ["logbert", "deeplog"],
    "ioc_analysis": ["iocbert", "attackbert"],
    "cve_analysis": ["attackbert", "qwen2_5_1_5b"],
    "threat_intel": ["attackbert", "iocbert"],
    "sigma_analysis": ["qwen2_5_1_5b"],
    "incident_response": ["qwen2_5_1_5b", "smollm2_1_7b"],
    "threat_hunting": ["attackbert", "iocbert"],
    "ocr_analysis": ["paddleocr", "trocr_small"],
    "kubernetes_security": ["qwen2_5_1_5b"],
    "cloud_security": ["qwen2_5_1_5b"],
    "devsecops_review": ["codebert", "graphcodebert"],
    "general_security_question": ["qwen2_5_1_5b", "smollm2_1_7b"],
}

TYPE_MAP: Dict[str, str] = {
    "cysecbert": "bert",
    "phishsense": "lora",
    "codebert": "bert",
    "graphcodebert": "bert",
    "netbert": "bert",
    "flowtransformer": "transformer",
    "malbert": "bert",
    "malconv": "cnn",
    "attackbert": "bert",
    "iocbert": "bert",
    "urlbert": "bert",
    "urlnet": "cnn",
    "logbert": "bert",
    "deeplog": "lstm",
    "paddleocr": "ocr",
    "trocr_small": "transformer",
    "qwen2_5_1_5b": "llm",
    "smollm2_1_7b": "llm",
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
