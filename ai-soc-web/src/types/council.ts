/**
 * types/council.ts — Shared types for the AI Security Council V2 dashboard.
 *
 * Mirrors the backend DiscussionJournal events (WebSocket) and
 * MultiMasterResult (REST) data contracts.
 */

/* ─── WebSocket Event (matches DiscussionJournal._log()) ─── */

export type CouncilEventType =
  | "coordinator"
  | "master_activation"
  | "master_planning"
  | "master_completed"
  | "expert_query"
  | "expert_response"
  | "discussion"
  | "contradiction"
  | "contradiction_resolved"
  | "consensus"
  | "consensus_final"
  | "report"
  | "error";

export interface CouncilEvent {
  type: CouncilEventType;
  source: string;
  target: string | null;
  message: string;
  icon: string;
  elapsed_ms: number;
  timestamp: string;
}

/* ─── Coordinator ─── */

export type CoordinatorPhase =
  | "idle"
  | "planning"
  | "dispatching"
  | "waiting"
  | "consensus"
  | "final_decision";

/* ─── Master State ─── */

export type MasterPhase =
  | "idle"
  | "activated"
  | "querying_experts"
  | "analyzing"
  | "debating"
  | "completed";

export interface MasterState {
  id: string;
  name: string;
  emoji: string;
  color: string;
  phase: MasterPhase;
  confidence: number;
  score: number;
  verdict: string;
  elapsed_ms: number;
  experts_active: number;
  experts_total: number;
  models_used: string[];
  evidence_count: number;
  progress: number;
}

/* ─── Discussion Message ─── */

export type DiscussionRole = "coordinator" | "master" | "expert" | "model" | "engine";

export interface DiscussionMessage {
  id: string;
  speaker: string;
  speakerEmoji: string;
  role: DiscussionRole;
  target?: string;
  content: string;
  timestamp: string;
  eventType: CouncilEventType;
  elapsed_ms: number;
}

/* ─── Evidence ─── */

export interface EvidenceItem {
  id: string;
  source: string;
  type: "model" | "expert" | "rag" | "cti" | "sigma" | "mitre" | "ioc";
  content: string;
  confidence: number;
  timestamp: string;
}

/* ─── Conflict ─── */

export interface ConflictItem {
  id: string;
  left: string;
  right: string;
  leftScore: number;
  rightScore: number;
  detail: string;
  status: "detected" | "discussing" | "resolved";
  resolution?: string;
  timestamp: string;
}

/* ─── Timeline ─── */

export interface TimelineEntry {
  id: string;
  timestamp: string;
  agent: string;
  agentEmoji: string;
  action: string;
  duration_ms: number;
  phase: string;
  eventType: CouncilEventType;
}

/* ─── Risk Gauges ─── */

export interface RiskGauges {
  risk_score: number;
  impact: number;
  likelihood: number;
  priority: number;
  business_impact: number;
  cvss: number;
  severity: string;
}

/* ─── Full REST Result ─── */

export interface MasterVerdictData {
  master_id: string;
  master_name: string;
  conclusion: string;
  confidence: number;
  score: number;
  evidence: string[];
  iocs: Array<{ type: string; value: string; confidence: number }>;
  mitre_techniques: string[];
  recommendations: string[];
  severity: string;
  reasoning_summary: string;
}

export interface WeightedConsensusData {
  score: number;
  confidence_level: string;
  verdict_final: string;
  weights_used: Record<string, number>;
  master_verdicts: Record<string, MasterVerdictData>;
  contradictions: Array<Record<string, unknown>>;
  contradictions_resolved: boolean;
  decision_justification: string;
}

export interface DiscussionLogEntry {
  round: number;
  speaker_id: string;
  speaker_name: string;
  target_id: string | null;
  target_name: string | null;
  message: string;
  evidence_cited: string[];
  timestamp: string;
}

export interface CouncilResultFull {
  query: string;
  classification: string;
  coordinator_id: string;
  activated_masters: string[];
  master_verdicts: Record<string, MasterVerdictData>;
  discussion_log: DiscussionLogEntry[];
  discussion_rounds: number;
  weighted_consensus: WeightedConsensusData | null;
  report: string;
  session_id: string;

  // v1 legacy fields (from CouncilResult merge)
  selected_models?: string[];
  experts?: Array<{
    expert_id: string;
    expert_name: string;
    category: string;
    status: string;
    conclusion: string;
    confidence: number;
    evidence: string[];
    limitations: string[];
    inference_ms: number;
    severity?: string;
  }>;
  conversation?: Array<{
    speaker: string;
    target?: string;
    phase: string;
    content: string;
    timestamp: string;
  }>;
  consensus?: {
    global_score: number;
    confidence_level: string;
    total_retained: number;
    total_models_executed: number;
  };
  final_response?: {
    conclusion: string;
    answer: string;
    global_confidence: number;
    confidence_level: string;
    participants: string[];
    primary_model?: string;
    main_evidence: string[];
    references_rag: Array<{ source: string; text: string; score: number }>;
    decision_reasons: string[];
    divergences: Array<Record<string, unknown>>;
  };
  timeline?: Array<{
    name: string;
    status: string;
    elapsed_ms: number;
    data: Record<string, unknown>;
  }>;
  metrics?: {
    total_execution_ms: number;
    experts_completed: number;
    experts_failed: number;
  };

  // v2 enriched fields
  reasoning_trace?: {
    incident_type: string;
    classification_confidence: number;
    experts_consulted: string[];
    steps: Array<{
      step: number;
      name: string;
      description: string;
      findings: string[];
      elapsed_ms: number;
      status: string;
    }>;
    key_observations: string[];
    hypothesis: string;
    hypothesis_validated: boolean;
    information_gaps: string[];
  };
  attack_timeline?: {
    attack_vector: string;
    entry_point: string;
    phases: Array<{
      phase_id: string;
      phase_name: string;
      techniques: string[];
      evidence: string[];
      confidence: number;
    }>;
    iocs_extracted: Array<{ type: string; value: string; confidence: number }>;
    estimated_impact: string;
  };
  risk_assessment?: {
    severity: string;
    severity_score: number;
    probability: number;
    impact: string;
    impact_score: number;
    criticality: string;
    risk_score: number;
    cvss_vector?: string;
  };
  response_plan?: {
    incident_type: string;
    containment: Array<{
      phase: string;
      priority: number;
      action: string;
      description: string;
      responsible: string;
      estimated_time: string;
      automated: boolean;
    }>;
    eradication: Array<{
      phase: string;
      priority: number;
      action: string;
      description: string;
      responsible: string;
      estimated_time: string;
      automated: boolean;
    }>;
    recovery: Array<{
      phase: string;
      priority: number;
      action: string;
      description: string;
      responsible: string;
      estimated_time: string;
      automated: boolean;
    }>;
    prevention: Array<{
      phase: string;
      priority: number;
      action: string;
      description: string;
      responsible: string;
      estimated_time: string;
      automated: boolean;
    }>;
    monitoring: string[];
    escalation_required: boolean;
    estimated_resolution_time: string;
  };
  decision_journal?: {
    session_id: string;
    timestamp: string;
    query_summary: string;
    incident_type: string;
    experts_solicited: string[];
    models_executed: string[];
    sources_consulted: string[];
    evidence_summary: string[];
    consensus_score: number;
    confidence_level: string;
    final_decision: string;
    decision_justification: string;
    contradictions_found: number;
    false_positive_risk: string;
    recommended_next_steps: string[];
  };
}

/* ─── Dashboard overall state ─── */

export type DashboardPhase =
  | "idle"
  | "planning"
  | "analyzing"
  | "debating"
  | "consensus"
  | "complete";
