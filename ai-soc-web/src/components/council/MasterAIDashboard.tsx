"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  Brain,
  ShieldCheck,
  AlertTriangle,
  Clock,
  GitCompareArrows,
  CheckCircle2,
  Cpu,
  Layers,
  Sparkles,
  Play,
  LoaderCircle,
  XCircle,
  Terminal,
  Activity,
} from "lucide-react";
import LiveAgentGraph, { ExpertState } from "./LiveAgentGraph";
import LiveMessageConsole, { ConsoleMessage, MessageType } from "./LiveMessageConsole";
import AttackTimeline from "./AttackTimeline";
import RiskMatrix from "./RiskMatrix";
import ResponsePlanCards from "./ResponsePlanCards";
import DecisionJournal from "./DecisionJournal";
import { Card, CardHeader } from "@/components/ui/Card";

interface ExpertAnalysis {
  expert_id: string;
  expert_name: string;
  category: string;
  status: string;
  response: unknown;
  conclusion: string;
  confidence: number;
  evidence: string[];
  limitations: string[];
  inference_ms: number;
  error?: string;
  severity?: string;
}

interface CouncilMessage {
  speaker: string;
  target?: string;
  phase: string;
  content: string;
  timestamp: string;
}

interface CouncilResult {
  classification: string;
  selected_models: string[];
  experts: ExpertAnalysis[];
  conversation: CouncilMessage[];
  contradictions: Array<Record<string, unknown>>;
  cross_validations: Array<{ reviewer: string; reviewed: string; status: string; notes: string }>;
  fact_check: { references: Array<{ source: string; text: string; score: number }>; hypotheses: string[]; unconfirmed: string[] };
  consensus: { global_score: number; confidence_level: string; total_retained: number; total_models_executed: number };
  reflection: { passed: boolean; issues: string[]; action: string };
  final_response: {
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
  timeline: Array<{ name: string; status: string; elapsed_ms: number; data: Record<string, unknown> }>;
  metrics: { total_execution_ms: number; experts_completed: number; experts_failed: number };
  
  // v2 fields
  reasoning_trace?: {
    incident_type: string;
    classification_confidence: number;
    experts_consulted: string[];
    steps: Array<{ step: number; name: string; description: string; findings: string[]; elapsed_ms: number; status: string }>;
    key_observations: string[];
    hypothesis: string;
    hypothesis_validated: boolean;
    information_gaps: string[];
  };
  attack_timeline?: {
    attack_vector: string;
    entry_point: string;
    phases: Array<{ phase_id: string; phase_name: string; techniques: string[]; evidence: string[]; confidence: number }>;
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
    containment: Array<{ phase: string; priority: number; action: string; description: string; responsible: string; estimated_time: string; automated: boolean }>;
    eradication: Array<{ phase: string; priority: number; action: string; description: string; responsible: string; estimated_time: string; automated: boolean }>;
    recovery: Array<{ phase: string; priority: number; action: string; description: string; responsible: string; estimated_time: string; automated: boolean }>;
    prevention: Array<{ phase: string; priority: number; action: string; description: string; responsible: string; estimated_time: string; automated: boolean }>;
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

function getOrchestratorUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
  if (envUrl) return envUrl.trim();
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }
  return "http://localhost:8080";
}

const EXPERT_INFO: Record<string, { name: string; emoji: string }> = {
  threat_master: { name: "Threat Master", emoji: "🛡️" },
  soc_master: { name: "SOC Master", emoji: "💻" },
  rag_master: { name: "RAG Master", emoji: "📚" },
  governance_master: { name: "Governance Master", emoji: "⚖️" },
  global_coordinator: { name: "Global Coordinator", emoji: "🧠" },
  governance_expert: { name: "Governance Expert", emoji: "⚖️" },
  cysecbert: { name: "CySecBERT", emoji: "🛡️" },
  phishsense: { name: "PhishSense", emoji: "🦙" },
  codebert: { name: "CodeBERT", emoji: "💻" },
  graphcodebert: { name: "GraphCodeBERT", emoji: "🔗" },
  netbert: { name: "NetBERT", emoji: "📡" },
  flowtransformer: { name: "FlowTransformer", emoji: "🌊" },
  malbert: { name: "MalBERT", emoji: "🦠" },
  malconv: { name: "MalConv", emoji: "⚙️" },
  attackbert: { name: "AttackBERT", emoji: "🎯" },
  iocbert: { name: "IOCBERT", emoji: "🔍" },
  urlbert: { name: "URLBERT", emoji: "🔗" },
  urlnet: { name: "URLNet", emoji: "🌐" },
  logbert: { name: "LogBERT", emoji: "📝" },
  deeplog: { name: "DeepLog", emoji: "📊" },
  paddleocr: { name: "PaddleOCR", emoji: "📄" },
  trocr_small: { name: "TrOCR", emoji: "📖" },
  qwen2_5_1_5b: { name: "Qwen2.5-1.5B", emoji: "🧠" },
  smollm2_1_7b: { name: "SmolLM2-1.7B", emoji: "⚡" },
  phishing_expert: { name: "Phishing Expert", emoji: "🎣" },
  email_header_expert: { name: "Email Security Expert", emoji: "📧" },
  url_expert: { name: "URL Reputation Expert", emoji: "🌐" },
  threat_intel_expert: { name: "Threat Intelligence Expert", emoji: "📡" },
  ioc_expert: { name: "IOC Expert", emoji: "🔍" },
  mitre_expert: { name: "MITRE Expert", emoji: "🗺️" },
  sigma_expert: { name: "Sigma Expert", emoji: "📝" },
  incident_response_expert: { name: "Incident Response Expert", emoji: "🚑" },
  soc_analyst_expert: { name: "SOC Analyst Expert", emoji: "💻" },
  rag_knowledge_expert: { name: "RAG Knowledge Expert", emoji: "📚" },
  vulnerability_expert: { name: "Vulnerability Expert", emoji: "🎯" },
  cloud_security_expert: { name: "Cloud Security Expert", emoji: "☁️" },
  kubernetes_security_expert: { name: "Kubernetes Security Expert", emoji: "☸️" },
  devsecops_expert: { name: "DevSecOps Expert", emoji: "🏗️" },
  risk_assessment_virtual_expert: { name: "Risk Assessment Expert", emoji: "⚖️" },
};

const anonymizeSpeaker = (text: string): string => {
  if (!text) return text;
  const clean = text.replace(/^[\p{Emoji}\s]+/u, "").trim().toLowerCase();
  
  for (const [key, info] of Object.entries(EXPERT_INFO)) {
    if (clean === key || clean === info.name.toLowerCase() || clean.replace(/_/g, " ") === key.replace(/_/g, " ")) {
      return `${info.emoji} ${info.name}`;
    }
  }
  return text;
};

const anonymizeExpert = (id: string): string => {
  const normId = id.toLowerCase().trim();
  if (normId in EXPERT_INFO) {
    const info = EXPERT_INFO[normId];
    return `${info.emoji} ${info.name}`;
  }
  return id
    .replace(/_expert/g, "")
    .replace(/_virtual/g, "")
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
};

const anonymize = (text: string): string => {
  if (!text) return text;
  let result = text;
  Object.entries(EXPERT_INFO).forEach(([key, info]) => {
    const regex = new RegExp(key, "gi");
    result = result.replace(regex, `${info.emoji} ${info.name}`);
  });
  return result;
};

export default function MasterAIDashboard() {
  const [query, setQuery] = useState("URGENT: Votre compte a été suspendu. Vérifiez votre identité via ce lien: http://banque-secure.xyz/login sinon votre compte sera définitivement bloqué.");
  const [result, setResult] = useState<CouncilResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Live simulation states
  const [isSimulating, setIsSimulating] = useState(false);
  const [simMessages, setSimMessages] = useState<ConsoleMessage[]>([]);
  const [simPhase, setSimPhase] = useState<string>("idle");
  const [activeExpertId, setActiveExpertId] = useState<string | null>(null);
  const [expertNodes, setExpertNodes] = useState<Array<{ id: string; name: string; state: ExpertState; colorClass: string }>>([]);
  const [simProgress, setSimProgress] = useState(0);
  const [simTimeMs, setSimTimeMs] = useState(0);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const simTimeIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Stop simulation on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (simTimeIntervalRef.current) clearInterval(simTimeIntervalRef.current);
    };
  }, []);

  const runCouncil = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setIsSimulating(true);
    setSimMessages([]);
    setSimPhase("comprehension");
    setSimProgress(5);
    setSimTimeMs(0);
    setActiveExpertId(null);
    setExpertNodes([]);

    // Start incrementing timer simulating executing latency
    if (simTimeIntervalRef.current) clearInterval(simTimeIntervalRef.current);
    simTimeIntervalRef.current = setInterval(() => {
      setSimTimeMs((prev) => prev + 64);
    }, 64);

    // Open WebSocket for live deliberation updates
    let ws: WebSocket | null = null;
    try {
      const wsUrl = getOrchestratorUrl().replace(/^http/, "ws") + "/ws";
      const newWs = new WebSocket(wsUrl);
      ws = newWs;
      newWs.onmessage = (event) => {
        try {
          const entry = JSON.parse(event.data);
          const time = new Date(entry.timestamp || new Date()).toLocaleTimeString();
          const speaker = entry.icon ? `${entry.icon} ${entry.source}` : entry.source;
          let type: MessageType = "evidence";
          if (entry.type === "error") type = "fallback";
          else if (entry.type === "contradiction") type = "warning";
          else if (entry.type === "consensus_final") type = "consensus";
          else if (entry.type === "master_activation") type = "mission";
          else if (entry.type === "discussion") type = "validation";
          else if (entry.type === "report") type = "validation";

          setSimMessages((prev) => {
            // Éviter les doublons exacts dans l'affichage
            if (prev.length > 0 && prev[prev.length - 1].content === anonymize(entry.message)) {
              return prev;
            }
            return [
              ...prev,
              {
                time,
                speaker: anonymizeSpeaker(speaker),
                type,
                content: anonymize(entry.message),
              }
            ];
          });

          // Mettre à jour la phase et la progression
          if (entry.type === "coordinator") {
            setSimPhase("comprehension");
            setSimProgress(15);
          } else if (entry.type === "master_activation") {
            setSimPhase("planning");
            setSimProgress(30);
            setExpertNodes((prev) => {
              if (prev.some(n => n.id === entry.source)) return prev;
              return [...prev, {
                id: entry.source,
                name: anonymizeExpert(entry.source),
                state: "finished" as ExpertState,
                colorClass: "bg-neutral-600",
              }];
            });
          } else if (entry.type === "expert_query") {
            setSimPhase("analysis");
            setSimProgress((p) => Math.min(p + 3, 70));
            setActiveExpertId(entry.target);
            setExpertNodes((prev) => {
              if (!prev.some(n => n.id === entry.target)) {
                return [...prev, {
                  id: entry.target,
                  name: anonymizeExpert(entry.target),
                  state: "analysing" as ExpertState,
                  colorClass: "bg-neutral-600",
                }];
              }
              return prev.map(n => n.id === entry.target ? { ...n, state: "analysing" as ExpertState } : n);
            });
          } else if (entry.type === "expert_response") {
            setSimProgress((p) => Math.min(p + 3, 80));
            setActiveExpertId(null);
            setExpertNodes((prev) =>
              prev.map(n => n.id === entry.source ? { ...n, state: "finished" as ExpertState } : n)
            );
          } else if (entry.type === "discussion") {
            setSimPhase("debate");
            setSimProgress((p) => Math.min(p + 2, 90));
            setExpertNodes((prev) =>
              prev.map(n => n.state === "finished" ? { ...n, state: "cross_validation" as ExpertState } : n)
            );
          } else if (entry.type === "consensus_final") {
            setSimPhase("consensus");
            setSimProgress(95);
          } else if (entry.type === "report") {
            setSimPhase("consensus");
            setSimProgress(100);
          }
        } catch (err) {
          console.error("Error parsing WS message:", err);
        }
      };
      // Attendre que le WebSocket soit pleinement connecté avant de lancer la requête
      await new Promise<void>((resolve) => {
        if (newWs.readyState === WebSocket.OPEN) {
          resolve();
        } else {
          newWs.onopen = () => resolve();
          newWs.onerror = () => resolve();
        }
      });
    } catch (err) {
      console.warn("Failed to open WebSocket, logs will fallback to post-fetch:", err);
    }

    try {
      const res = await fetch(`${getOrchestratorUrl()}/api/v1/security/council`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = (await res.json()) as CouncilResult;
      if (!res.ok) throw new Error((data as any).error || `HTTP ${res.status}`);

      // Attendre un tout petit peu pour que les messages WS finissent de s'afficher
      await new Promise((resolve) => setTimeout(resolve, 800));

      setResult(data);
      setIsSimulating(false);
      setLoading(false);
      if (simTimeIntervalRef.current) clearInterval(simTimeIntervalRef.current);
      if (ws) ws.close();
    } catch (e) {
      setError((e as Error).message);
      setIsSimulating(false);
      setLoading(false);
      if (simTimeIntervalRef.current) clearInterval(simTimeIntervalRef.current);
      if (ws) ws.close();
    }
  };

  const playSimulation = (data: CouncilResult, initialNodes: typeof expertNodes) => {
    const timeStr = () => new Date().toLocaleTimeString();
    const isEmail = data.classification.includes("email") || data.classification.includes("phishing");
    const categoryConf = data.reasoning_trace?.classification_confidence ?? 0.95;

    // Setup sequence of simulation steps
    const steps = [
      // Step 1: Comprehension
      {
        delay: 600,
        action: () => {
          setSimPhase("comprehension");
          setSimProgress(15);
          setSimMessages([
            {
              time: timeStr(),
              speaker: "🧠 Master AI",
              type: "mission" as MessageType,
              content: isEmail ? "Email détecté. Classification en cours..." : "Requête de sécurité détectée. Classification en cours...",
            },
          ]);
        },
      },
      // Step 2: Classification
      {
        delay: 1300,
        action: () => {
          setSimPhase("planning");
          setSimProgress(25);
          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "🧠 Master AI",
              type: "mission" as MessageType,
              content: `Catégorie : ${data.classification}, Confiance : ${(categoryConf * (categoryConf <= 1 ? 100 : 1)).toFixed(0)} %`,
            },
          ]);
        },
      },
      // Step 2.5: Activation des experts
      {
        delay: 2000,
        action: () => {
          setSimProgress(30);
          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "🧠 Master AI",
              type: "mission" as MessageType,
              content: `Activation des experts : ${data.selected_models.map(m => "✓ " + anonymizeExpert(m)).join(", ")}`,
            },
          ]);
        },
      },
      // Step 3-7: Distribute to experts one-by-one and print logs
      ...data.experts.map((exp, idx) => ({
        delay: 2800 + idx * 1000,
        action: () => {
          setSimPhase("analysis");
          setSimProgress(35 + Math.round((idx / data.experts.length) * 40));
          setActiveExpertId(exp.expert_id);

          // Update expert node state to analysing
          setExpertNodes((prev) =>
            prev.map((n) => (n.id === exp.expert_id ? { ...n, state: "analysing" as ExpertState } : n))
          );

          // Node completed shortly after
          setTimeout(() => {
            setExpertNodes((prev) =>
              prev.map((n) =>
                n.id === exp.expert_id
                  ? { ...n, state: (exp.status === "completed" ? "finished" : "error") as ExpertState }
                  : n
              )
            );
          }, 600);

          const isBlock = exp.conclusion === "BLOCK";
          const messageContent = exp.evidence && exp.evidence.length > 0
            ? exp.evidence.join(". ")
            : (typeof exp.response === "string" ? exp.response : `Analyse terminée avec verdict ${exp.conclusion}`);

          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: anonymizeExpert(exp.expert_id),
              type: (isBlock ? "warning" : "evidence") as MessageType,
              content: messageContent,
            },
          ]);
        },
      })),
      // Step 9: Cross validation
      {
        delay: 3200 + data.experts.length * 1000,
        action: () => {
          setSimPhase("debate");
          setSimProgress(80);
          setActiveExpertId(null);

          // Set all finished experts to cross validation
          setExpertNodes((prev) =>
            prev.map((n) => (n.state === "finished" ? { ...n, state: "cross_validation" as ExpertState } : n))
          );

          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "🧠 Master AI",
              type: "validation" as MessageType,
              content: `Lancement de la validation croisée entre experts... ${
                data.contradictions.length > 0
                  ? `⚠️ ${data.contradictions.length} divergence(s) détectée(s) : activation du protocole de débat.`
                  : "Accord mutuel sans divergence détectée."
              }`,
            },
          ]);
        },
      },
      // Step 10: RAG validation / local references
      {
        delay: 4200 + data.experts.length * 1000,
        action: () => {
          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "📂 RAG Agent",
              type: "evidence" as MessageType,
              content: `Fact-checking local terminé. ${
                data.fact_check.references.length > 0
                  ? `${data.fact_check.references.length} référence(s) locale(s) confirmée(s) (MISP/MITRE/CVE).`
                  : "Aucune référence locale directe correspondante."
              }`,
            },
          ]);
        },
      },
      // Step 11: Consensus calculation
      {
        delay: 5200 + data.experts.length * 1000,
        action: () => {
          setSimPhase("consensus");
          setSimProgress(90);

          setExpertNodes((prev) =>
            prev.map((n) =>
              n.state === "cross_validation" ? { ...n, state: "consensus" as ExpertState } : n
            )
          );

          const consensusVal = data.decision_journal?.consensus_score ?? data.consensus.global_score;
          const consensusContent = data.contradictions.length > 0
            ? `Les preuves divergent. ${data.contradictions.length} contradiction(s) détectée(s). Consensus : ${consensusVal.toFixed(0)} %`
            : `Les preuves convergent. Aucune contradiction. Consensus : ${consensusVal.toFixed(0)} %`;

          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "🧠 Master AI",
              type: "consensus" as MessageType,
              content: consensusContent,
            },
          ]);
        },
      },
      // Step 12: Final Decision Verdict
      {
        delay: 6200 + data.experts.length * 1000,
        action: () => {
          setSimPhase("done");
          setSimProgress(100);
          if (simTimeIntervalRef.current) clearInterval(simTimeIntervalRef.current);

          const decisionStr = data.decision_journal?.final_decision ?? data.final_response.conclusion;

          setSimMessages((prev) => [
            ...prev,
            {
              time: timeStr(),
              speaker: "📄 Décision finale",
              type: "completed" as MessageType,
              content: decisionStr.toUpperCase(),
            },
          ]);

          // Transition simulation completion
          setTimeout(() => {
            setResult(data);
            setIsSimulating(false);
            setLoading(false);
          }, 600);
        },
      },
    ];

    // Play each step sequentially
    // Clear any previous timeouts
    if (timerRef.current) clearTimeout(timerRef.current);

    steps.forEach((step) => {
      timerRef.current = setTimeout(() => {
        step.action();
      }, step.delay);
    });
  };

  return (
    <div className="space-y-6">
      {/* Search Input panel */}
      <Card>
        <CardHeader
          title="Session AI Security Council v2"
          subtitle="Master AI Reasoning Engine orchestrant 15 experts spécialisés en parallèle"
          icon={<Brain size={18} />}
          action={
            <button
              onClick={runCouncil}
              disabled={loading || !query.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-glow transition hover:bg-primary/90 disabled:opacity-40"
            >
              {loading ? (
                <LoaderCircle size={14} className="animate-spin" />
              ) : (
                <Play size={14} />
              )}
              Lancer l'Analyse
            </button>
          }
        />
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          className="w-full resize-none rounded-lg border border-white/10 bg-black/30 px-3 py-3 font-mono text-xs leading-5 text-[#f0f4ff] placeholder:text-tertiary focus:border-primary/50 focus:outline-none"
          placeholder="Entrez un événement de sécurité, un email ou un log suspect..."
        />
      </Card>

      {error && (
        <Card className="border-block/30 animate-fade-in">
          <p className="flex items-center gap-2 text-sm text-block">
            <XCircle size={16} /> {error}
          </p>
        </Card>
      )}

      {/* Live AI Council Simulator Panel */}
      {isSimulating && (
        <div className="space-y-6 animate-fade-in">
          {/* Progress Header */}
          <Card>
            <div className="flex flex-col gap-3 p-4">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-primary font-semibold">
                  <Activity size={14} className="animate-pulse" />
                  ANALYSING THREAT EVENT LIVE...
                </span>
                <span className="font-mono text-tertiary">
                  Temps écoulé: {simTimeMs} ms · Progression: {simProgress}%
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-primary shadow-glow transition-all duration-300"
                  style={{ width: `${simProgress}%` }}
                />
              </div>
            </div>
          </Card>

          {/* Interactive Flow Visualisation & Log Console */}
          <div className="grid gap-6 lg:grid-cols-2">
            <LiveAgentGraph
              experts={expertNodes}
              activeExpertId={activeExpertId}
              phase={simPhase}
            />

            <LiveMessageConsole messages={simMessages} />
          </div>
        </div>
      )}

      {/* Complete Dashboard Results Display */}
      {result && !isSimulating && (
        <div className="space-y-6 animate-fade-in">
          {/* Row 1: KPI metrics summary */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-white/5 bg-black/30 p-4 space-y-2">
              <span className="text-[10px] text-secondary uppercase tracking-widest block">
                Consensus Global
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-[#f0f4ff]">
                  {(result.decision_journal?.consensus_score ?? result.consensus.global_score).toFixed(0)}%
                </span>
                <span className="text-xs text-secondary font-medium uppercase">
                  {result.decision_journal?.confidence_level ?? result.consensus.confidence_level}
                </span>
              </div>
            </div>

            <div className="rounded-lg border border-white/5 bg-black/30 p-4 space-y-2">
              <span className="text-[10px] text-secondary uppercase tracking-widest block">
                Experts Activés
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-[#f0f4ff]">
                  {result.metrics.experts_completed}
                </span>
                <span className="text-xs text-secondary">/ {result.experts.length} complétés</span>
              </div>
            </div>

            <div className="rounded-lg border border-white/5 bg-black/30 p-4 space-y-2">
              <span className="text-[10px] text-secondary uppercase tracking-widest block">
                Contradictions
              </span>
              <div className="flex items-baseline gap-2">
                <span
                  className={cn(
                    "text-2xl font-bold font-mono",
                    result.contradictions.length > 0 ? "text-block" : "text-accept"
                  )}
                >
                  {result.contradictions.length}
                </span>
                <span className="text-xs text-secondary">identifiées</span>
              </div>
            </div>

            <div className="rounded-lg border border-white/5 bg-black/30 p-4 space-y-2">
              <span className="text-[10px] text-secondary uppercase tracking-widest block">
                Latence Totale
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-[#f0f4ff]">
                  {result.metrics.total_execution_ms.toFixed(0)}
                </span>
                <span className="text-xs text-secondary">ms</span>
              </div>
            </div>
          </div>

          {/* Row 2: Live Agent Graph & Log Console (Retained after compilation) */}
          <div className="grid gap-6 lg:grid-cols-2">
            <LiveAgentGraph
              experts={result.selected_models.map((mid) => ({
                id: mid,
                name: anonymizeExpert(mid),
                state: "finished" as ExpertState,
                colorClass: "bg-accept",
              }))}
              activeExpertId={null}
              phase="done"
            />

            <LiveMessageConsole
              messages={[
                {
                  time: "10:42:11",
                  speaker: "🧠 Master AI",
                  type: "mission",
                  content: `Analyse complétée pour classification ${result.classification}.`,
                },
                ...result.experts.map((exp) => ({
                  time: "10:42:12",
                  speaker: anonymizeExpert(exp.expert_id),
                  type: (exp.conclusion === "BLOCK" ? "warning" : "evidence") as MessageType,
                  content: `Preuves: ${exp.evidence.join(", ") || "Aucune preuve."}`,
                })),
                {
                  time: "10:42:14",
                  speaker: "🧠 Master AI",
                  type: "completed",
                  content: `Décision finalisée : ${
                    result.decision_journal?.final_decision ?? result.final_response.conclusion
                  }.`,
                },
              ]}
            />
          </div>

          {/* Row 3: Decision Journal Card */}
          {result.decision_journal && <DecisionJournal journal={result.decision_journal} />}

          {/* Row 4: Attack timeline + Risk Matrix */}
          <div className="grid gap-6 lg:grid-cols-2">
            {result.attack_timeline && <AttackTimeline timeline={result.attack_timeline} />}

            {result.risk_assessment && <RiskMatrix assessment={result.risk_assessment} />}
          </div>

          {/* Row 5: Actionable IR playbook */}
          {result.response_plan && <ResponsePlanCards plan={result.response_plan} />}

          {/* Row 6: RAG References + Cross Validations */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader
                title="Validations Croisées"
                subtitle="Défis et accords identifiés entre experts durant l'analyse"
                icon={<GitCompareArrows size={18} />}
              />
              <div className="max-h-64 space-y-2 overflow-y-auto pr-1 p-4">
                {result.cross_validations.map((v, i) => (
                  <div
                    key={`${v.reviewer}-${v.reviewed}-${i}`}
                    className="rounded bg-white/[0.02] border border-white/5 px-3 py-2.5 text-xs"
                  >
                    <div className="flex justify-between items-center gap-3">
                      <span className="font-semibold text-[#f0f4ff]">
                        {anonymize(v.reviewer)} → {anonymize(v.reviewed)}
                      </span>
                      <span
                        className={cn(
                          "rounded px-1.5 py-0.2 font-mono text-[9px] uppercase",
                          v.status === "confirmed"
                            ? "bg-accept/10 text-accept"
                            : v.status === "challenged"
                            ? "bg-block/10 text-block"
                            : "bg-white/10 text-secondary"
                        )}
                      >
                        {v.status}
                      </span>
                    </div>
                    <p className="mt-1.5 text-secondary leading-relaxed">{anonymize(v.notes)}</p>
                  </div>
                ))}
                {result.cross_validations.length === 0 && (
                  <p className="text-xs text-secondary text-center py-6">
                    Aucune validation croisée disponible.
                  </p>
                )}
              </div>
            </Card>

            <Card>
              <CardHeader
                title="Preuves RAG Locales"
                subtitle="Citations de documents officiels indexés dans la base locale"
                icon={<CheckCircle2 size={18} />}
              />
              <div className="max-h-64 space-y-2 overflow-y-auto pr-1 p-4">
                {result.fact_check.references.map((ref, idx) => (
                  <div
                    key={`${ref.source}-${idx}`}
                    className="rounded bg-white/[0.02] border border-white/5 px-3 py-2.5 text-xs space-y-1"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-primary font-bold">{ref.source}</span>
                      <span className="text-[10px] text-tertiary">
                        Pertinence: {(ref.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-secondary leading-relaxed">{ref.text}</p>
                  </div>
                ))}
                {result.fact_check.references.length === 0 && (
                  <p className="text-xs text-secondary text-center py-6">
                    Aucune preuve locale confirmée dans la base RAG.
                  </p>
                )}
              </div>
            </Card>
          </div>

          {/* Row 7: Detailed Experts Table */}
          <Card>
            <CardHeader
              title="Journal des Experts"
              subtitle="Performance, conclusions et indicateurs individuels"
              icon={<Cpu size={18} />}
            />
            <div className="overflow-x-auto p-4">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-tertiary">
                    <th className="pb-2 font-medium">Expert</th>
                    <th className="pb-2 font-medium">Catégorie</th>
                    <th className="pb-2 font-medium">État</th>
                    <th className="pb-2 font-medium">Verdict</th>
                    <th className="pb-2 font-medium text-right">Confiance</th>
                    <th className="pb-2 font-medium text-right">Temps</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.02]">
                  {result.experts.map((exp, idx) => (
                    <tr key={`${exp.expert_id}-${idx}`} className="hover:bg-white/[0.01] transition-colors">
                      <td className="py-2.5 font-semibold text-[#f0f4ff]">{anonymize(exp.expert_name)}</td>
                      <td className="py-2.5 text-secondary capitalize">{exp.category.replace(/_/g, " ")}</td>
                      <td className="py-2.5">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                            exp.status === "completed"
                              ? "bg-accept/15 text-accept"
                              : "bg-block/15 text-block"
                          )}
                        >
                          {exp.status}
                        </span>
                      </td>
                      <td
                        className={cn(
                          "py-2.5 font-mono font-bold",
                          exp.conclusion === "BLOCK"
                            ? "text-block"
                            : exp.conclusion === "ACCEPT"
                            ? "text-accept"
                            : "text-warn"
                        )}
                      >
                        {exp.conclusion}
                      </td>
                      <td className="py-2.5 text-right font-mono">{exp.confidence.toFixed(0)}%</td>
                      <td className="py-2.5 text-right font-mono text-tertiary">
                        {exp.inference_ms.toFixed(0)} ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
