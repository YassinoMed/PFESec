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
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.gateway.api import SecurityAIGateway
from backend.config import CONFIG
from backend.models_registry.registry import ModelRegistry, MODEL_REGISTRY, get_registry
from backend.models_registry.base_model import ModelStatus
from backend.models_registry.models.base_wrapper import GenericModelWrapper
from backend.models_registry.models.phishing.wrapper import PhishingModelWrapper
from backend.models_registry.downloader import ModelDownloader
from backend.consensus.engine import ConsensusEngine, ModelVote, ConsensusConfig

BASE_DIR = Path(__file__).resolve().parent.parent
GATEWAY = SecurityAIGateway()
REGISTRY = get_registry()
DOWNLOADER = ModelDownloader()
CONSENSUS = ConsensusEngine()
CONSENSUS_CONFIG = ConsensusConfig.default()


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
                if mid in ("cysecbert", "secbert", "phishsense", "securityllm", "security_rag"):
                    wrapper = PhishingModelWrapper(meta)
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
        votes = []

        self._load_all_models()

        if model_inputs:
            for m in model_inputs:
                mid = m.get("model_id", m.get("id", ""))
                model = REGISTRY.get_model(mid)
                if not model:
                    self._json(400, {"error": f"Model '{mid}' not found"})
                    return
                result = asyncio.run(model.predict({"text": query}))
                confidence = float(m.get("confidence", result.get("confidence", result.get("result", {}).get("confidence", 85.0))))
                response_text = m.get("response", result.get("prediction", result.get("result", str(result))))
                votes.append(ModelVote(
                    model_id=mid,
                    model_name=model.metadata().name,
                    category=model.metadata().category.value,
                    confidence=confidence,
                    weight=1,
                    response=response_text,
                    inference_ms=float(m.get("inference_ms", result.get("elapsed_s", 0.01))) * 1000,
                    error=m.get("error", result.get("error")),
                ))
        else:
            import random
            for mid, meta in MODEL_REGISTRY.items():
                votes.append(ModelVote(
                    model_id=mid,
                    model_name=meta.name,
                    category=meta.category.value,
                    confidence=round(random.uniform(70, 99), 1),
                    weight=1,
                    response=f"Analyse par {meta.name}",
                    inference_ms=round(random.uniform(5, 500), 2),
                ))

        result = CONSENSUS.compute(query, votes)
        self._json(200, result.to_dict())

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
    print(f"{'='*80}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Orchestrateur arrete.")
        sys.exit(0)


if __name__ == "__main__":
    main()
