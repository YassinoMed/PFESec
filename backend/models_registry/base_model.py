from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class ModelStatus(str, Enum):
    UNLOADED = "unloaded"
    LOADED = "loaded"
    LOADING = "loading"
    UNLOADING = "unloading"
    DOWNLOADING = "downloading"
    DOWNLOAD_PENDING = "download_pending"
    ERROR = "error"
    NOT_FOUND = "not_found"


class ModelCategory(str, Enum):
    EMAIL_SECURITY = "email_security"
    WEB_SECURITY = "web_security"
    NETWORK_SECURITY = "network_security"
    MALWARE = "malware"
    LOGS = "logs"
    THREAT_INTELLIGENCE = "threat_intelligence"
    URL_ANALYSIS = "url_analysis"
    SENTIMENT = "sentiment"
    EMBEDDINGS = "embeddings"
    OCR = "ocr"
    VISION = "vision"
    LLM = "llm"
    RAG = "rag"


CATEGORY_META: Dict[ModelCategory, Dict[str, str]] = {
    ModelCategory.EMAIL_SECURITY: {"label": "Email Security", "icon": "Mail", "color": "hsl(217, 91%, 60%)"},
    ModelCategory.WEB_SECURITY: {"label": "Web Security", "icon": "Shield", "color": "hsl(142, 72%, 46%)"},
    ModelCategory.NETWORK_SECURITY: {"label": "Network Security", "icon": "Network", "color": "hsl(271, 91%, 65%)"},
    ModelCategory.MALWARE: {"label": "Malware", "icon": "Bug", "color": "hsl(0, 82%, 58%)"},
    ModelCategory.LOGS: {"label": "Log Analysis", "icon": "FileText", "color": "hsl(38, 92%, 55%)"},
    ModelCategory.THREAT_INTELLIGENCE: {"label": "Threat Intelligence", "icon": "Eye", "color": "hsl(188, 86%, 53%)"},
    ModelCategory.URL_ANALYSIS: {"label": "URL Analysis", "icon": "Link", "color": "hsl(291, 64%, 52%)"},
    ModelCategory.SENTIMENT: {"label": "Sentiment", "icon": "Smile", "color": "hsl(326, 82%, 60%)"},
    ModelCategory.EMBEDDINGS: {"label": "Embeddings", "icon": "Layers", "color": "hsl(180, 100%, 40%)"},
    ModelCategory.OCR: {"label": "OCR", "icon": "ScanText", "color": "hsl(15, 80%, 55%)"},
    ModelCategory.VISION: {"label": "Vision", "icon": "Camera", "color": "hsl(45, 93%, 55%)"},
    ModelCategory.LLM: {"label": "LLM", "icon": "Brain", "color": "hsl(280, 87%, 60%)"},
    ModelCategory.RAG: {"label": "RAG", "icon": "BookOpen", "color": "hsl(200, 70%, 50%)"},
}


@dataclass
class ModelMetadata:
    model_id: str
    name: str
    category: ModelCategory
    version: str
    framework: str
    hf_id: str
    local_path: str
    size: str
    param_count_b: float
    memory_mb: int
    gpu_required: bool
    description: str
    task: str
    icon: str = "Box"
    repo_available: bool = True
    sha256: str = ""
    homepage: str = ""


@dataclass
class ModelInfo:
    metadata: ModelMetadata
    status: ModelStatus = ModelStatus.UNLOADED
    loaded_at: Optional[datetime] = None
    load_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    gpu_usage_pct: Optional[float] = None
    cpu_usage_pct: Optional[float] = None
    avg_inference_ms: Optional[float] = None
    total_predictions: int = 0
    total_errors: int = 0
    last_used: Optional[datetime] = None
    download_progress: float = 0.0
    download_speed: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict:
        return {
            "model_id": self.metadata.model_id,
            "name": self.metadata.name,
            "category": self.metadata.category.value,
            "version": self.metadata.version,
            "framework": self.metadata.framework,
            "hf_id": self.metadata.hf_id,
            "local_path": self.metadata.local_path,
            "size": self.metadata.size,
            "param_count_b": self.metadata.param_count_b,
            "memory_mb": self.metadata.memory_mb,
            "gpu_required": self.metadata.gpu_required,
            "description": self.metadata.description,
            "task": self.metadata.task,
            "icon": self.metadata.icon,
            "repo_available": self.metadata.repo_available,
            "status": self.status.value,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "load_time_ms": self.load_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "gpu_usage_pct": self.gpu_usage_pct,
            "cpu_usage_pct": self.cpu_usage_pct,
            "avg_inference_ms": self.avg_inference_ms,
            "total_predictions": self.total_predictions,
            "total_errors": self.total_errors,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "download_progress": self.download_progress,
            "download_speed": self.download_speed,
            "error_message": self.error_message,
        }


class BaseAIModel(ABC):
    def __init__(self, metadata: ModelMetadata):
        self._metadata = metadata
        self._status = ModelStatus.UNLOADED
        self._loaded_at: Optional[datetime] = None
        self._load_time_ms: Optional[float] = None
        self._memory_usage_mb: Optional[float] = None
        self._gpu_usage_pct: Optional[float] = None
        self._cpu_usage_pct: Optional[float] = None
        self._avg_inference_ms: Optional[float] = None
        self._total_predictions: int = 0
        self._total_errors: int = 0
        self._last_used: Optional[datetime] = None
        self._model_instance: Any = None

    @property
    def model_id(self) -> str:
        return self._metadata.model_id

    @property
    def info(self) -> ModelInfo:
        return ModelInfo(
            metadata=self._metadata,
            status=self._status,
            loaded_at=self._loaded_at,
            load_time_ms=self._load_time_ms,
            memory_usage_mb=self._memory_usage_mb,
            gpu_usage_pct=self._gpu_usage_pct,
            cpu_usage_pct=self._cpu_usage_pct,
            avg_inference_ms=self._avg_inference_ms,
            total_predictions=self._total_predictions,
            total_errors=self._total_errors,
            last_used=self._last_used,
        )

    @abstractmethod
    async def load(self) -> bool:
        ...

    @abstractmethod
    async def unload(self) -> bool:
        ...

    @abstractmethod
    async def predict(self, input_data: Any) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        ...

    def metadata(self) -> ModelMetadata:
        return self._metadata

    def status(self) -> ModelStatus:
        return self._status

    def _track_inference(self, elapsed_ms: float, success: bool):
        self._total_predictions += 1
        if not success:
            self._total_errors += 1
        self._last_used = datetime.utcnow()
        if self._avg_inference_ms is None:
            self._avg_inference_ms = elapsed_ms
        else:
            self._avg_inference_ms = (self._avg_inference_ms * (self._total_predictions - 1) + elapsed_ms) / self._total_predictions
