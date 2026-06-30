"use client";

import { useState, useRef, useCallback } from "react";
import { SentinelHeader } from "@/components/sentinel/SentinelHeader";
import {
  SentinelSidebar,
  type SentinelView,
} from "@/components/sentinel/SentinelSidebar";
import {
  OrchestratorControlPanel,
  type OrchestratorState,
} from "@/components/sentinel/OrchestratorControlPanel";
import { LiveAgentFeed } from "@/components/sentinel/LiveAgentFeed";
import {
  ConsensusEnginePanel,
  type Vote,
} from "@/components/sentinel/ConsensusEnginePanel";
import {
  EvidenceRagPanel,
  type Evidence,
} from "@/components/sentinel/EvidenceRagPanel";
import { DecisionJournal } from "@/components/sentinel/DecisionJournal";
import type { ConsoleMessage, MessageType } from "@/components/council/LiveMessageConsole";
import {
  Crosshair,
  Terminal,
  FlaskConical,
  LayoutGrid,
  Scale,
} from "lucide-react";

const now = () => new Date().toLocaleTimeString("en-GB");

// ─── Simulation scenario (fidèle au design Stitch) ───
type SimStep = {
  speaker: string;
  content: string;
  progress: number;
  after?: Partial<OrchestratorState>;
};

const SCENARIO: SimStep[] = [
  {
    speaker: "🧠 Master AI",
    content: "Email suspect détecté. Activation du conseil de sécurité.",
    progress: 12,
    after: { status: "ORCHESTRATING", classification: "Analysing..." },
  },
  {
    speaker: "🧠 Master AI",
    content: "Assigning task to Threat Intel: Correlate IOCs against recent APT29 campaigns.",
    progress: 28,
  },
  {
    speaker: "📧 Email Expert",
    content: "Suspicious urgency detected in payload headers. Analyzing DKIM/SPF anomalies.",
    progress: 42,
  },
  {
    speaker: "🛡 CySecBERT",
    content: "Phishing probability: 98%. Payload matches known credential harvester signature.",
    progress: 60,
    after: { classification: "Advanced Persistent Threat", confidence: 89 },
  },
  {
    speaker: "📡 Threat Intel",
    content: "Sender domain banque-secure.xyz registered 2 days ago. Reputation: MALICIOUS.",
    progress: 78,
  },
  {
    speaker: "🗺️ MITRE Expert",
    content: "Mapped to technique T1566 (Phishing) — Credential Harvesting sub-technique.",
    progress: 90,
  },
  {
    speaker: "🧠 Master AI",
    content: "Consensus reached: 92% stability. Verdict: BLOCK. Response plan generated.",
    progress: 100,
    after: { status: "ORCHESTRATING", progress: 100 },
  },
];

const INITIAL_VOTES: Vote[] = [
  { expert: "Threat Intel", verdict: "CONFIRM" },
  { expert: "SOC Analyst", verdict: "CONFIRM" },
  { expert: "MITRE Expert", verdict: "UNCERTAIN" },
  { expert: "Malware Expert", verdict: "CONFIRM" },
];

const RAG_SOURCES: Evidence[] = [
  {
    source: "MITRE ATT&CK",
    text: "Referenced technique T1566 (Phishing) based on payload delivery mechanism.",
    tone: "tertiary",
  },
  {
    source: "CVE DB",
    text: "Cross-referencing attachment hash with known CVE-2023-XXXX exploit patterns. Match probability: Low.",
    tone: "secondary",
  },
];

const IOC_EXTRACT: Evidence[] = [
  {
    source: "Domain",
    text: "banque-secure.xyz — registered 2024-06-25, reputation MALICIOUS",
    tone: "error",
  },
  {
    source: "URL",
    text: "http://banque-secure.xyz/login — credential harvester pattern",
    tone: "error",
  },
  {
    source: "Sender",
    text: "security@banque-secure.xyz — SPF: FAIL, DKIM: NONE",
    tone: "primary",
  },
];

const MITRE_MAP: Evidence[] = [
  {
    source: "T1566.002",
    text: "Spearphishing Link — initial access vector confirmed",
    tone: "tertiary",
  },
  {
    source: "T1189",
    text: "Drive-by Compromise — possible secondary stage",
    tone: "secondary",
  },
  {
    source: "T1110.004",
    text: "Credential Stuffing — harvest target on fake login",
    tone: "error",
  },
];

// ─── Bottom Nav mobile items ───
const MOBILE_NAV = [
  { icon: Terminal, active: true },
  { icon: FlaskConical, active: false },
  { icon: LayoutGrid, active: false },
  { icon: Scale, active: false },
];

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

export default function SentinelPage() {
  const [view, setView] = useState<SentinelView>("orchestrator");
  const [query, setQuery] = useState("URGENT: Votre compte a été suspendu. Vérifiez votre identité via ce lien: http://banque-secure.xyz/login sinon votre compte sera définitivement bloqué.");
  const [messages, setMessages] = useState<ConsoleMessage[]>([]);
  const [typing, setTyping] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [consensus, setConsensus] = useState(0);

  const [votes, setVotes] = useState<Vote[]>(INITIAL_VOTES);
  const [ragSources, setRagSources] = useState<Evidence[]>(RAG_SOURCES);
  const [iocExtracts, setIocExtracts] = useState<Evidence[]>(IOC_EXTRACT);
  const [mitreMap, setMitreMap] = useState<Evidence[]>(MITRE_MAP);
  const [decisionJournal, setDecisionJournal] = useState({
    title: "Awaiting Analysis",
    summary: "Threat analysis has not been initiated yet.",
    details: "Initiate threat analysis to populate the decision journal and extract threat markers.",
  });

  const [orch, setOrch] = useState<OrchestratorState>({
    status: "IDLE",
    classification: "Awaiting threat input",
    confidence: 0,
    progress: 0,
  });

  const timers = useRef<NodeJS.Timeout[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  const runScenario = useCallback(async () => {
    if (running || !query.trim()) return;
    clearTimers();
    setRunning(true);
    setMessages([]);
    setConsensus(0);
    setOrch({
      status: "ORCHESTRATING",
      classification: "Initializing...",
      confidence: 0,
      progress: 5,
    });

    // Ouvrir la connexion WebSocket pour les logs temps réel (port 8090)
    try {
      const wsHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const wsUrl = `ws://${wsHost}:8090/ws`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const entry = JSON.parse(event.data);
          const time = new Date(entry.timestamp || new Date()).toLocaleTimeString("en-GB");
          const speaker = entry.icon ? `${entry.icon} ${entry.source}` : entry.source;
          
          let type: MessageType = "evidence";
          if (entry.type === "error") type = "fallback";
          else if (entry.type === "contradiction") type = "warning";
          else if (entry.type === "consensus_final") type = "consensus";
          else if (entry.type === "master_activation") type = "mission";
          else if (entry.type === "discussion") type = "validation";
          else if (entry.type === "report") type = "validation";

          setTyping(entry.source.replace(/^[\p{Emoji}\s]+/u, "").trim());

          setMessages((prev) => {
            if (prev.length > 0 && prev[prev.length - 1].content === entry.message) {
              return prev;
            }
            return [
              ...prev,
              {
                time,
                speaker: anonymizeSpeaker(speaker),
                type,
                content: entry.message,
              }
            ];
          });

          // Mettre à jour la barre de progression
          if (entry.type === "coordinator") {
            setOrch((prev) => ({ ...prev, classification: "Analyzing Query...", progress: 15 }));
          } else if (entry.type === "master_activation") {
            setOrch((prev) => ({ ...prev, progress: 30 }));
          } else if (entry.type === "expert_query") {
            setOrch((prev) => ({ ...prev, progress: Math.min(prev.progress + 2, 70) }));
          } else if (entry.type === "expert_response") {
            setOrch((prev) => ({ ...prev, progress: Math.min(prev.progress + 2, 80) }));
          } else if (entry.type === "discussion") {
            setOrch((prev) => ({ ...prev, classification: "Deliberating...", progress: Math.min(prev.progress + 2, 90) }));
          } else if (entry.type === "consensus_final") {
            setOrch((prev) => ({ ...prev, classification: "Consensus Reached", progress: 95 }));
          } else if (entry.type === "report") {
            setOrch((prev) => ({ ...prev, progress: 100 }));
          }
        } catch (err) {
          console.error("WS parse error:", err);
        }
      };
      // Attendre que le WebSocket soit pleinement connecté avant de lancer la requête
      await new Promise<void>((resolve) => {
        if (ws.readyState === WebSocket.OPEN) {
          resolve();
        } else {
          ws.onopen = () => resolve();
          ws.onerror = () => resolve();
        }
      });
    } catch (err) {
      console.warn("WebSocket connection failed:", err);
    }

    try {
      const res = await fetch(`${getOrchestratorUrl()}/api/v1/security/council`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

      // Attendre la fin des logs
      await new Promise((resolve) => setTimeout(resolve, 800));
      setTyping(null);

      if (data.weighted_consensus) {
        const score = data.weighted_consensus.score;
        setConsensus(score);
        setOrch({
          status: "IDLE",
          classification: data.classification.replace(/_/g, " ").toUpperCase(),
          confidence: score,
          progress: 100,
        });

        // Formater les votes
        const mappedVotes = Object.values(data.master_verdicts).map((v: any) => ({
          expert: v.master_name,
          verdict: v.conclusion === "BLOCK" ? "CONFIRM" : v.conclusion === "ACCEPT" ? "CONFIRM" : "UNCERTAIN",
        })) as Vote[];
        setVotes(mappedVotes);

        // Formater les sources RAG
        const mappedRag = data.final_response?.references_rag 
          ? data.final_response.references_rag.map((ref: any) => ({
              source: ref.source,
              text: ref.text,
              tone: ref.score > 0.8 ? "tertiary" : "secondary"
            }))
          : RAG_SOURCES;
        setRagSources(mappedRag);

        // Formater les IOCs
        const mappedIocs: Evidence[] = [];
        if (data.master_verdicts) {
          Object.values(data.master_verdicts).forEach((v: any) => {
            if (v.iocs) {
              v.iocs.forEach((ioc: any) => {
                mappedIocs.push({
                  source: ioc.type.toUpperCase(),
                  text: `${ioc.value} (confiance: ${(ioc.confidence * 100).toFixed(0)}%)`,
                  tone: "error",
                });
              });
            }
          });
        }
        setIocExtracts(mappedIocs.length > 0 ? mappedIocs : IOC_EXTRACT);

        // Formater MITRE
        const mappedMitre: Evidence[] = [];
        if (data.master_verdicts) {
          Object.values(data.master_verdicts).forEach((v: any) => {
            if (v.mitre_techniques) {
              v.mitre_techniques.forEach((tech: string) => {
                mappedMitre.push({
                  source: tech.split(" - ")[0],
                  text: tech.split(" - ")[1] || tech,
                  tone: "secondary",
                });
              });
            }
          });
        }
        setMitreMap(mappedMitre.length > 0 ? mappedMitre : MITRE_MAP);

        // Journal de décision
        setDecisionJournal({
          title: data.classification.replace(/_/g, " ").toUpperCase(),
          summary: data.weighted_consensus.decision_justification,
          details: data.report || "Aucun détail supplémentaire.",
        });
      }
      
      setRunning(false);
      if (wsRef.current) wsRef.current.close();
    } catch (e) {
      setRunning(false);
      setTyping(null);
      setOrch((prev) => ({ ...prev, status: "IDLE", classification: "Error occurred" }));
      if (wsRef.current) wsRef.current.close();
      alert(`Erreur de connexion orchestrateur: ${(e as Error).message}`);
    }
  }, [running, query, clearTimers]);

  const handlePause = () => {
    clearTimers();
    setRunning(false);
    setTyping(null);
    setOrch((prev) => ({ ...prev, status: "PAUSED" }));
    if (wsRef.current) wsRef.current.close();
  };

  const handleRestart = () => {
    clearTimers();
    setMessages([]);
    setConsensus(0);
    setTyping(null);
    setRunning(false);
    setVotes(INITIAL_VOTES);
    setRagSources(RAG_SOURCES);
    setIocExtracts(IOC_EXTRACT);
    setMitreMap(MITRE_MAP);
    setDecisionJournal({
      title: "Awaiting Analysis",
      summary: "Threat analysis has not been initiated yet.",
      details: "Initiate threat analysis to populate the decision journal and extract threat markers.",
    });
    setOrch({
      status: "IDLE",
      classification: "Awaiting threat input",
      confidence: 0,
      progress: 0,
    });
    if (wsRef.current) wsRef.current.close();
  };

  const hasResult = messages.length > 0;

  return (
    <>
      <SentinelHeader
        session="SOC-2024-X9"
        risk={orch.confidence >= 80 ? "CRITICAL" : "MEDIUM"}
        consensus={consensus}
        agents={12}
      />
      <SentinelSidebar active={view} onSelect={setView} />

      {/* ─── Main Content Area (exact du design) ─── */}
      <main
        className="relative flex flex-1 flex-col gap-6 overflow-hidden p-6 md:flex-row md:ml-64 md:mt-16 md:h-[calc(100vh-4rem)]"
      >
        {/* Left Panel: Orchestrator Control */}
        <OrchestratorControlPanel
          state={orch}
          onPause={handlePause}
          onRestart={handleRestart}
          query={query}
          onQueryChange={setQuery}
        />

        {/* Center Panel: Live Agent Feed */}
        <LiveAgentFeed messages={messages} typing={typing} />

        {/* Right Panel: Consensus + Journal + Evidence */}
        <div className="flex min-h-0 flex-[1.5] flex-col gap-6">
          {/* Consensus Engine */}
          <ConsensusEnginePanel stability={consensus} votes={votes} />

          {/* Decision Journal — panneau du design Stitch */}
          <DecisionJournal
            title={decisionJournal.title}
            summary={decisionJournal.summary}
            details={decisionJournal.details}
          />

          {/* Evidence & RAG */}
          <EvidenceRagPanel
            rag={ragSources}
            ioc={iocExtracts}
            mitre={mitreMap}
          />
        </div>
      </main>

      {/* Bouton d'initialisation flottant quand idle */}
      {!hasResult && (
        <div className="stitch-fade-in fixed inset-0 z-30 flex items-center justify-center md:ml-64 md:mt-16">
          <button
            onClick={runScenario}
            className="stitch-glow-active flex items-center gap-3 rounded-lg border px-8 py-4 transition-all hover:brightness-125"
            style={{
              borderColor: "rgba(0, 209, 255, 0.4)",
              backgroundColor: "rgba(0, 209, 255, 0.08)",
              color: "var(--stitch-primary)",
            }}
          >
            <Crosshair size={20} />
            <span className="sentinel-caps" style={{ fontSize: "13px" }}>
              Initiate Threat Analysis
            </span>
          </button>
        </div>
      )}

      {/* ─── Bottom NavBar (Mobile only — exact du design) ─── */}
      <nav className="stitch-bottom-nav">
        {MOBILE_NAV.map(({ icon: Icon, active: isActive }, i) => (
          <div
            key={i}
            className="flex flex-col items-center gap-1 cursor-pointer transition-transform"
            style={{
              color: isActive ? "var(--stitch-tertiary)" : "var(--stitch-on-surface-variant)",
              transform: isActive ? "scale(0.98)" : "none",
            }}
          >
            <Icon size={20} />
          </div>
        ))}
      </nav>
    </>
  );
}
