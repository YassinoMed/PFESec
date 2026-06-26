from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ExpertAnalysis:
    expert_id: str
    expert_name: str
    category: str
    status: str
    response: Any = None
    conclusion: str = "UNKNOWN"
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    inference_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "category": self.category,
            "status": self.status,
            "response": self.response,
            "conclusion": self.conclusion,
            "confidence": round(self.confidence, 2),
            "evidence": self.evidence,
            "limitations": self.limitations,
            "inference_ms": round(self.inference_ms, 2),
            "error": self.error,
        }


@dataclass
class CouncilMessage:
    speaker: str
    target: Optional[str]
    phase: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return self.__dict__.copy()


@dataclass
class CrossValidation:
    reviewer: str
    reviewed: str
    status: str
    notes: str

    def to_dict(self) -> Dict:
        return self.__dict__.copy()


@dataclass
class FactCheckResult:
    verified_facts: List[Dict] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    unconfirmed: List[str] = field(default_factory=list)
    references: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "verified_facts": self.verified_facts,
            "hypotheses": self.hypotheses,
            "unconfirmed": self.unconfirmed,
            "references": self.references,
        }


@dataclass
class CouncilResult:
    query: str
    classification: str
    selected_models: List[str]
    experts: List[ExpertAnalysis]
    conversation: List[CouncilMessage]
    contradictions: List[Dict]
    cross_validations: List[CrossValidation]
    fact_check: FactCheckResult
    consensus: Dict
    reflection: Dict
    final_response: Dict
    timeline: List[Dict]
    metrics: Dict
    config: Dict

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "classification": self.classification,
            "selected_models": self.selected_models,
            "experts": [e.to_dict() for e in self.experts],
            "conversation": [m.to_dict() for m in self.conversation],
            "contradictions": self.contradictions,
            "cross_validations": [v.to_dict() for v in self.cross_validations],
            "fact_check": self.fact_check.to_dict(),
            "consensus": self.consensus,
            "reflection": self.reflection,
            "final_response": self.final_response,
            "timeline": self.timeline,
            "metrics": self.metrics,
            "config": self.config,
        }
