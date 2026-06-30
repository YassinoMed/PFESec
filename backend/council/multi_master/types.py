"""Multi-Master types — Structures de données pour l'architecture hiérarchique."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.council.types import CouncilResult, ExpertAnalysis


@dataclass
class MasterPlan:
    """Plan d'analyse construit par un Master AI."""
    master_id: str
    master_name: str
    query: str
    classification: str
    selected_experts: List[str] = field(default_factory=list)
    models_to_query: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "master_id": self.master_id,
            "master_name": self.master_name,
            "query": self.query[:100],
            "classification": self.classification,
            "selected_experts": self.selected_experts,
            "models_to_query": self.models_to_query,
            "reasoning_steps": self.reasoning_steps,
        }


@dataclass
class MasterVerdict:
    """Verdict produit par un Master AI après analyse."""
    master_id: str
    master_name: str
    conclusion: str
    confidence: float
    score: float
    evidence: List[str] = field(default_factory=list)
    iocs: List[Dict] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    severity: str = "UNKNOWN"
    expert_analyses: List[ExpertAnalysis] = field(default_factory=list)
    plan: Optional[MasterPlan] = None
    reasoning_summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "master_id": self.master_id,
            "master_name": self.master_name,
            "conclusion": self.conclusion,
            "confidence": round(self.confidence, 2),
            "score": round(self.score, 2),
            "evidence": self.evidence[:8],
            "iocs": self.iocs[:10],
            "mitre_techniques": self.mitre_techniques[:10],
            "recommendations": self.recommendations[:5],
            "severity": self.severity,
            "reasoning_summary": self.reasoning_summary[:200],
        }


@dataclass
class MasterDiscussion:
    """Un échange entre deux Masters AI."""
    round: int
    speaker_id: str
    speaker_name: str
    target_id: Optional[str]
    target_name: Optional[str]
    message: str
    evidence_cited: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "round": self.round,
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "message": self.message,
            "evidence_cited": self.evidence_cited[:5],
            "timestamp": self.timestamp,
        }


@dataclass
class WeightedConsensus:
    """Résultat du consensus pondéré entre Masters."""
    score: float
    confidence_level: str
    verdict_final: str
    weights_used: Dict[str, float]
    master_verdicts: Dict[str, MasterVerdict]
    contradictions: List[Dict] = field(default_factory=list)
    contradictions_resolved: bool = False
    decision_justification: str = ""

    def to_dict(self) -> Dict:
        return {
            "score": round(self.score, 2),
            "confidence_level": self.confidence_level,
            "verdict_final": self.verdict_final,
            "weights_used": self.weights_used,
            "master_verdicts": {k: v.to_dict() for k, v in self.master_verdicts.items()},
            "contradictions": self.contradictions,
            "contradictions_resolved": self.contradictions_resolved,
            "decision_justification": self.decision_justification[:300],
        }


@dataclass
class MultiMasterResult:
    """Résultat complet de l'architecture Multi-Master."""
    query: str
    classification: str
    coordinator_id: str = "global_coordinator"
    activated_masters: List[str] = field(default_factory=list)
    master_verdicts: Dict[str, MasterVerdict] = field(default_factory=dict)
    discussion_log: List[MasterDiscussion] = field(default_factory=list)
    discussion_rounds: int = 0
    weighted_consensus: Optional[WeightedConsensus] = None
    council_result: Optional[CouncilResult] = None
    report: str = ""
    session_id: str = ""

    def to_dict(self) -> Dict:
        d = {}
        if self.council_result:
            if hasattr(self.council_result, "to_dict"):
                d = self.council_result.to_dict()
            else:
                d = dict(self.council_result.__dict__)
        
        d.update({
            "query": self.query,
            "classification": self.classification,
            "coordinator_id": self.coordinator_id,
            "activated_masters": self.activated_masters,
            "master_verdicts": {k: v.to_dict() for k, v in self.master_verdicts.items()},
            "discussion_log": [d.to_dict() for d in self.discussion_log],
            "discussion_rounds": self.discussion_rounds,
            "weighted_consensus": self.weighted_consensus.to_dict() if self.weighted_consensus else None,
            "report": self.report,
            "session_id": self.session_id,
        })
        return d
