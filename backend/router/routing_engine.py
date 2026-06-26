import json
import aiohttp
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.config import CONFIG


@dataclass
class InferenceRequest:
    model_id: str
    prompt: str
    max_new_tokens: int = 200
    priority: int = 5

@dataclass
class InferenceResponse:
    model_id: str
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    latency_ms: float = 0.0


class RoutingEngine:
    def __init__(self):
        self.inference_url = CONFIG.inference_server_url
        self.model_paths = self._build_model_paths()

    def _build_model_paths(self) -> Dict[str, str]:
        return {
            "cysecbert": "outputs/cysecbert-phishing",
            "secbert": "outputs/secbert-phishing",
            "phishsense": "outputs/phishsense-targeted-lora",
            "phishsense-merged": "outputs/phishsense-merged",
            "securityllm": "outputs/securityllm-targeted-lora",
            "securityllm-merged": "outputs/securityllm-merged",
        }

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        import time
        t0 = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": request.model_id,
                    "prompt": request.prompt,
                    "max_new_tokens": request.max_new_tokens,
                }
                async with session.post(
                    f"{self.inference_url}/api/predict",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        elapsed = (time.time() - t0) * 1000
                        return InferenceResponse(
                            model_id=request.model_id,
                            success=True,
                            data=data,
                            latency_ms=round(elapsed, 2),
                        )
                    else:
                        error_text = await resp.text()
                        return InferenceResponse(
                            model_id=request.model_id,
                            success=False,
                            error=f"HTTP {resp.status}: {error_text[:200]}",
                            latency_ms=round((time.time() - t0) * 1000, 2),
                        )
        except asyncio.TimeoutError:
            return InferenceResponse(
                model_id=request.model_id,
                success=False,
                error="Timeout apres 120s",
                latency_ms=120000,
            )
        except Exception as e:
            return InferenceResponse(
                model_id=request.model_id,
                success=False,
                error=str(e),
                latency_ms=round((time.time() - t0) * 1000, 2),
            )

    async def infer_batch(self, requests: List[InferenceRequest]) -> List[InferenceResponse]:
        bert_requests = [r for r in requests if r.model_id in ("cysecbert", "secbert")]
        llm_requests = [r for r in requests if r.model_id not in ("cysecbert", "secbert")]

        results = []

        if bert_requests:
            bert_tasks = [self.infer(r) for r in bert_requests]
            bert_results = await asyncio.gather(*bert_tasks, return_exceptions=True)
            for r in bert_results:
                if isinstance(r, InferenceResponse):
                    results.append(r)
                elif isinstance(r, Exception):
                    results.append(InferenceResponse(model_id="bert", success=False, error=str(r)))

        for r in llm_requests:
            result = await self.infer(r)
            results.append(result)

        return results

    async def load_model(self, model_id: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.inference_url}/api/load-model",
                    json={"model": model_id},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def get_models_status(self) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.inference_url}/api/models", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("models", [])
        except Exception:
            pass
        return []
