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

# ── Email Security (existing) ──
_reg("cysecbert", "CySecBERT", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "TUKE-Phishing-Detection/CySecBERT", "models/phishing/cysecbert",
    "110M", 0.110, 520, False,
    "BERT fine-tuné pour la détection de phishing et emails malveillants", "phishing", "Mail", True)

_reg("secbert", "SecBERT", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "TUKE-Phishing-Detection/SecBERT", "models/phishing/secbert",
    "110M", 0.110, 520, False,
    "BERT spécialisé dans la sécurité informatique - classification de texte", "phishing", "Shield", True)

_reg("phishsense", "PhishSense 1B", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "microsoft/PhishSense-1B", "models/phishing/phishsense",
    "1B", 1.0, 2100, True,
    "LLM de 1B paramètres spécialisé dans la détection de phishing avancé", "phishing", "Fish", True)

_reg("securityllm", "SecurityLLM", ModelCategory.EMAIL_SECURITY, "1.0", "PyTorch",
    "microsoft/SecurityLLM", "models/phishing/securityllm",
    "7B", 7.0, 14200, True,
    "LLM généraliste de sécurité fine-tuné pour l'analyse de menaces", "security", "Bot", True)

_reg("security_rag", "Security RAG", ModelCategory.RAG, "2.0", "Haystack",
    "sentence-transformers/all-MiniLM-L6-v2", "models/rag/security_rag",
    "80M", 0.080, 400, False,
    "Moteur RAG avec base de connaissances MITRE ATT&CK, CVE, OWASP, Sigma", "rag", "BookOpen", True)

# ── Web Security ──
_reg("codebert", "CodeBERT", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "microsoft/codebert-base", "models/web_security/codebert",
    "125M", 0.125, 530, False,
    "BERT pré-entraîné sur du code source - détection de vulnérabilités web", "code_analysis", "Code", True)

_reg("graphcodebert", "GraphCodeBERT", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "microsoft/graphcodebert-base", "models/web_security/graphcodebert",
    "125M", 0.125, 540, False,
    "BERT avec flux de données pour analyse structurelle de code", "code_analysis", "GitBranch", True)

_reg("unixcoder", "UniXcoder", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "microsoft/unixcoder-base", "models/web_security/unixcoder",
    "125M", 0.125, 540, False,
    "Modèle unifié pour compréhension et génération de code multi-langage", "code_analysis", "Code2", True)

_reg("vulberta", "VulBERTa", ModelCategory.WEB_SECURITY, "1.0", "PyTorch",
    "ICL-ml/VulBERTa", "models/web_security/vulberta",
    "125M", 0.125, 530, False,
    "RoBERTa fine-tuné sur CVE pour détection de code vulnérable", "vulnerability", "AlertTriangle", True)

# ── Network Security ──
_reg("netbert", "NetBERT", ModelCategory.NETWORK_SECURITY, "1.0", "PyTorch",
    "icsi/netbert", "models/network/netbert",
    "110M", 0.110, 520, False,
    "BERT pré-entraîné sur trafic réseau - classification de flux", "network_traffic", "Radio", True)

_reg("flowtransformer", "FlowTransformer", ModelCategory.NETWORK_SECURITY, "1.0", "PyTorch",
    "icsi/flow-transformer", "models/network/flowtransformer",
    "85M", 0.085, 450, False,
    "Transformer pour analyse séquentielle de flux réseau", "network_traffic", "Activity", True)

_reg("dnsbert", "DNSBERT", ModelCategory.NETWORK_SECURITY, "1.0", "PyTorch",
    "icsi/dns-bert", "models/network/dnsbert",
    "110M", 0.110, 520, False,
    "BERT spécialisé dans la détection d'anomalies DNS", "dns_analysis", "Globe", True)

# ── Malware ──
_reg("malbert", "MalBERT", ModelCategory.MALWARE, "1.0", "PyTorch",
    "malbert/malbert-base", "models/malware/malbert",
    "110M", 0.110, 530, False,
    "BERT fine-tuné sur la classification de malware par analyse de binaire", "malware_classification", "Bug", True)

_reg("malconv", "MalConv", ModelCategory.MALWARE, "2.0", "PyTorch",
    "malconv/malconv2", "models/malware/malconv",
    "12M", 0.012, 350, False,
    "CNN 1D pour détection de malware directement depuis les bytes PE", "malware_detection", "Terminal", True)

_reg("ember", "EMBER", ModelCategory.MALWARE, "2.0", "LightGBM",
    "endgame/ember-model", "models/malware/ember",
    "8M", 0.008, 150, False,
    "Gradient boosting pour classification de malware basée sur features statiques", "malware_detection", "BarChart3", True)

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

_reg("threatbert", "ThreatBERT", ModelCategory.THREAT_INTELLIGENCE, "1.0", "PyTorch",
    "da09/ThreatBERT", "models/threat/threatbert",
    "110M", 0.110, 530, False,
    "BERT pour enrichissement et classification de menaces", "threat_enrichment", "Shield", True)

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

# ── Sentiment Analysis ──
_reg("distilroberta_sentiment", "DistilRoBERTa Sentiment", ModelCategory.SENTIMENT, "1.0", "PyTorch",
    "cardiffnlp/twitter-roberta-base-sentiment-latest", "models/sentiment/distilroberta",
    "125M", 0.125, 530, False,
    "RoBERTa distillée pour analyse de sentiment dans des messages (social engineering)", "sentiment_analysis", "Smile", True)

_reg("goemotions", "GoEmotions BERT", ModelCategory.SENTIMENT, "1.0", "PyTorch",
    "monologg/bert-base-cased-goemotions", "models/sentiment/goemotions",
    "110M", 0.110, 520, False,
    "BERT fine-tuné sur GoEmotions - détection multi-émotions pour analyse psychologique", "emotion_detection", "Heart", True)

# ── Embeddings ──
_reg("all_minilm_l6_v2", "all-MiniLM-L6-v2", ModelCategory.EMBEDDINGS, "2.0", "PyTorch",
    "sentence-transformers/all-MiniLM-L6-v2", "models/embeddings/all_minilm",
    "80M", 0.080, 400, False,
    "MiniLM léger pour embeddings de phrases - similarité sémantique", "embedding", "Layers", True)

_reg("bge_base", "BGE-base", ModelCategory.EMBEDDINGS, "1.0", "PyTorch",
    "BAAI/bge-base-en-v1.5", "models/embeddings/bge_base",
    "110M", 0.110, 530, False,
    "Embedding multilingue haute performance pour RAG et retrieval", "embedding", "Database", True)

_reg("e5_base", "E5-base", ModelCategory.EMBEDDINGS, "1.0", "PyTorch",
    "intfloat/e5-base-v2", "models/embeddings/e5_base",
    "110M", 0.110, 530, False,
    "Embedding pour retrieval avec instructions - idéal pour recherche sémantique", "embedding", "Search", True)

# ── OCR ──
_reg("paddleocr", "PaddleOCR", ModelCategory.OCR, "4.0", "PaddlePaddle",
    "PaddleOCR-json/PaddleOCR", "models/ocr/paddleocr",
    "14M", 0.014, 800, False,
    "Système OCR multi-langue basé sur PaddleOCR - extraction de texte dans les images", "ocr", "ScanText", True)

_reg("trocr_small", "TrOCR-small", ModelCategory.OCR, "1.0", "PyTorch",
    "microsoft/trocr-small-handwritten", "models/ocr/trocr",
    "60M", 0.060, 400, False,
    "Transformer pour OCR - reconnaissance de texte imprimé et manuscrit", "ocr", "FileText", True)

# ── Vision ──
_reg("mobilesam", "MobileSAM", ModelCategory.VISION, "1.0", "PyTorch",
    "wkcn/mobilesam-vit-tiny", "models/vision/mobilesam",
    "12M", 0.012, 350, False,
    "Version mobile légère de SAM - segmentation d'objets dans les images", "segmentation", "Image", True)

_reg("yolov11n", "YOLOv11n", ModelCategory.VISION, "11.0", "PyTorch",
    "ultralytics/yolov11n", "models/vision/yolov11n",
    "2.6M", 0.0026, 200, False,
    "Détection d'objets ultra-légère nano - identification de menaces visuelles", "object_detection", "Camera", True)

# ── Lightweight LLM ──
_reg("qwen2_5_1_5b", "Qwen2.5-1.5B-Instruct", ModelCategory.LLM, "2.5", "PyTorch",
    "Qwen/Qwen2.5-1.5B-Instruct", "models/llm/qwen2.5-1.5b",
    "1.5B", 1.5, 3500, True,
    "LLM instructif de 1.5B paramètres - génération de rapports de sécurité", "text_generation", "MessageSquare", True)

_reg("smollm2_1_7b", "SmolLM2-1.7B", ModelCategory.LLM, "2.0", "PyTorch",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct", "models/llm/smollm2-1.7b",
    "1.7B", 1.7, 3800, True,
    "LLM instructif léger 1.7B - analyse et synthèse de menaces", "text_generation", "Brain", True)


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
