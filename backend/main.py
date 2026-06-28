#!/usr/bin/env python3
"""SecureRAG Hub - AI Orchestrator Server

Point d'entree du serveur d'orchestration multi-agent.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.gateway.api import SecurityAIGateway
from backend.config import CONFIG
from backend.models_registry.registry import ModelRegistry, MODEL_REGISTRY, get_registry
from backend.models_registry.base_model import ModelStatus
from backend.models_registry.models.base_wrapper import GenericModelWrapper
from backend.models_registry.models.phishing.wrapper import PhishingModelWrapper
from backend.models_registry.downloader import ModelDownloader
from backend.consensus.engine import ConsensusEngine, ModelVote, ConsensusConfig
from backend.council import CouncilConfig, MasterAIOrchestrator

BASE_DIR = Path(__file__).resolve().parent.parent
GATEWAY = SecurityAIGateway()
REGISTRY = get_registry()
DOWNLOADER = ModelDownloader()
CONSENSUS_CONFIG = ConsensusConfig.default()
CONSENSUS = ConsensusEngine(CONSENSUS_CONFIG)
COUNCIL_CONFIG = CouncilConfig.default()
COUNCIL = MasterAIOrchestrator(REGISTRY, COUNCIL_CONFIG)


class OrchestratorHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] [ORCHESTRATOR] {fmt % args}")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _load_all_models(self):
        if not REGISTRY._models:
            for mid, meta in MODEL_REGISTRY.items():
                if mid in ("cysecbert", "phishsense"):
                    wrapper = PhishingModelWrapper(meta)
                    wrapper._status = ModelStatus.LOADED
                else:
                    wrapper = GenericModelWrapper(meta)
                REGISTRY.register_model(wrapper)

    def _handle_model_registry(self, path: str, method: str, body: Dict = None):
        segments = path.split("/")
        if method == "GET":
            if path == "/api/v1/models":
                self._load_all_models()
                models = REGISTRY.list_models()
                self._json(200, {
                    "models": [m.to_dict() for m in models],
                    "total": len(models),
                })
            elif path == "/api/v1/models/summary":
                self._load_all_models()
                self._json(200, REGISTRY.summary())
            elif path.startswith("/api/v1/models/") and path.endswith("/status"):
                mid = segments[4]
                info = REGISTRY.get_info(mid)
                if not info:
                    self._json(404, {"error": f"Model '{mid}' not found"})
                else:
                    self._json(200, info.to_dict())
            elif path.startswith("/api/v1/models/category/"):
                cat = segments[4]
                models = REGISTRY.list_by_category(cat) if hasattr(ModelStatus, cat) else []
                self._json(200, {"category": cat, "models": [m.to_dict() for m in models]})
            else:
                self._json(404, {"error": "Unknown model route"})
        elif method == "POST":
            if path.startswith("/api/v1/models/") and path.endswith("/load"):
                mid = segments[4]
                self._load_all_models()
                model = REGISTRY.get_model(mid)
                if not model:
                    self._json(404, {"error": f"Model '{mid}' not found"})
                    return
                ok = asyncio.run(model.load())
                if ok:
                    REGISTRY.update_status(mid, ModelStatus.LOADED)
                    self._json(200, {"success": True, "model_id": mid, "status": "loaded"})
                else:
                    REGISTRY.update_status(mid, ModelStatus.ERROR)
                    self._json(500, {"success": False, "model_id": mid, "status": "error"})
            elif path.startswith("/api/v1/models/") and path.endswith("/unload"):
                mid = segments[4]
                model = REGISTRY.get_model(mid)
                if not model:
                    self._json(404, {"error": f"Model '{mid}' not found"})
                    return
                ok = asyncio.run(model.unload())
                REGISTRY.update_status(mid, ModelStatus.UNLOADED)
                self._json(200, {"success": ok, "model_id": mid, "status": "unloaded"})
            elif path.startswith("/api/v1/models/") and path.endswith("/predict"):
                mid = segments[4]
                model = REGISTRY.get_model(mid)
                if not model:
                    self._json(404, {"error": f"Model '{mid}' not found"})
                    return
                result = asyncio.run(model.predict(body or {}))
                self._json(200, result)
            elif path == "/api/v1/models/download":
                mid = body.get("model_id", "")
                if mid not in MODEL_REGISTRY:
                    self._json(404, {"error": f"Model '{mid}' not found in registry"})
                    return
                meta = MODEL_REGISTRY[mid]
                ok = DOWNLOADER.download(mid, meta.hf_id, meta.local_path)
                if ok:
                    progress = DOWNLOADER.get_progress(mid)
                    self._json(200, {"success": True, "model_id": mid, "progress": progress.to_dict() if progress else {}})
                else:
                    progress = DOWNLOADER.get_progress(mid)
                    self._json(500, {"success": False, "model_id": mid, "error": progress.error if progress else "Download failed"})
            else:
                self._json(404, {"error": "Unknown model route"})

    def do_GET(self):
        parsed = self._parse_path()
        path = parsed["path"]

        if path == "/" or path == "":
            self._serve_file(BASE_DIR / "web" / "index.html", "text/html; charset=utf-8")
        elif path == "/health":
            self._json(200, {"status": "ok", "service": "security-ai-orchestrator"})
        elif path == "/api/v1/security/consensus":
            self._json(200, {
                "config": CONSENSUS_CONFIG.to_dict(),
                "description": "POST /api/v1/security/consensus avec un body {query, models} pour executer le consensus",
            })
        elif path == "/api/v1/security/council":
            self._load_all_models()
            self._json(200, {
                "config": COUNCIL_CONFIG.to_dict(),
                "experts": COUNCIL.experts.list_experts(),
                "description": "POST /api/v1/security/council avec un body {query, models?, context?} pour executer le AI Security Council",
            })
        elif path.startswith("/api/v1/models"):
            self._handle_model_registry(path, "GET")
        elif path == "/api/v1/security/spec":
            self._json(200, GATEWAY.get_openapi_spec())
        elif path == "/api/v1/security/agents":
            self._json(200, {
                "agents": [
                    "query_classifier", "model_router", "security_rag",
                    "threat_intelligence", "sigma_analysis", "malware_analysis",
                    "incident_response", "evidence_fusion", "securityllm_synthesis",
                    "ai_governance",
                ]
            })
        elif path == "/api/v1/security/workflows":
            from backend.orchestrator.workflow import SECURITY_WORKFLOWS
            self._json(200, {
                "workflows": {k: {"name": v.name, "description": v.description, "category": v.category, "steps": len(v.steps)}
                              for k, v in SECURITY_WORKFLOWS.items()}
            })
        else:
            self._json(404, {"error": "Route non trouvee"})

    def do_POST(self):
        parsed = self._parse_path()
        path = parsed["path"]

        cl = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(cl)
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self._json(400, {"error": "JSON invalide"})
            return

        if path == "/api/v1/security/consensus":
            self._handle_consensus(body)
        elif path == "/api/v1/security/council":
            self._handle_council(body)
        elif path.startswith("/api/v1/models"):
            self._handle_model_registry(path, "POST", body)
        elif path == "/api/v1/security/query":
            result = asyncio.run(GATEWAY.handle_query(body))
            status = 200 if result.get("success", False) else 500
            self._json(status, result)
        else:
            self._json(404, {"error": "Route non trouvee"})

    def _handle_consensus(self, body: Dict):
        query = body.get("query", "").strip()
        if not query:
            self._json(400, {"error": "Query requise"})
            return

        model_inputs = body.get("models", body.get("votes", []))

        self._load_all_models()

        if model_inputs:
            try:
                votes = asyncio.run(self._collect_consensus_votes(query, model_inputs))
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return
        else:
            selected = [{"model_id": mid, "execute": True} for mid in REGISTRY.list_ids()
                        if REGISTRY.get_model(mid) and REGISTRY.get_model(mid).status() == ModelStatus.LOADED]
            votes = asyncio.run(self._collect_consensus_votes(query, selected))

        result = CONSENSUS.compute(query, votes)
        self._json(200, result.to_dict())

    def _handle_council(self, body: Dict):
        query = body.get("query", "").strip()
        if not query:
            self._json(400, {"error": "Query requise"})
            return
        if not COUNCIL_CONFIG.enabled:
            self._json(503, {"error": "AI Security Council disabled"})
            return

        self._load_all_models()
        result = asyncio.run(COUNCIL.run(
            query=query,
            user_role=body.get("user_role", "analyst"),
            context=body.get("context", {}),
            models=body.get("models"),
        ))
        self._json(200, result.to_dict())

    async def _collect_consensus_votes(self, query: str, model_inputs: List[Dict]) -> List[ModelVote]:
        tasks = []
        static_votes = []

        for item in model_inputs:
            mid = item.get("model_id", item.get("id", ""))
            if not mid:
                raise ValueError("Chaque modele doit definir 'model_id' ou 'id'")

            model = REGISTRY.get_model(mid)
            if not model:
                raise ValueError(f"Model '{mid}' not found")

            should_execute = item.get("execute", False)
            has_precomputed_vote = any(k in item for k in ("response", "confidence", "error"))
            if has_precomputed_vote and not should_execute:
                static_votes.append(self._vote_from_payload(model, item))
            else:
                tasks.append(self._execute_model_vote(model, query, item))

        executed = await asyncio.gather(*tasks) if tasks else []
        return static_votes + list(executed)

    def _vote_from_payload(self, model, payload: Dict) -> ModelVote:
        meta = model.metadata()
        return ModelVote(
            model_id=payload.get("model_id", payload.get("id", meta.model_id)),
            model_name=payload.get("model_name", meta.name),
            category=payload.get("category", meta.category.value),
            confidence=self._normalize_confidence(payload.get("confidence", 0.0)),
            weight=1,
            response=payload.get("response"),
            inference_ms=float(payload.get("inference_ms", 0.0)),
            error=payload.get("error"),
        )

    async def _execute_model_vote(self, model, query: str, payload: Dict) -> ModelVote:
        meta = model.metadata()
        t0 = time.time()
        try:
            prediction = await asyncio.wait_for(
                model.predict({"text": query, "query": query}),
                timeout=float(payload.get("timeout_s", CONSENSUS_CONFIG.model_timeout_s)),
            )
            inference_ms = self._extract_inference_ms(prediction, t0)
            error = prediction.get("error")
            return ModelVote(
                model_id=meta.model_id,
                model_name=meta.name,
                category=meta.category.value,
                confidence=self._normalize_confidence(self._extract_confidence(prediction)),
                weight=1,
                response=self._extract_response(prediction),
                inference_ms=inference_ms,
                error=error,
            )
        except asyncio.TimeoutError:
            return ModelVote(
                model_id=meta.model_id,
                model_name=meta.name,
                category=meta.category.value,
                confidence=0.0,
                weight=1,
                response=None,
                inference_ms=(time.time() - t0) * 1000,
                error="timeout",
            )
        except Exception as exc:
            return ModelVote(
                model_id=meta.model_id,
                model_name=meta.name,
                category=meta.category.value,
                confidence=0.0,
                weight=1,
                response=None,
                inference_ms=(time.time() - t0) * 1000,
                error=str(exc),
            )

    def _extract_confidence(self, prediction: Dict) -> float:
        value = prediction.get("confidence")
        if value is None:
            value = prediction.get("confidence_pct")
        if value is None:
            value = prediction.get("threat_score")
        if value is None and isinstance(prediction.get("result"), dict):
            value = prediction["result"].get("confidence")
        return float(value or 0.0)

    def _normalize_confidence(self, value: Any) -> float:
        confidence = float(value or 0.0)
        if 0.0 <= confidence <= 1.0:
            confidence *= 100.0
        return max(0.0, min(100.0, confidence))

    def _extract_response(self, prediction: Dict) -> Any:
        for key in ("response", "prediction", "generated_text", "verdict"):
            if prediction.get(key) not in (None, ""):
                return prediction[key]
        if prediction.get("result") not in (None, ""):
            return prediction["result"]
        return None

    def _extract_inference_ms(self, prediction: Dict, t0: float) -> float:
        if prediction.get("inference_ms") is not None:
            return float(prediction["inference_ms"])
        if prediction.get("elapsed_s") is not None:
            return float(prediction["elapsed_s"]) * 1000
        return (time.time() - t0) * 1000

    def _parse_path(self) -> Dict:
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        return {"path": parsed.path.rstrip("/"), "query": parsed.query}

    def _json(self, status: int, data: Any):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, fp: Path, ctype: str):
        if not fp.exists():
            self._json(404, {"error": "Fichier non trouve"})
            return
        content = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)


def main():
    port = int(os.getenv("ORCHESTRATOR_PORT", "8080"))
    
    # ── Initialisation et chargement automatique de tous les modèles ──
    for mid, meta in MODEL_REGISTRY.items():
        if mid in ("cysecbert", "phishsense", "qwen2_5_1_5b", "smollm2_1_7b"):
            wrapper = PhishingModelWrapper(meta)
            wrapper._status = ModelStatus.LOADED
        else:
            wrapper = GenericModelWrapper(meta)
        REGISTRY.register_model(wrapper)
                
    server = HTTPServer(("0.0.0.0", port), OrchestratorHandler)

    print(f"\n{'='*80}")
    print(f"  SecureRAG Hub — AI Orchestrator")
    print(f"  Gateway   : http://localhost:{port}/api/v1/security/query")
    print(f"  Health    : http://localhost:{port}/health")
    print(f"  Spec      : http://localhost:{port}/api/v1/security/spec")
    print(f"  Agents    : {len(GATEWAY.orchestrator.agents)} agents disponibles")
    print(f"  Models    : {len(MODEL_REGISTRY)} modeles dans le registre")
    print(f"  Registry  : http://localhost:{port}/api/v1/models")
    print(f"  Consensus : http://localhost:{port}/api/v1/security/consensus")
    print(f"  Council   : http://localhost:{port}/api/v1/security/council")
    print(f"{'='*80}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Orchestrateur arrete.")
        sys.exit(0)


if __name__ == "__main__":
    main()
