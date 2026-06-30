"use client";

import React, { useState, useRef, useEffect } from "react";
import { getWsUrl, runCouncilAnalysis } from "@/lib/councilApi";
import { useCouncilWebSocket } from "@/hooks/useCouncilWebSocket";
import type { CouncilResultFull, RiskGauges } from "@/types/council";
import { SystemMonitorBar } from "./SystemMonitorBar";
import { CoordinatorPanel } from "./CoordinatorPanel";
import { MasterGrid } from "./MasterGrid";
import { DiscussionFeed } from "./DiscussionFeed";
import { ConsensusWheel } from "./ConsensusWheel";
import { RiskGaugesPanel } from "./RiskGaugesPanel";
import { EvidenceFusionPanel } from "./EvidenceFusionPanel";
import { ConflictResolutionPanel } from "./ConflictResolutionPanel";
import { ExpertDrilldown } from "./ExpertDrilldown";
import { TimelinePanel } from "./TimelinePanel";
import { AgentGraphPanel } from "./AgentGraphPanel";
import { LogConsole } from "./LogConsole";
import { FinalReportPanel } from "./FinalReportPanel";
import { ExplainabilityPanel } from "./ExplainabilityPanel";
import { Terminal, Shield, Play, LoaderCircle, AlertTriangle } from "lucide-react";

const SUGGESTIONS = [
  "Payload suspect avec appel système inhabituel sur serveur sensible.",
  "Email avec lien suspect vers banque-secure.xyz et signature DKIM manquante.",
  "Script Powershell obfusqué exécuté dans le dossier AppData/Local.",
];

export default function CouncilDashboard() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<CouncilResultFull | null>(null);
  const [activeTab, setActiveTab] = useState<"briefing" | "graph" | "timeline" | "explain" | "drilldown" | "logs">("briefing");

  // Telemetry time counter during run
  const [elapsedTimeMs, setElapsedTimeMs] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection hooks
  const wsUrl = getWsUrl();
  const {
    isConnected,
    coordinatorPhase,
    masterStates,
    discussions,
    evidences,
    conflicts,
    timeline,
    eventCount,
    events,
    reset,
    waitForOpen,
  } = useCouncilWebSocket(wsUrl, loading);

  // Map risk metrics from final REST results
  const riskGauges: RiskGauges | null = result?.risk_assessment
    ? {
        risk_score: result.risk_assessment.risk_score,
        impact: result.risk_assessment.impact_score * 10,
        likelihood: result.risk_assessment.probability * 100,
        priority: result.risk_assessment.severity === "CRITICAL" ? 95 : result.risk_assessment.severity === "HIGH" ? 75 : 50,
        business_impact: result.risk_assessment.risk_score * 0.9,
        cvss: result.risk_assessment.severity_score,
        severity: result.risk_assessment.severity,
      }
    : null;

  // Active models & experts count
  const activeModelsCount = result?.selected_models?.length ?? 0;
  const activeExpertsCount = result?.experts?.length ?? timeline.filter(t => t.eventType === "expert_query").length;

  const handleStartAnalysis = async (searchQuery: string) => {
    const q = searchQuery.trim();
    if (!q) return;

    reset();
    setResult(null);
    setLoading(true);
    setError("");
    setElapsedTimeMs(0);

    // Latency counter
    if (timerRef.current) clearInterval(timerRef.current);
    const start = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedTimeMs(Date.now() - start);
    }, 50);

    try {
      // Establish WS channel before posting the query to avoid missing initial logs
      await waitForOpen();

      const data = await runCouncilAnalysis(q);
      setResult(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  // Clean timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return (
    <div className="space-y-4 max-w-[1600px] mx-auto p-4 min-h-screen">
      {/* Top telemetry monitoring bar */}
      <SystemMonitorBar
        elapsedTimeMs={elapsedTimeMs}
        modelsCount={activeModelsCount}
        expertsCount={activeExpertsCount}
      />

      {/* Main Grid: Control panel + suggestions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Incident submission input */}
        <div className="lg:col-span-2 glass rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Terminal size={16} className="text-primary animate-pulse" />
              <h3 className="text-xs font-bold text-white/50 uppercase tracking-widest">
                SOC Incident Submission Console
              </h3>
            </div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Saisissez un événement de sécurité ou un incident RAG suspect pour analyse multi-master..."
              className="w-full h-24 bg-[#050810]/60 border border-white/[0.08] rounded-lg p-3 text-xs text-white placeholder-white/30 focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 mt-3">
            {/* Status indicator */}
            <div className="flex items-center gap-2 text-xs">
              <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-ping" : "bg-white/20"}`} />
              <span className="text-white/40">WebSocket:</span>
              <span className={isConnected ? "text-green-400 font-semibold" : "text-white/30"}>
                {isConnected ? "CONNECTED" : "OFFLINE"}
              </span>
            </div>

            <button
              onClick={() => handleStartAnalysis(query)}
              disabled={loading || !query.trim()}
              className="px-5 py-2 rounded-lg bg-primary hover:bg-primary-dim text-white text-xs font-bold flex items-center gap-2 transition-all shadow-glow disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <LoaderCircle className="animate-spin" size={14} /> Deliberating...
                </>
              ) : (
                <>
                  <Play size={12} fill="currentColor" /> Initiate Threat Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Suggestions / Prompt recipes */}
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield size={15} className="text-primary" />
            <h3 className="text-xs font-bold text-white/50 uppercase tracking-widest">
              Incident Scenarios
            </h3>
          </div>
          <div className="space-y-2">
            {SUGGESTIONS.map((s, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(s);
                  handleStartAnalysis(s);
                }}
                className="w-full text-left p-2 rounded bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.05] transition-colors text-[11px] text-white/60 hover:text-white leading-relaxed truncate block"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Deliberations grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left column: Coordinator + Masters cards (lg:col-span-4) */}
        <div className="lg:col-span-4 space-y-4">
          <CoordinatorPanel
            phase={coordinatorPhase}
            eventCount={eventCount}
            latestMessage={discussions[discussions.length - 1]?.content}
          />
          <MasterGrid masterStates={masterStates} />
          <ConsensusWheel consensus={result?.weighted_consensus ?? null} />
        </div>

        {/* Center column: Live agent discussions feed (lg:col-span-5) */}
        <div className="lg:col-span-5 h-[620px] lg:h-auto flex flex-col">
          <DiscussionFeed messages={discussions} isStreaming={loading} />
        </div>

        {/* Right column: Conflict resolution + Evidence fusion (lg:col-span-3) */}
        <div className="lg:col-span-3 space-y-4">
          <ConflictResolutionPanel conflicts={conflicts} />
          <EvidenceFusionPanel evidences={evidences} />
        </div>
      </div>

      {/* Threat Metrics & Gauges */}
      <RiskGaugesPanel riskData={riskGauges} />

      {/* Tabbed view selection */}
      <div className="border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex gap-2">
          {(["briefing", "graph", "timeline", "explain", "drilldown", "logs"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-wider transition-all border-b-2 ${
                activeTab === tab
                  ? "border-primary text-white"
                  : "border-transparent text-white/40 hover:text-white/60"
              }`}
            >
              {tab === "briefing" && "📋 Playbook Briefing"}
              {tab === "graph" && "🕸️ Live Agent Graph"}
              {tab === "timeline" && "🕒 Analysis Timeline"}
              {tab === "explain" && "🧐 Explainability tags"}
              {tab === "drilldown" && "🔬 Expert drilldown"}
              {tab === "logs" && "⌨️ Raw Logs console"}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="animate-fade-up">
        {activeTab === "briefing" && <FinalReportPanel result={result} />}
        {activeTab === "graph" && <AgentGraphPanel masterStates={masterStates} coordinatorPhase={coordinatorPhase} />}
        {activeTab === "timeline" && <TimelinePanel timeline={timeline} />}
        {activeTab === "explain" && <ExplainabilityPanel result={result} />}
        {activeTab === "drilldown" && <ExpertDrilldown result={result} />}
        {activeTab === "logs" && <LogConsole events={events} />}
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-xs flex items-center gap-2 animate-pulse">
          <AlertTriangle size={14} />
          <span>Error during Analysis Engine execution: {error}</span>
        </div>
      )}
    </div>
  );
}
