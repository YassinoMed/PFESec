#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inference_server.py — Serveur d'inférence GPU multi-modèles pour SecureRAG Hub.

Charge TOUS les modèles disponibles en VRAM en même temps (ou séquentiellement si insuffisant)
et expose une API REST pour :
  - GET  /api/models          → liste + statut de chaque modèle
  - POST /api/predict         → inférence sur UN modèle
  - POST /api/predict-all     → inférence simultanée sur TOUS les modèles (scoring Accept/Block)
  - GET  /api/gpu-status      → état VRAM GPU en temps réel
  - GET  /                    → interface web

Usage :
  python inference_server.py
  python inference_server.py --port 8000 --lazy   # charge les modèles à la demande
"""

import os
import gc
import re
import sys
import json
import time
import math
import threading
import argparse
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── HuggingFace Offline ────────────────────────────────────────────────────────
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import torch
import numpy as np

BASE_DIR = Path(__file__).resolve().parent

# ── Chemins des modèles ────────────────────────────────────────────────────────
OUTPUTS = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "cysecbert": {
        "name": "CySecBERT Classifier",
        "type": "bert",
        "path": OUTPUTS / "cysecbert-phishing",
        "base_path": MODELS_DIR / "CySecBERT",
        "description": "BERT fine-tuné — détection phishing / email malveillant",
        "task": "phishing",
        "icon": "🛡️",
    },
    "secbert": {
        "name": "SecBERT Classifier",
        "type": "bert",
        "path": OUTPUTS / "secbert-phishing",
        "base_path": MODELS_DIR / "SecBERT",
        "description": "SecBERT cybersécurité — classification phishing",
        "task": "phishing",
        "icon": "🔒",
    },
    "phishsense": {
        "name": "Llama PhishSense (LoRA)",
        "type": "lora",
        "path": OUTPUTS / "phishsense-targeted-lora",
        "base_path": MODELS_DIR / "Llama-Phishsense-1B",
        "description": "Llama 1B + LoRA — analyse sémantique phishing",
        "task": "phishing",
        "icon": "🎣",
    },
    "phishsense-merged": {
        "name": "Llama PhishSense (Merged)",
        "type": "llm",
        "path": OUTPUTS / "phishsense-merged",
        "base_path": MODELS_DIR / "Llama-Phishsense-1B",
        "description": "Llama 1B fusionné — inférence phishing directe",
        "task": "phishing",
        "icon": "🔍",
    },
    "securityllm": {
        "name": "SecurityLLM (LoRA)",
        "type": "lora",
        "path": OUTPUTS / "securityllm-targeted-lora",
        "base_path": MODELS_DIR / "SecurityLLM",
        "description": "SecurityLLM + LoRA — analyse SOC & règles détection",
        "task": "soc",
        "icon": "🧠",
    },
}

# ── Chargement dynamique des poids ────────────────────────────────────────────
_loaded_models: Dict[str, Dict[str, Any]] = {}
_load_lock = threading.Lock()


def _get_status(model_id: str) -> str:
    cfg = MODEL_REGISTRY[model_id]
    path = cfg["path"]
    mtype = cfg["type"]
    if mtype in ("bert",):
        if (path / "config.json").exists() and (
            (path / "model.safetensors").exists() or (path / "pytorch_model.bin").exists()
        ):
            return "READY"
        return "NOT_TRAINED"
    elif mtype == "lora":
        if (path / "adapter_config.json").exists():
            return "READY"
        return "NOT_TRAINED"
    elif mtype == "llm":
        if (path / "config.json").exists():
            return "READY"
        return "NOT_TRAINED"
    return "UNKNOWN"


def _detect_dtype():
    if torch.cuda.is_available():
        try:
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
        except Exception:
            pass
        return torch.float16
    return torch.float32


def _load_bert(model_id: str, cfg: Dict) -> Dict:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    path = cfg["path"]
    print(f"  [LOAD] {model_id} — BERT classifier depuis {path}")
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForSequenceClassification.from_pretrained(
        str(path),
        local_files_only=True,
        torch_dtype=torch.float32,
    ).to(device).eval()
    label_map = None
    try:
        raw = json.loads((path / "config.json").read_text(encoding="utf-8"))
        label_map = raw.get("id2label", None)
        if label_map:
            label_map = {int(k): v for k, v in label_map.items()}
    except Exception:
        pass
    print(f"  [OK] {model_id} chargé sur {device.upper()}")
    return {"model": model, "tokenizer": tokenizer, "device": device, "label_map": label_map}


def _load_lora(model_id: str, cfg: Dict) -> Dict:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    base_path = cfg["base_path"]
    adapter_path = cfg["path"]
    print(f"  [LOAD] {model_id} — LLM+LoRA base={base_path.name}, adapter={adapter_path.name}")
    dtype = _detect_dtype()
    device_map = "auto" if torch.cuda.is_available() else None
    
    # Gestion sécurisée du tokenizer Mistral avec fix_mistral_regex=True
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(base_path), local_files_only=True, trust_remote_code=True, fix_mistral_regex=True)
    except TypeError:
        tokenizer = AutoTokenizer.from_pretrained(str(base_path), local_files_only=True, trust_remote_code=True)
        
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = AutoModelForCausalLM.from_pretrained(
        str(base_path), local_files_only=True, trust_remote_code=True,
        torch_dtype=dtype, device_map=device_map,
    )
    model = PeftModel.from_pretrained(base_model, str(adapter_path), local_files_only=True)
    model.eval()
    device = next(model.parameters()).device.type
    print(f"  [OK] {model_id} (LoRA) chargé sur {device.upper()}")
    return {"model": model, "tokenizer": tokenizer, "device": device, "label_map": None}


def _load_llm(model_id: str, cfg: Dict) -> Dict:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    path = cfg["path"]
    print(f"  [LOAD] {model_id} — LLM merged depuis {path}")
    dtype = _detect_dtype()
    device_map = "auto" if torch.cuda.is_available() else None
    
    # Gestion sécurisée du tokenizer Mistral avec fix_mistral_regex=True
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=True, fix_mistral_regex=True)
    except TypeError:
        tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=True)
        
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        str(path), local_files_only=True, trust_remote_code=True,
        torch_dtype=dtype, device_map=device_map,
    )
    model.eval()
    device = next(model.parameters()).device.type
    print(f"  [OK] {model_id} (LLM) chargé sur {device.upper()}")
    return {"model": model, "tokenizer": tokenizer, "device": device, "label_map": None}


def load_model(model_id: str) -> Optional[Dict]:
    """Charge un modèle si pas encore en mémoire. Thread-safe."""
    with _load_lock:
        if model_id in _loaded_models:
            return _loaded_models[model_id]
        cfg = MODEL_REGISTRY.get(model_id)
        if not cfg:
            return None
        status = _get_status(model_id)
        if status not in ("READY",):
            print(f"  [SKIP] {model_id} : statut {status}")
            return None
        try:
            mtype = cfg["type"]
            if mtype == "bert":
                loaded = _load_bert(model_id, cfg)
            elif mtype == "lora":
                loaded = _load_lora(model_id, cfg)
            elif mtype == "llm":
                loaded = _load_llm(model_id, cfg)
            else:
                return None
            _loaded_models[model_id] = loaded
            return loaded
        except Exception as e:
            print(f"  [ERROR] Impossible de charger {model_id}: {e}")
            return None


def load_all_models():
    """Charge tous les modèles READY en VRAM."""
    print("\n" + "="*80)
    print("  CHARGEMENT DE TOUS LES MODÈLES EN VRAM (GPU)")
    print("="*80)
    ready = [mid for mid in MODEL_REGISTRY if _get_status(mid) == "READY"]
    print(f"  Modèles READY détectés : {ready}\n")
    for mid in ready:
        try:
            load_model(mid)
        except Exception as e:
            print(f"  [ERROR] {mid}: {e}")
    print(f"\n  Modèles chargés en mémoire : {list(_loaded_models.keys())}")
    print("="*80 + "\n")


# ── Inférence ─────────────────────────────────────────────────────────────────

PHISHING_PROMPT_TEMPLATE = """### System:
Tu es un assistant de cybersécurité défensif expert en détection de phishing et d'emails malveillants.
Analyse le contenu suivant et donne un verdict CLAIR: PHISHING ou SAFE.
Explique brièvement les indicateurs détectés.

### User:
{text}

### Assistant:
Verdict:"""

SOC_PROMPT_TEMPLATE = """### System:
Tu es un analyste SOC expert en cybersécurité défensive. Analyse la menace ou le log suivant.
Donne une évaluation de risque: BLOCK (menace confirmée/probable) ou ACCEPT (activité légitime).
Explique brièvement ton raisonnement.

### User:
{text}

### Assistant:
Évaluation:"""


def _infer_bert(loaded: Dict, text: str, cfg: Dict) -> Dict:
    model = loaded["model"]
    tokenizer = loaded["tokenizer"]
    device = loaded["device"]
    label_map = loaded["label_map"]

    inputs = tokenizer(
        text, truncation=True, max_length=512, return_tensors="pt", padding=True
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

    pred_id = int(np.argmax(probs))
    pred_label = label_map.get(pred_id, str(pred_id)) if label_map else str(pred_id)
    confidence = float(probs[pred_id])

    all_probs = {}
    if label_map:
        for i, p in enumerate(probs):
            all_probs[label_map.get(i, str(i))] = float(p)
    else:
        for i, p in enumerate(probs):
            all_probs[str(i)] = float(p)

    is_phishing = any(kw in pred_label.lower() for kw in ["phish", "malicious", "spam", "unsafe"])
    verdict = "BLOCK" if is_phishing else "ACCEPT"
    score = confidence if is_phishing else (1.0 - confidence)

    return {
        "predicted": True,
        "prediction": pred_label,
        "confidence": confidence,
        "probabilities": all_probs,
        "verdict": verdict,
        "threat_score": round(score * 100, 1),
        "type": "classification",
    }


def _infer_llm(loaded: Dict, text: str, cfg: Dict, max_new_tokens: int = 64) -> Dict:
    model = loaded["model"]
    tokenizer = loaded["tokenizer"]
    task = cfg.get("task", "phishing")

    if task == "soc":
        prompt = SOC_PROMPT_TEMPLATE.format(text=text[:1500])
    else:
        prompt = PHISHING_PROMPT_TEMPLATE.format(text=text[:1500])

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1800)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            use_cache=True,
            num_beams=1,
            pad_token_id=tokenizer.eos_token_id,
        )

    gen_only = output_ids[0][inputs["input_ids"].shape[1]:]
    generated = tokenizer.decode(gen_only, skip_special_tokens=True).strip()

    # Extraire le verdict
    verdict = "UNKNOWN"
    threat_score = 50.0
    low_gen = generated.lower()
    if any(kw in low_gen for kw in ["block", "phishing", "malicious", "suspect", "dangereux", "menace"]):
        verdict = "BLOCK"
        threat_score = 85.0
    elif any(kw in low_gen for kw in ["accept", "safe", "légitime", "legitime", "normal", "bénin", "benin"]):
        verdict = "ACCEPT"
        threat_score = 15.0

    return {
        "predicted": True,
        "prediction": generated,
        "verdict": verdict,
        "threat_score": threat_score,
        "type": "generative",
        "confidence": None,
    }


def run_inference(model_id: str, text: str, max_new_tokens: int = 64) -> Dict:
    """Lance l'inférence sur un modèle. Le charge si nécessaire."""
    t0 = time.time()
    cfg = MODEL_REGISTRY.get(model_id)
    if not cfg:
        return {"error": f"Modèle '{model_id}' inconnu", "model_id": model_id}

    status = _get_status(model_id)
    if status != "READY":
        return {"error": f"Modèle non entraîné (statut: {status})", "model_id": model_id, "status": status}

    loaded = load_model(model_id)
    if loaded is None:
        return {"error": "Impossible de charger le modèle", "model_id": model_id}

    try:
        mtype = cfg["type"]
        if mtype == "bert":
            result = _infer_bert(loaded, text, cfg)
        elif mtype in ("lora", "llm"):
            result = _infer_llm(loaded, text, cfg, max_new_tokens=max_new_tokens)
        else:
            return {"error": f"Type inconnu: {mtype}", "model_id": model_id}

        result["model_id"] = model_id
        result["model_name"] = cfg["name"]
        result["model_type"] = mtype
        result["elapsed_s"] = round(time.time() - t0, 2)
        result["icon"] = cfg.get("icon", "🤖")
        return result
    except Exception as e:
        return {"error": str(e), "model_id": model_id, "elapsed_s": round(time.time() - t0, 2)}


def run_all_inference(text: str, max_new_tokens: int = 64) -> List[Dict]:
    """Lance l'inférence en parallèle sur tous les modèles READY."""
    ready_ids = [mid for mid in MODEL_REGISTRY if _get_status(mid) == "READY"]
    results = []

    # BERT models en parallèle (légers), LLM en séquentiel (VRAM)
    bert_ids = [mid for mid in ready_ids if MODEL_REGISTRY[mid]["type"] == "bert"]
    llm_ids = [mid for mid in ready_ids if MODEL_REGISTRY[mid]["type"] in ("lora", "llm")]

    # BERT en threads parallèles
    if bert_ids:
        with ThreadPoolExecutor(max_workers=len(bert_ids)) as ex:
            futures = {ex.submit(run_inference, mid, text, max_new_tokens): mid for mid in bert_ids}
            for f in as_completed(futures):
                results.append(f.result())

    # LLM en séquentiel pour préserver la VRAM
    for mid in llm_ids:
        results.append(run_inference(mid, text, max_new_tokens))

    # Trier par model_id pour un affichage stable
    order = list(MODEL_REGISTRY.keys())
    results.sort(key=lambda r: order.index(r.get("model_id", "")) if r.get("model_id", "") in order else 99)

    # Calcul du score de consensus
    verdicts = [r.get("verdict") for r in results if r.get("verdict") in ("BLOCK", "ACCEPT")]
    n_block = verdicts.count("BLOCK")
    n_accept = verdicts.count("ACCEPT")
    n_total = len(verdicts)

    consensus = "BLOCK" if n_block > n_accept else ("ACCEPT" if n_accept > n_block else "UNCERTAIN")
    consensus_pct = round((max(n_block, n_accept) / n_total * 100) if n_total > 0 else 0, 1)

    return {
        "results": results,
        "consensus": {
            "verdict": consensus,
            "block_votes": n_block,
            "accept_votes": n_accept,
            "total_votes": n_total,
            "confidence_pct": consensus_pct,
        },
        "text_preview": text[:120] + ("..." if len(text) > 120 else ""),
        "timestamp": datetime.now().isoformat(),
    }


# ── GPU Status ─────────────────────────────────────────────────────────────────

def get_gpu_status() -> Dict:
    if not torch.cuda.is_available():
        return {"available": False, "message": "Aucun GPU CUDA disponible"}

    devices = []
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        total = props.total_memory
        allocated = torch.cuda.memory_allocated(i)
        reserved = torch.cuda.memory_reserved(i)
        free = total - reserved
        devices.append({
            "index": i,
            "name": props.name,
            "total_gb": round(total / 1e9, 2),
            "allocated_gb": round(allocated / 1e9, 2),
            "reserved_gb": round(reserved / 1e9, 2),
            "free_gb": round(free / 1e9, 2),
            "utilization_pct": round(allocated / total * 100, 1),
        })

    return {
        "available": True,
        "devices": devices,
        "loaded_models": list(_loaded_models.keys()),
        "cuda_version": torch.version.cuda,
    }


# ── HTTP Handler ───────────────────────────────────────────────────────────────

class InferenceHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {fmt % args}")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", ""):
            self._serve_file(BASE_DIR / "web" / "index.html", "text/html; charset=utf-8")
        elif path.startswith("/web/"):
            fp = BASE_DIR / path.lstrip("/")
            self._serve_file(fp, self._mime(fp))
        elif path == "/api/models":
            models_info = []
            for mid, cfg in MODEL_REGISTRY.items():
                status = _get_status(mid)
                models_info.append({
                    "id": mid,
                    "name": cfg["name"],
                    "type": cfg["type"],
                    "description": cfg["description"],
                    "task": cfg.get("task", "unknown"),
                    "status": status,
                    "loaded": mid in _loaded_models,
                    "icon": cfg.get("icon", "🤖"),
                    "path": str(cfg["path"]),
                })
            self._json(200, {"models": models_info})
        elif path == "/api/gpu-status":
            self._json(200, get_gpu_status())
        elif path == "/api/test-scripts":
            self._handle_list_scripts()
        elif path == "/api/test-scripts/view":
            qs = urllib.parse.parse_qs(parsed.query)
            name = qs.get("name", [None])[0]
            if name:
                self._handle_view_script(name)
            else:
                self._json(400, {"error": "Paramètre 'name' requis"})
        else:
            self._json(404, {"error": "Route non trouvée"})

    def do_POST(self):
        cl = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(cl)
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self._json(400, {"error": "JSON invalide"})
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/predict":
            model_id = body.get("model")
            text = body.get("prompt", "").strip()
            max_tokens = int(body.get("max_new_tokens", 64))
            if not model_id or not text:
                self._json(400, {"error": "Champs 'model' et 'prompt' requis"})
                return
            result = run_inference(model_id, text, max_new_tokens=max_tokens)
            self._json(200, result)

        elif path == "/api/predict-all":
            text = body.get("prompt", "").strip()
            max_tokens = int(body.get("max_new_tokens", 64))
            if not text:
                self._json(400, {"error": "Champ 'prompt' requis"})
                return
            result = run_all_inference(text, max_new_tokens=max_tokens)
            self._json(200, result)

        elif path == "/api/load-model":
            model_id = body.get("model")
            if not model_id:
                self._json(400, {"error": "Champ 'model' requis"})
                return
            loaded = load_model(model_id)
            if loaded:
                self._json(200, {"success": True, "model_id": model_id, "message": "Modèle chargé"})
            else:
                self._json(500, {"success": False, "model_id": model_id, "error": "Échec du chargement"})

        elif path == "/api/run-tests":
            # Compatibilité avec l'ancienne interface
            import subprocess
            model_id = body.get("model")
            script_name = body.get("script")
            if not model_id or not script_name:
                self._json(400, {"error": "Modèle et script requis"})
                return
            script_path = BASE_DIR / "tests" / Path(script_name).name
            if not script_path.exists():
                self._json(404, {"error": "Script introuvable"})
                return
            venv_py = BASE_DIR.parent / "myenv" / "Scripts" / "python.exe"
            py = str(venv_py) if venv_py.exists() else sys.executable
            cmd = [py, str(BASE_DIR / "test_runner.py"), "--test-file", str(script_path), "--model", model_id, "--report"]
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=300, check=False)
                stdout = res.stdout.decode("utf-8", errors="replace")
                stderr = res.stderr.decode("utf-8", errors="replace")
                reports_dir = BASE_DIR / "reports"
                report_data = {}
                if reports_dir.exists():
                    rpts = list(reports_dir.glob(f"test_report_{model_id}_*.json"))
                    if rpts:
                        latest = max(rpts, key=os.path.getmtime)
                        report_data = json.loads(latest.read_text(encoding="utf-8"))
                self._json(200, {"success": res.returncode == 0, "stdout": stdout, "stderr": stderr, "report": report_data})
            except subprocess.TimeoutExpired:
                self._json(504, {"error": "Timeout"})
            except Exception as e:
                self._json(500, {"error": str(e)})
        else:
            self._json(404, {"error": "Route non trouvée"})

    def _handle_list_scripts(self):
        tests_dir = BASE_DIR / "tests"
        scripts = []
        if tests_dir.exists():
            for f in tests_dir.glob("*.txt"):
                cat = "Autre"
                if "phishing" in f.name.lower():
                    cat = "Détection Phishing"
                elif "cyber_defense" in f.name.lower():
                    cat = "Analyse SOC"
                elif "robustness" in f.name.lower():
                    cat = "Robustesse & Adversarial"
                scripts.append({"name": f.name, "path": str(f), "category": cat, "size_bytes": f.stat().st_size})
        self._json(200, {"scripts": scripts})

    def _handle_view_script(self, script_name: str):
        script_name = Path(script_name).name
        script_file = BASE_DIR / "tests" / script_name
        if not script_file.exists():
            self._json(404, {"error": "Script introuvable"})
            return
        try:
            sys.path.insert(0, str(BASE_DIR))
            from test_runner import parse_test_file
            tests = parse_test_file(script_file)
            self._json(200, {"script_name": script_name, "total_tests": len(tests), "tests": tests})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, status: int, data: Any):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, fp: Path, ctype: str):
        if not fp.exists():
            self._json(404, {"error": "Fichier non trouvé"})
            return
        content = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _mime(self, fp: Path) -> str:
        ext = fp.suffix.lower()
        return {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
                ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml",
                ".txt": "text/plain"}.get(ext, "application/octet-stream")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SecureRAG Hub — Serveur d'inférence GPU")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--lazy", action="store_true", help="Chargement des modèles à la demande (économise la VRAM)")
    parser.add_argument("--models", nargs="+", help="Charger seulement ces modèles (ex: cysecbert secbert)")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("  SecureRAG Hub — Serveur d'Inférence GPU Multi-Modèles")
    print("="*80)

    if torch.cuda.is_available():
        n = torch.cuda.device_count()
        for i in range(n):
            props = torch.cuda.get_device_properties(i)
            vram = props.total_memory / 1e9
            print(f"  GPU {i}: {props.name} — {vram:.1f} GB VRAM")
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
    else:
        print("  ⚠️  Aucun GPU CUDA — inférence sur CPU (lent pour les LLM)")

    if not args.lazy:
        if args.models:
            for mid in args.models:
                if mid in MODEL_REGISTRY:
                    load_model(mid)
                else:
                    print(f"  [WARN] Modèle inconnu : {mid}")
        else:
            load_all_models()
    else:
        print("  Mode Lazy : modèles chargés à la demande.")

    server = HTTPServer(("", args.port), InferenceHandler)
    print(f"\n  URL : http://localhost:{args.port}/")
    print(f"  API : http://localhost:{args.port}/api/models")
    print(f"  GPU : http://localhost:{args.port}/api/gpu-status")
    print("="*80 + "\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Serveur arrêté.")


if __name__ == "__main__":
    main()
