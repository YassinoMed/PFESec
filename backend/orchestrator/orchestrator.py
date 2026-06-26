import asyncio
import time
from typing import Any, Dict, List, Optional
from backend.agents.base import AgentContext, AgentResult
from backend.agents.query_classifier import QueryClassifierAgent
from backend.agents.model_router import ModelRouterAgent
from backend.agents.security_rag import SecurityRAGAgent
from backend.agents.threat_intelligence import ThreatIntelligenceAgent
from backend.agents.sigma_analysis import SigmaAnalysisAgent
from backend.agents.malware_analysis import MalwareAnalysisAgent
from backend.agents.incident_response import IncidentResponseAgent
from backend.agents.evidence_fusion import EvidenceFusionAgent
from backend.agents.securityllm_synthesis import SecurityLLMSynthesisAgent
from backend.agents.governance import AIGovernanceAgent
from backend.orchestrator.workflow import SECURITY_WORKFLOWS, WorkflowDefinition, WorkflowStep
from backend.config import CONFIG


class AIOrchestrator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.agents: Dict[str, Any] = {}
        self._register_agents()

    def _register_agents(self):
        self.agents = {
            "query_classifier": QueryClassifierAgent(),
            "model_router": ModelRouterAgent(),
            "security_rag": SecurityRAGAgent(),
            "threat_intelligence": ThreatIntelligenceAgent(),
            "sigma_analysis": SigmaAnalysisAgent(),
            "malware_analysis": MalwareAnalysisAgent(),
            "incident_response": IncidentResponseAgent(),
            "evidence_fusion": EvidenceFusionAgent(),
            "securityllm_synthesis": SecurityLLMSynthesisAgent(),
            "ai_governance": AIGovernanceAgent(),
        }

    def get_agent(self, name: str):
        return self.agents.get(name)

    def get_workflow(self, category: str) -> Optional[WorkflowDefinition]:
        return SECURITY_WORKFLOWS.get(category)

    async def execute_workflow(self, context: AgentContext, workflow: WorkflowDefinition) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        execution_graph = self._build_execution_graph(workflow)

        for step in execution_graph:
            agent = self.agents.get(step.agent_name)
            if not agent:
                results[step.agent_name] = {"error": f"Agent '{step.agent_name}' non trouve", "success": False}
                continue

            context.intermediate_results = dict(results)
            result = await agent.run(context)
            results[step.agent_name] = {
                "output": result.output if hasattr(result, "output") else result,
                "success": getattr(result, "success", True),
                "confidence": getattr(result, "confidence", 0),
                "latency_ms": getattr(result, "latency_ms", 0),
                "error": getattr(result, "error", None),
            }

        return results

    def _build_execution_graph(self, workflow: WorkflowDefinition) -> List[WorkflowStep]:
        executed = set()
        ordered = []
        remaining = list(workflow.steps)

        while remaining:
            batch = []
            for step in list(remaining):
                deps = set(step.depends_on)
                if deps.issubset(executed):
                    batch.append(step)
                    remaining.remove(step)
            if not batch and remaining:
                for step in remaining:
                    if step.optional:
                        batch.append(step)
                        remaining.remove(step)
                if not batch:
                    break
            ordered.extend(batch)
            executed.update(s.agent_name for s in batch)

        return ordered

    async def orchestrate(self, query: str, user_role: str = "analyst", context: Optional[Dict] = None) -> Dict:
        t0 = time.time()
        ctx = AgentContext(
            query=query,
            user_role=user_role,
            metadata=context or {},
        )

        classifier = self.agents["query_classifier"]
        classification = await classifier.run(ctx)
        category = classification.output.get("primary_category", "general_security_question")

        workflow = self.get_workflow(category)
        if not workflow:
            workflow = self.get_workflow("general_security_question")

        ctx.intermediate_results = {"query_classifier": classification.output}
        results = await self.execute_workflow(ctx, workflow)

        elapsed_s = round(time.time() - t0, 3)

        return {
            "classification": category,
            "workflow": workflow.name,
            "models_used": [],
            "agents_used": list(results.keys()),
            "results": results,
            "total_latency_s": elapsed_s,
            "trace_id": ctx.trace_id,
            "session_id": ctx.session_id,
        }
