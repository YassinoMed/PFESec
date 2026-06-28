from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from backend.models_registry.base_model import (
    BaseAIModel, ModelMetadata, ModelInfo, ModelStatus, ModelCategory,
)

MODEL_REGISTRY: Dict[str, ModelMetadata] = {}

def _reg(
    model_id: str, name: str, category: ModelCategory,
    version: str, framework: str, hf_id: str, local_path: str,
    size: str, param_count_b: float, memory_mb: int, gpu_required: bool,
    description: str, task: str, icon: str = "Box",
    repo_available: bool = True, sha256: str = "", homepage: str = "",
) -> ModelMetadata:
    m = ModelMetadata(
        model_id=model_id, name=name, category=category,
        version=version, framework=framework, hf_id=hf_id,
        local_path=local_path, size=size, param_count_b=param_count_b,
        memory_mb=memory_mb, gpu_required=gpu_required,
        description=description, task=task, icon=icon,
        repo_available=repo_available, sha256=sha256, homepage=homepage,
    )
    MODEL_REGISTRY[model_id] = m
    return m

# ── Email Security ──
_reg("cysecbert", "CySecBERT", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "TUKE-Phishing-Detection/CySecBERT", "models/phishing/cysecbert",
    "110M", 0.110, 520, False,
    "BERT fine-tuné pour la détection de phishing et emails malveillants", "phishing", "Mail", True)

_reg("phishsense", "PhishSense 1B", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "microsoft/PhishSense-1B", "models/phishing/phishsense",
    "1B", 1.0, 2100, True,
    "LLM de 1B paramètres spécialisé dans la détection de phishing avancé", "phishing", "Fish", True)

# ── Web Security ──
_reg("codebert", "CodeBERT", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "microsoft/codebert-base", "models/web_security/codebert",
    "125M", 0.125, 530, False,
    "BERT pré-entraîné sur du code source - détection de vulnérabilités web", "code_analysis", "Code", True)

_reg("graphcodebert", "GraphCodeBERT", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "microsoft/graphcodebert-base", "models/web_security/graphcodebert",
    "125M", 0.125, 540, False,
    "BERT avec flux de données pour analyse structurelle de code", "code_analysis", "GitBranch", True)

# ── Network Security ──
_reg("netbert", "NetBERT", ModelCategory.NETWORK_SECURITY, "1.0", "PyTorch",
    "icsi/netbert", "models/network/netbert",
    "110M", 0.110, 520, False,
    "BERT pré-entraîné sur trafic réseau - classification de flux", "network_traffic", "Radio", True)

_reg("flowtransformer", "FlowTransformer", ModelCategory.NETWORK_SECURITY, "1.0", "PyTorch",
    "icsi/flow-transformer", "models/network/flowtransformer",
    "85M", 0.085, 450, False,
    "Transformer pour analyse séquentielle de flux réseau", "network_traffic", "Activity", True)

# ── Malware ──
_reg("malbert", "MalBERT", ModelCategory.MALWARE, "1.0", "PyTorch",
    "malbert/malbert-base", "models/malware/malbert",
    "110M", 0.110, 530, False,
    "BERT fine-tuné sur la classification de malware par analyse de binaire", "malware_classification", "Bug", True)

_reg("malconv", "MalConv", ModelCategory.MALWARE, "2.0", "PyTorch",
    "malconv/malconv2", "models/malware/malconv",
    "12M", 0.012, 350, False,
    "CNN 1D pour détection de malware directement depuis les bytes PE", "malware_detection", "Terminal", True)

# ── Log Analysis ──
_reg("logbert", "LogBERT", ModelCategory.LOGS, "1.0", "PyTorch",
    "logbert/logbert", "models/logs/logbert",
    "110M", 0.110, 530, False,
    "BERT adapté pour la détection d'anomalies dans les logs systèmes", "log_anomaly", "FileText", True)

_reg("deeplog", "DeepLog", ModelCategory.LOGS, "1.0", "PyTorch",
    "deeplog/deeplog", "models/logs/deeplog",
    "8M", 0.008, 200, False,
    "LSTM pour analyse séquentielle de logs et détection de patterns anormaux", "log_anomaly", "List", True)

# ── Threat Intelligence ──
_reg("attackbert", "AttackBERT", ModelCategory.THREAT_INTELLIGENCE, "1.0", "PyTorch",
    "da09/AttackBERT", "models/threat/attackbert",
    "110M", 0.110, 530, False,
    "BERT pour classification de TTPs MITRE ATT&CK et techniques d'attaque", "ttp_classification", "Eye", True)

_reg("iocbert", "IOCBERT", ModelCategory.THREAT_INTELLIGENCE, "1.0", "PyTorch",
    "da09/IOC-BERT", "models/threat/iocbert",
    "110M", 0.110, 530, False,
    "BERT spécialisé dans l'extraction et la classification d'IOCs", "ioc_extraction", "Crosshair", True)

# ── URL Analysis ──
_reg("urlbert", "URLBERT", ModelCategory.URL_ANALYSIS, "1.0", "PyTorch",
    "da09/URLBERT", "models/url/urlbert",
    "110M", 0.110, 530, False,
    "BERT pré-entraîné sur URLs pour détection de sites malveillants", "url_classification", "Link", True)

_reg("urlnet", "URLNet", ModelCategory.URL_ANALYSIS, "1.0", "PyTorch",
    "da09/URLNet", "models/url/urlnet",
    "5M", 0.005, 120, False,
    "CNN pour classification d'URLs malveillantes basée sur caractères", "url_classification", "ExternalLink", True)

# ── OCR ──
_reg("paddleocr", "PaddleOCR", ModelCategory.OCR, "4.0", "PaddlePaddle",
    "PaddleOCR-json/PaddleOCR", "models/ocr/paddleocr",
    "14M", 0.014, 800, False,
    "Système OCR multi-langue basé sur PaddleOCR - extraction de texte dans les images", "ocr", "ScanText", True)

_reg("trocr_small", "TrOCR-small", ModelCategory.OCR, "1.0", "PyTorch",
    "microsoft/trocr-small-handwritten", "models/ocr/trocr",
    "60M", 0.060, 400, False,
    "Transformer pour OCR - reconnaissance de texte imprimé et manuscrit", "ocr", "FileText", True)

# ── LLM ──
_reg("qwen2_5_1_5b", "Qwen2.5-1.5B-Instruct", ModelCategory.LLM, "2.5", "PyTorch",
    "Qwen/Qwen2.5-1.5B-Instruct", "models/llm/qwen2.5-1.5b",
    "1.5B", 1.5, 3500, True,
    "LLM instructif de 1.5B paramètres - génération de rapports de sécurité et raisonnement", "text_generation", "MessageSquare", True)

_reg("smollm2_1_7b", "SmolLM2-1.7B-Instruct", ModelCategory.LLM, "2.0", "PyTorch",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct", "models/llm/smollm2-1.7b",
    "1.7B", 1.7, 3800, True,
    "LLM instructif léger 1.7B - synthèse d'alertes et structuration de playbooks", "text_generation", "Brain", True)


class ModelRegistry:
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
        self._models: Dict[str, BaseAIModel] = {}
        self._model_infos: Dict[str, ModelInfo] = {}
        self._register_all()

    def _register_all(self):
        for mid, meta in MODEL_REGISTRY.items():
            self._model_infos[mid] = ModelInfo(metadata=meta)

    def register_model(self, model: BaseAIModel):
        self._models[model.model_id] = model
        self._model_infos[model.model_id] = model.info

    def get_model(self, model_id: str) -> Optional[BaseAIModel]:
        return self._models.get(model_id)

    def get_info(self, model_id: str) -> Optional[ModelInfo]:
        return self._model_infos.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        return [self._model_infos[mid] for mid in self._model_infos]

    def list_by_category(self, category: ModelCategory) -> List[ModelInfo]:
        return [info for info in self.list_models() if info.metadata.category == category]

    def list_ids(self) -> List[str]:
        return list(self._model_infos.keys())

    def summary(self) -> Dict[str, Any]:
        all_models = self.list_models()
        total = len(all_models)
        loaded = sum(1 for m in all_models if m.status == ModelStatus.LOADED)
        available = sum(1 for m in all_models if m.status in (ModelStatus.LOADED, ModelStatus.UNLOADED))
        error = sum(1 for m in all_models if m.status == ModelStatus.ERROR)
        total_preds = sum(m.total_predictions for m in all_models)
        total_errors = sum(m.total_errors for m in all_models)
        avg_inf = [m.avg_inference_ms for m in all_models if m.avg_inference_ms is not None]
        avg_inference = sum(avg_inf) / len(avg_inf) if avg_inf else 0
        total_memory = sum(m.memory_usage_mb or m.metadata.memory_mb for m in all_models if m.metadata.gpu_required)
        total_memory_cpu = sum(m.memory_usage_mb or m.metadata.memory_mb for m in all_models if not m.metadata.gpu_required)

        cats = {}
        for m in all_models:
            cat = m.metadata.category.value
            if cat not in cats:
                cats[cat] = {"total": 0, "loaded": 0}
            cats[cat]["total"] += 1
            if m.status == ModelStatus.LOADED:
                cats[cat]["loaded"] += 1

        return {
            "total_models": total,
            "loaded": loaded,
            "available": available,
            "error": error,
            "unloaded": total - loaded - error,
            "total_predictions": total_preds,
            "total_errors": total_errors,
            "avg_inference_ms": round(avg_inference, 2),
            "estimated_gpu_memory_mb": total_memory,
            "estimated_cpu_memory_mb": total_memory_cpu,
            "categories": cats,
            "health": "healthy" if error < total * 0.1 else "degraded",
        }

    def update_status(self, model_id: str, status: ModelStatus, **kwargs):
        info = self._model_infos.get(model_id)
        if not info:
            return
        info.status = status
        for k, v in kwargs.items():
            if hasattr(info, k):
                setattr(info, k, v)


def get_registry() -> ModelRegistry:
    return ModelRegistry()
