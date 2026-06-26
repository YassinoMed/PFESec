import json
import time
import uuid
from typing import Any, Dict, Optional
from backend.orchestrator.orchestrator import AIOrchestrator
from backend.config import CONFIG


class SecurityAIGateway:
    def __init__(self):
        self.orchestrator = AIOrchestrator()

    async def handle_query(self, body: Dict) -> Dict:
        t0 = time.time()

        query = body.get("query", "").strip()
        context = body.get("context", {})
        user_role = body.get("user_role", "analyst")

        if not query:
            return self._error("Query requise", 400)

        try:
            result = await self.orchestrator.orchestrate(query, user_role, context)
            elapsed_s = round(time.time() - t0, 3)

            response = self._build_response(result, elapsed_s)
            return response

        except Exception as e:
            return self._error(str(e), 500)

    def _build_response(self, result: Dict, elapsed_s: float) -> Dict:
        results = result.get("results", {})
        synthesis = results.get("securityllm_synthesis", {}).get("output", {})
        evidence = results.get("evidence_fusion", {}).get("output", {})
        governance = results.get("ai_governance", {}).get("output", {})

        response_text = ""
        if isinstance(synthesis, dict):
            sections = synthesis.get("sections", {})
            if sections:
                response_text = "\n\n".join(
                    f"**{k.replace('_', ' ').title()}:**\n{v}" if isinstance(v, str) else str(v)
                    for k, v in sections.items()
                )
            report_formats = synthesis.get("formats", {})
            if "markdown" in report_formats:
                response_text = report_formats["markdown"]

        threat = evidence.get("threat_assessment", {})
        models_output = evidence.get("models", {})
        agents_output = evidence.get("agents", {})

        return {
            "success": True,
            "classification": result.get("classification", "general"),
            "workflow": result.get("workflow", "general_security_question"),
            "models_used": list(models_output.keys()),
            "agents_used": result.get("agents_used", []),
            "evidence": {
                "threat_assessment": threat,
                "models": models_output,
                "agents": agents_output,
                "summary": evidence.get("evidence_summary", {}),
            },
            "response": response_text,
            "confidence": threat.get("confidence", 0.5),
            "governance": governance,
            "latency_ms": round(elapsed_s * 1000, 2),
            "trace_id": result.get("trace_id", str(uuid.uuid4())),
            "session_id": result.get("session_id", str(uuid.uuid4())),
        }

    def _error(self, message: str, status: int = 500) -> Dict:
        return {"success": False, "error": message, "status": status}

    @staticmethod
    def get_routes():
        return [
            ("POST", f"{CONFIG.gateway.api_prefix}/query", "handle_query"),
        ]

    @staticmethod
    def get_openapi_spec() -> Dict:
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Security AI Gateway API",
                "version": "1.0.0",
                "description": "API de l'orchestrateur multi-agent de securite IA",
            },
            "paths": {
                f"{CONFIG.gateway.api_prefix}/query": {
                    "post": {
                        "summary": "Executer une requete securite multi-agent",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["query"],
                                        "properties": {
                                            "query": {"type": "string", "description": "Requete de securite"},
                                            "context": {"type": "object", "description": "Contexte optionnel"},
                                            "user_role": {
                                                "type": "string",
                                                "enum": ["analyst", "soc", "ciso", "user"],
                                                "default": "analyst",
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {"description": "Reponse complete avec evidences"},
                            "400": {"description": "Requete invalide"},
                            "500": {"description": "Erreur interne"},
                        },
                    }
                }
            },
        }
