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
import type { ConsoleMessage } from "@/components/council/LiveMessageConsole";
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

export default function SentinelPage() {
  const [view, setView] = useState<SentinelView>("orchestrator");
  const [messages, setMessages] = useState<ConsoleMessage[]>([]);
  const [typing, setTyping] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [consensus, setConsensus] = useState(0);

  const [orch, setOrch] = useState<OrchestratorState>({
    status: "IDLE",
    classification: "Awaiting threat input",
    confidence: 0,
    progress: 0,
  });

  const timers = useRef<NodeJS.Timeout[]>([]);

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  const runScenario = useCallback(() => {
    if (running) return;
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

    SCENARIO.forEach((step, idx) => {
      const typingTimer = setTimeout(() => {
        setTyping(
          step.speaker
            .replace(/^[\p{Emoji}\s]+/u, "")
            .trim()
        );
      }, idx * 2200);
      timers.current.push(typingTimer);

      const msgTimer = setTimeout(
        () => {
          setTyping(null);
          setMessages((prev) => [
            ...prev,
            {
              time: now(),
              speaker: step.speaker,
              type: "evidence",
              content: step.content,
            },
          ]);
          setOrch((prev) => ({
            ...prev,
            ...step.after,
            progress: step.progress,
          }));
          if (idx === SCENARIO.length - 1) {
            setConsensus(92);
            setRunning(false);
          }
        },
        idx * 2200 + 1400
      );
      timers.current.push(msgTimer);
    });
  }, [running, clearTimers]);

  const handlePause = () => {
    clearTimers();
    setRunning(false);
    setTyping(null);
    setOrch((prev) => ({ ...prev, status: "PAUSED" }));
  };

  const handleRestart = () => {
    clearTimers();
    setMessages([]);
    setConsensus(0);
    setTyping(null);
    setRunning(false);
    setOrch({
      status: "IDLE",
      classification: "Awaiting threat input",
      confidence: 0,
      progress: 0,
    });
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
        />

        {/* Center Panel: Live Agent Feed */}
        <LiveAgentFeed messages={messages} typing={typing} />

        {/* Right Panel: Consensus + Journal + Evidence */}
        <div className="flex min-h-0 flex-[1.5] flex-col gap-6">
          {/* Consensus Engine */}
          <ConsensusEnginePanel stability={consensus} votes={INITIAL_VOTES} />

          {/* Decision Journal — panneau du design Stitch */}
          <DecisionJournal
            title="Phishing Analysis"
            summary="High probability of a targeted credential harvesting attack."
            details="Payload exhibits sophisticated evasion techniques. Sender domains show recent fast-flux behavior. Recommend immediate quarantine of affected endpoints and reset of compromised credentials."
          />

          {/* Evidence & RAG */}
          <EvidenceRagPanel
            rag={RAG_SOURCES}
            ioc={IOC_EXTRACT}
            mitre={MITRE_MAP}
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
