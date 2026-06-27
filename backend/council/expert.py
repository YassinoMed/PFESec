"""Council Expert Manager — Manages all expert agents including 15 virtual experts."""

import asyncio
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.council.types import ExpertAnalysis


class CouncilExpert(ABC):
    expert_id: str
    expert_name: str
    category: str
    capabilities: List[str]

    @abstractmethod
    async def analyze(self, query: str, context: Optional[Dict] = None) -> ExpertAnalysis:
        ...

    async def answer(self, question: str, analysis: ExpertAnalysis, peer: Optional[ExpertAnalysis] = None) -> str:
        if peer:
            return (
                f"{self.expert_name} compare sa conclusion {analysis.conclusion} avec "
                f"{peer.expert_name} ({peer.conclusion}). Les preuves locales restent: "
                f"{'; '.join(analysis.evidence[:3]) or 'aucune preuve explicite'}."
            )
        return (
            f"{self.expert_name}: conclusion={analysis.conclusion}, confiance={analysis.confidence:.1f}%. "
            f"Preuves: {'; '.join(analysis.evidence[:3]) or 'aucune preuve explicite'}. "
            f"Limites: {'; '.join(analysis.limitations[:2]) or 'non specifiees'}."
        )

    async def validate(self, other: ExpertAnalysis, own: ExpertAnalysis) -> Dict[str, str]:
        if not own.error and own.conclusion == other.conclusion:
            return {"status": "confirmed", "notes": f"{self.expert_name} confirme la conclusion {other.conclusion}."}
        if not own.error and own.conclusion != "UNKNOWN" and other.conclusion != "UNKNOWN":
            return {"status": "challenged", "notes": f"{self.expert_name} signale un desaccord avec {other.expert_name}."}
        return {"status": "limited", "notes": f"{self.expert_name} ne dispose pas d'assez d'elements pour valider."}


class RegistryCouncilExpert(CouncilExpert):
    def __init__(self, model):
        self.model = model
        meta = model.metadata()
        self.expert_id = meta.model_id
        self.expert_name = meta.name
        self.category = meta.category.value
        self.capabilities = [meta.task, meta.category.value, meta.framework]

    async def analyze(self, query: str, context: Optional[Dict] = None) -> ExpertAnalysis:
        t0 = time.time()
        try:
            output = await self.model.predict({"text": query, "query": query, "context": context or {}})
            elapsed_ms = _extract_inference_ms(output, t0)
            if output.get("error"):
                return ExpertAnalysis(
                    expert_id=self.expert_id,
                    expert_name=self.expert_name,
                    category=self.category,
                    status="error",
                    confidence=0.0,
                    inference_ms=elapsed_ms,
                    error=output.get("error"),
                    limitations=["model_error"],
                )

            response = _extract_response(output)
            confidence = _normalize_confidence(_extract_confidence(output))
            conclusion = _extract_conclusion(output, response)
            return ExpertAnalysis(
                expert_id=self.expert_id,
                expert_name=self.expert_name,
                category=self.category,
                status="completed",
                response=response,
                conclusion=conclusion,
                confidence=confidence,
                evidence=_extract_evidence(query, output, response),
                limitations=_extract_limitations(output, confidence),
                inference_ms=elapsed_ms,
                recommendations=[],
                iocs=[],
                mitre_techniques=[],
                severity="UNKNOWN",
            )
        except Exception as exc:
            return ExpertAnalysis(
                expert_id=self.expert_id,
                expert_name=self.expert_name,
                category=self.category,
                status="error",
                confidence=0.0,
                inference_ms=(time.time() - t0) * 1000,
                error=str(exc),
                limitations=["exception_during_analysis"],
            )


class ExpertModelManager:
    def __init__(self, registry):
        self.registry = registry
        self._dynamic: Dict[str, CouncilExpert] = {}
        self._virtual_registered = False

    def register_expert(self, expert: CouncilExpert):
        self._dynamic[expert.expert_id] = expert

    def register_all_virtual_experts(self):
        """Register all 15 virtual expert agents."""
        if self._virtual_registered:
            return
        try:
            from backend.council.virtual_experts import ALL_VIRTUAL_EXPERTS
            for ExpertClass in ALL_VIRTUAL_EXPERTS:
                expert = ExpertClass()
                self._dynamic[expert.expert_id] = expert
            self._virtual_registered = True
        except Exception as exc:
            import traceback
            print(f"[ExpertModelManager] Failed to register virtual experts: {exc}")
            traceback.print_exc()

    def get_expert(self, expert_id: str) -> Optional[CouncilExpert]:
        if expert_id in self._dynamic:
            return self._dynamic[expert_id]
        model = self.registry.get_model(expert_id)
        if model:
            return RegistryCouncilExpert(model)
        return None

    def list_experts(self) -> List[Dict[str, Any]]:
        experts = []
        for expert in self._dynamic.values():
            experts.append({
                "expert_id": expert.expert_id,
                "expert_name": expert.expert_name,
                "category": expert.category,
                "capabilities": expert.capabilities,
                "dynamic": True,
            })
        for model_id in self.registry.list_ids():
            model = self.registry.get_model(model_id)
            if model:
                meta = model.metadata()
                experts.append({
                    "expert_id": meta.model_id,
                    "expert_name": meta.name,
                    "category": meta.category.value,
                    "capabilities": [meta.task, meta.framework],
                    "dynamic": False,
                })
        return experts

    async def run_parallel(self, query: str, expert_ids: List[str], timeout_s: float, context: Optional[Dict] = None) -> List[ExpertAnalysis]:
        tasks = []
        for expert_id in expert_ids:
            expert = self.get_expert(expert_id)
            if expert:
                tasks.append(self._run_one(expert, query, timeout_s, context))
        if not tasks:
            return []
        return list(await asyncio.gather(*tasks))

    async def _run_one(self, expert: CouncilExpert, query: str, timeout_s: float, context: Optional[Dict]) -> ExpertAnalysis:
        t0 = time.time()
        try:
            return await asyncio.wait_for(expert.analyze(query, context), timeout=timeout_s)
        except asyncio.TimeoutError:
            return ExpertAnalysis(
                expert_id=expert.expert_id,
                expert_name=expert.expert_name,
                category=expert.category,
                status="timeout",
                confidence=0.0,
                inference_ms=(time.time() - t0) * 1000,
                error="timeout",
                limitations=["timeout"],
            )


# ── Helper functions ──────────────────────────────────────────────────────────

def _extract_response(output: Dict) -> Any:
    for key in ("response", "prediction", "generated_text", "verdict"):
        if output.get(key) not in (None, ""):
            return output[key]
    return output.get("result", output)


def _extract_confidence(output: Dict) -> float:
    value = output.get("confidence")
    if value is None:
        value = output.get("confidence_pct")
    if value is None:
        value = output.get("threat_score")
    return float(value or 0.0)


def _normalize_confidence(value: float) -> float:
    if 0.0 <= value <= 1.0:
        value *= 100.0
    return max(0.0, min(100.0, value))


def _extract_inference_ms(output: Dict, t0: float) -> float:
    if output.get("inference_ms") is not None:
        return float(output["inference_ms"])
    if output.get("elapsed_s") is not None:
        return float(output["elapsed_s"]) * 1000
    return (time.time() - t0) * 1000


def _extract_conclusion(output: Dict, response: Any) -> str:
    verdict = str(output.get("verdict") or output.get("prediction") or response or "").upper()
    if any(word in verdict for word in ("BLOCK", "PHISH", "MALWARE", "MALICIOUS", "RANSOMWARE")):
        return "BLOCK"
    if any(word in verdict for word in ("ACCEPT", "SAFE", "LEGITIMATE", "BENIGN", "NORMAL")):
        return "ACCEPT"
    return "UNKNOWN"


def _extract_evidence(query: str, output: Dict, response: Any) -> List[str]:
    evidence = []
    if isinstance(output.get("evidence"), list):
        evidence.extend(str(e) for e in output["evidence"])
    text = f"{query} {response}".lower()
    indicators = [
        "phishing", "password", "credential", "powershell", "encodedcommand",
        "ransomware", "cve", "mitre", "sigma", "malware", "urgent", "click",
    ]
    evidence.extend([f"indicator:{term}" for term in indicators if term in text])
    return list(dict.fromkeys(evidence))[:8]


def _extract_limitations(output: Dict, confidence: float) -> List[str]:
    if isinstance(output.get("limitations"), list):
        return [str(x) for x in output["limitations"]]
    limitations = []
    if confidence < 80:
        limitations.append("confidence_below_80")
    if not output.get("evidence"):
        limitations.append("limited_explicit_evidence")
    return limitations
