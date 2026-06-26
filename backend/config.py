import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentConfig:
    enabled: bool = True
    timeout_s: int = 30
    max_retries: int = 2


@dataclass
class ModelRouterConfig:
    phishing_models: List[str] = field(default_factory=lambda: ["cysecbert", "secbert", "phishsense"])
    soc_models: List[str] = field(default_factory=lambda: ["securityllm", "security_rag"])
    threat_intel_models: List[str] = field(default_factory=lambda: ["rag", "threat_intel"])
    general_models: List[str] = field(default_factory=lambda: ["securityllm"])
    priority_order: Dict[str, int] = field(default_factory=lambda: {
        "cysecbert": 1, "secbert": 2, "phishsense": 3,
        "securityllm": 1, "security_rag": 2,
        "rag": 1, "threat_intel": 2
    })


@dataclass
class RAGConfig:
    vector_store_path: str = "backend/rag_agent/vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    rerank_top_k: int = 3
    cache_ttl_s: int = 3600
    sources: List[str] = field(default_factory=lambda: [
        "mitre_attck", "cve", "nist", "owasp", "sigma", "misp", "runbooks"
    ])


@dataclass
class GatewayConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    api_prefix: str = "/api/v1/security"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_per_min: int = 60


@dataclass
class MonitoringConfig:
    otlp_endpoint: str = "http://localhost:4317"
    service_name: str = "security-ai-orchestrator"
    enable_tracing: bool = True
    enable_metrics: bool = True
    metrics_port: int = 9090


@dataclass
class AppConfig:
    agents: AgentConfig = field(default_factory=AgentConfig)
    model_router: ModelRouterConfig = field(default_factory=ModelRouterConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    backend_url: str = field(default_factory=lambda: os.getenv("BACKEND_URL", "http://localhost:8000"))
    inference_server_url: str = field(default_factory=lambda: os.getenv("INFERENCE_URL", "http://localhost:8000"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_demo_mode: bool = field(default_factory=lambda: os.getenv("DEMO_MODE", "false").lower() == "true")


CONFIG = AppConfig()
