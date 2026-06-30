from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
#  Core Expert Analysis
# ──────────────────────────────────────────────

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
    recommendations: List[str] = field(default_factory=list)
    iocs: List[Dict] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    severity: str = "UNKNOWN"

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
            "recommendations": self.recommendations,
            "iocs": self.iocs,
            "mitre_techniques": self.mitre_techniques,
            "severity": self.severity,
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


# ──────────────────────────────────────────────
#  NEW v2 — Reasoning Trace
# ──────────────────────────────────────────────

@dataclass
class ReasoningStep:
    """One step in the structured reasoning chain (never exposes model internals)."""
    step: int
    name: str
    description: str
    findings: List[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    status: str = "completed"

    def to_dict(self) -> Dict:
        return {
            "step": self.step,
            "name": self.name,
            "description": self.description,
            "findings": self.findings,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "status": self.status,
        }


@dataclass
class ReasoningTrace:
    """Structured reasoning trace — Decision Journal without raw chain-of-thought."""
    incident_type: str = "unknown"
    classification_confidence: float = 0.0
    experts_consulted: List[str] = field(default_factory=list)
    models_executed: List[str] = field(default_factory=list)
    rag_sources_queried: List[str] = field(default_factory=list)
    steps: List[ReasoningStep] = field(default_factory=list)
    key_observations: List[str] = field(default_factory=list)
    hypothesis: str = ""
    hypothesis_validated: bool = False
    information_gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "incident_type": self.incident_type,
            "classification_confidence": round(self.classification_confidence, 2),
            "experts_consulted": self.experts_consulted,
            "models_executed": self.models_executed,
            "rag_sources_queried": self.rag_sources_queried,
            "steps": [s.to_dict() for s in self.steps],
            "key_observations": self.key_observations,
            "hypothesis": self.hypothesis,
            "hypothesis_validated": self.hypothesis_validated,
            "information_gaps": self.information_gaps,
        }


# ──────────────────────────────────────────────
#  NEW v2 — Attack Timeline
# ──────────────────────────────────────────────

@dataclass
class AttackPhase:
    phase_id: str          # e.g. "TA0001"
    phase_name: str        # e.g. "Initial Access"
    techniques: List[str]  # e.g. ["T1566.001 - Spearphishing Attachment"]
    evidence: List[str]
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "techniques": self.techniques,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class AttackTimeline:
    attack_vector: str = "unknown"
    entry_point: str = "unknown"
    phases: List[AttackPhase] = field(default_factory=list)
    iocs_extracted: List[Dict] = field(default_factory=list)
    lateral_movement: bool = False
    persistence_mechanism: Optional[str] = None
    exfiltration_detected: bool = False
    estimated_impact: str = "unknown"
    mitre_tactics: List[str] = field(default_factory=list)
    sigma_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "attack_vector": self.attack_vector,
            "entry_point": self.entry_point,
            "phases": [p.to_dict() for p in self.phases],
            "iocs_extracted": self.iocs_extracted,
            "lateral_movement": self.lateral_movement,
            "persistence_mechanism": self.persistence_mechanism,
            "exfiltration_detected": self.exfiltration_detected,
            "estimated_impact": self.estimated_impact,
            "mitre_tactics": self.mitre_tactics,
            "sigma_rules": self.sigma_rules,
        }


# ──────────────────────────────────────────────
#  NEW v2 — Risk Assessment
# ──────────────────────────────────────────────

@dataclass
class RiskAssessment:
    severity: str = "UNKNOWN"
    severity_score: float = 0.0
    probability: float = 0.0
    impact: str = "UNKNOWN"
    impact_score: float = 0.0
    criticality: str = "UNKNOWN"
    priority: int = 5
    risk_score: float = 0.0
    affected_assets: List[str] = field(default_factory=list)
    business_impact: str = ""
    technical_impact: str = ""
    cvss_vector: str = ""
    exploitability: str = "UNKNOWN"

    def to_dict(self) -> Dict:
        return {
            "severity": self.severity,
            "severity_score": round(self.severity_score, 2),
            "probability": round(self.probability, 2),
            "impact": self.impact,
            "impact_score": round(self.impact_score, 2),
            "criticality": self.criticality,
            "priority": self.priority,
            "risk_score": round(self.risk_score, 2),
            "affected_assets": self.affected_assets,
            "business_impact": self.business_impact,
            "technical_impact": self.technical_impact,
            "cvss_vector": self.cvss_vector,
            "exploitability": self.exploitability,
        }


# ──────────────────────────────────────────────
#  NEW v2 — Response Plan
# ──────────────────────────────────────────────

@dataclass
class ResponseAction:
    phase: str
    priority: int
    action: str
    description: str
    responsible: str = "SOC"
    estimated_time: str = "immediate"
    automated: bool = False

    def to_dict(self) -> Dict:
        return {
            "phase": self.phase,
            "priority": self.priority,
            "action": self.action,
            "description": self.description,
            "responsible": self.responsible,
            "estimated_time": self.estimated_time,
            "automated": self.automated,
        }


@dataclass
class ResponsePlan:
    incident_type: str = "unknown"
    containment: List[ResponseAction] = field(default_factory=list)
    eradication: List[ResponseAction] = field(default_factory=list)
    recovery: List[ResponseAction] = field(default_factory=list)
    prevention: List[ResponseAction] = field(default_factory=list)
    monitoring: List[str] = field(default_factory=list)
    escalation_required: bool = False
    estimated_resolution_time: str = "unknown"

    def to_dict(self) -> Dict:
        return {
            "incident_type": self.incident_type,
            "containment": [a.to_dict() for a in self.containment],
            "eradication": [a.to_dict() for a in self.eradication],
            "recovery": [a.to_dict() for a in self.recovery],
            "prevention": [a.to_dict() for a in self.prevention],
            "monitoring": self.monitoring,
            "escalation_required": self.escalation_required,
            "estimated_resolution_time": self.estimated_resolution_time,
        }


# ──────────────────────────────────────────────
#  NEW v2 — Decision Journal
# ──────────────────────────────────────────────

@dataclass
class DecisionJournal:
    """Explicable audit trail — never exposes raw model chain-of-thought."""
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    query_summary: str = ""
    incident_type: str = "unknown"
    experts_solicited: List[str] = field(default_factory=list)
    models_executed: List[str] = field(default_factory=list)
    sources_consulted: List[str] = field(default_factory=list)
    evidence_summary: List[str] = field(default_factory=list)
    consensus_score: float = 0.0
    confidence_level: str = "Low"
    final_decision: str = "UNKNOWN"
    decision_justification: str = ""
    contradictions_found: int = 0
    contradictions_resolved: List[Dict] = field(default_factory=list)
    false_positive_risk: str = "unknown"
    recommended_next_steps: List[str] = field(default_factory=list)

    def validate_before_emission(self) -> None:
        if self.contradictions_found > 0 and not self.contradictions_resolved:
            raise ValueError(
                f"BLOCAGE: {self.contradictions_found} contradiction(s) détectée(s) "
                "mais aucune n'est enregistrée dans contradictions_resolved. "
                "Le DecisionJournal ne peut pas être émis sans traçabilité complète."
            )

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "query_summary": self.query_summary,
            "incident_type": self.incident_type,
            "experts_solicited": self.experts_solicited,
            "models_executed": self.models_executed,
            "sources_consulted": self.sources_consulted,
            "evidence_summary": self.evidence_summary,
            "consensus_score": round(self.consensus_score, 2),
            "confidence_level": self.confidence_level,
            "final_decision": self.final_decision,
            "decision_justification": self.decision_justification,
            "contradictions_found": self.contradictions_found,
            "contradictions_resolved": self.contradictions_resolved,
            "false_positive_risk": self.false_positive_risk,
            "recommended_next_steps": self.recommended_next_steps,
        }


# ──────────────────────────────────────────────
#  Extended CouncilResult (backward-compatible)
# ──────────────────────────────────────────────

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
    # v2 extensions
    reasoning_trace: Optional[ReasoningTrace] = None
    attack_timeline: Optional[AttackTimeline] = None
    risk_assessment: Optional[RiskAssessment] = None
    response_plan: Optional[ResponsePlan] = None
    decision_journal: Optional[DecisionJournal] = None
    evidence_fusion: Optional[Dict] = None

    def to_dict(self) -> Dict:
        base = {
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
        if self.reasoning_trace:
            base["reasoning_trace"] = self.reasoning_trace.to_dict()
        if self.attack_timeline:
            base["attack_timeline"] = self.attack_timeline.to_dict()
        if self.risk_assessment:
            base["risk_assessment"] = self.risk_assessment.to_dict()
        if self.response_plan:
            base["response_plan"] = self.response_plan.to_dict()
        if self.decision_journal:
            base["decision_journal"] = self.decision_journal.to_dict()
        if self.evidence_fusion:
            base["evidence_fusion"] = self.evidence_fusion
        return base
