/**
 * lib/councilApi.ts — API client and shared constants for the Council V2 dashboard.
 */

import type { CouncilResultFull } from "@/types/council";

/* ─── Orchestrator URL ─── */

export function getOrchestratorUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
  if (envUrl) return envUrl.trim();
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }
  return "http://localhost:8080";
}

export function getWsUrl(): string {
  if (typeof window !== "undefined") {
    return `ws://${window.location.hostname}:8090/ws`;
  }
  return "ws://localhost:8090/ws";
}

/* ─── REST API ─── */

export async function runCouncilAnalysis(query: string): Promise<CouncilResultFull> {
  const res = await fetch(`${getOrchestratorUrl()}/api/v1/security/council`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data as CouncilResultFull;
}

/* ─── Expert/Agent name mapping ─── */

export interface AgentInfo {
  name: string;
  emoji: string;
  role: "coordinator" | "master" | "expert" | "model" | "engine";
  color: string;
}

export const AGENT_MAP: Record<string, AgentInfo> = {
  // Coordinator
  global_coordinator:     { name: "Global Coordinator",       emoji: "🧠", role: "coordinator", color: "#a78bfa" },
  // Masters
  threat_master:          { name: "Threat Master",            emoji: "🛡️", role: "master", color: "#f87171" },
  soc_master:             { name: "SOC Master",               emoji: "⚙️",  role: "master", color: "#60a5fa" },
  rag_master:             { name: "Knowledge Master",         emoji: "📚", role: "master", color: "#fbbf24" },
  governance_master:      { name: "Governance Master",        emoji: "🏛️", role: "master", color: "#c084fc" },
  // Experts
  threat_intel_expert:    { name: "Threat Intel Expert",      emoji: "📡", role: "expert", color: "#fb923c" },
  phishing_expert:        { name: "Phishing Expert",          emoji: "🎣", role: "expert", color: "#f87171" },
  email_header_expert:    { name: "Email Security Expert",    emoji: "📧", role: "expert", color: "#38bdf8" },
  url_expert:             { name: "URL Reputation Expert",    emoji: "🌐", role: "expert", color: "#34d399" },
  ioc_expert:             { name: "IOC Expert",               emoji: "🔍", role: "expert", color: "#fb923c" },
  mitre_expert:           { name: "MITRE Expert",             emoji: "🗺️", role: "expert", color: "#a78bfa" },
  sigma_expert:           { name: "Sigma Expert",             emoji: "📝", role: "expert", color: "#fbbf24" },
  incident_response_expert: { name: "Incident Response",     emoji: "🚑", role: "expert", color: "#f87171" },
  soc_analyst_expert:     { name: "SOC Analyst Expert",       emoji: "💻", role: "expert", color: "#60a5fa" },
  rag_knowledge_expert:   { name: "RAG Knowledge Expert",     emoji: "📚", role: "expert", color: "#fbbf24" },
  vulnerability_expert:   { name: "Vulnerability Expert",     emoji: "🎯", role: "expert", color: "#fb923c" },
  governance_expert:      { name: "Governance Expert",        emoji: "⚖️", role: "expert", color: "#c084fc" },
  cloud_security_expert:  { name: "Cloud Security Expert",    emoji: "☁️", role: "expert", color: "#38bdf8" },
  kubernetes_security_expert: { name: "K8s Security Expert",  emoji: "☸️", role: "expert", color: "#60a5fa" },
  devsecops_expert:       { name: "DevSecOps Expert",         emoji: "🏗️", role: "expert", color: "#34d399" },
  risk_assessment_virtual_expert: { name: "Risk Assessment",  emoji: "⚖️", role: "expert", color: "#fbbf24" },
  knowledge_base_analyst: { name: "Knowledge Analyst",        emoji: "📚", role: "expert", color: "#fbbf24" },
  ai_governance_compliance_expert: { name: "AI Compliance",   emoji: "⚖️", role: "expert", color: "#c084fc" },
  // Models
  cysecbert:              { name: "CySecBERT",                emoji: "🛡️", role: "model", color: "#f472b6" },
  phishsense:             { name: "PhishSense",               emoji: "🦙", role: "model", color: "#f472b6" },
  codebert:               { name: "CodeBERT",                 emoji: "💻", role: "model", color: "#f472b6" },
  graphcodebert:          { name: "GraphCodeBERT",            emoji: "🔗", role: "model", color: "#f472b6" },
  netbert:                { name: "NetBERT",                  emoji: "📡", role: "model", color: "#f472b6" },
  flowtransformer:        { name: "FlowTransformer",          emoji: "🌊", role: "model", color: "#f472b6" },
  malbert:                { name: "MalBERT",                  emoji: "🦠", role: "model", color: "#f472b6" },
  malconv:                { name: "MalConv",                  emoji: "⚙️", role: "model", color: "#f472b6" },
  attackbert:             { name: "AttackBERT",               emoji: "🎯", role: "model", color: "#f472b6" },
  iocbert:                { name: "IOCBERT",                  emoji: "🔍", role: "model", color: "#f472b6" },
  urlbert:                { name: "URLBERT",                  emoji: "🔗", role: "model", color: "#f472b6" },
  urlnet:                 { name: "URLNet",                   emoji: "🌐", role: "model", color: "#f472b6" },
  logbert:                { name: "LogBERT",                  emoji: "📝", role: "model", color: "#f472b6" },
  deeplog:                { name: "DeepLog",                  emoji: "📊", role: "model", color: "#f472b6" },
  paddleocr:              { name: "PaddleOCR",                emoji: "📄", role: "model", color: "#f472b6" },
  trocr_small:            { name: "TrOCR",                    emoji: "📖", role: "model", color: "#f472b6" },
  qwen2_5_1_5b:           { name: "Qwen2.5-1.5B",            emoji: "🧠", role: "model", color: "#f472b6" },
  smollm2_1_7b:           { name: "SmolLM2-1.7B",            emoji: "⚡", role: "model", color: "#f472b6" },
  // Engines
  weighted_consensus_engine: { name: "Consensus Engine",      emoji: "⚖️", role: "engine", color: "#fbbf24" },
  securityllm_report_engine: { name: "Report Engine",         emoji: "📊", role: "engine", color: "#34d399" },
};

export function resolveAgent(rawId: string): AgentInfo {
  if (!rawId) return { name: "Unknown", emoji: "❓", role: "engine", color: "#64748b" };
  const clean = rawId.replace(/^[\p{Emoji}\s]+/u, "").trim().toLowerCase();
  if (clean in AGENT_MAP) return AGENT_MAP[clean];
  // Try matching by display name
  for (const info of Object.values(AGENT_MAP)) {
    if (info.name.toLowerCase() === clean || clean.replace(/_/g, " ") === info.name.toLowerCase()) {
      return info;
    }
  }
  return { name: rawId, emoji: "🔹", role: "engine", color: "#64748b" };
}

/* ─── Master definitions ─── */

export const MASTERS = [
  { id: "threat_master", name: "Threat Master", emoji: "🛡️", color: "#f87171", bgClass: "from-red-500/20 to-red-900/10" },
  { id: "soc_master",    name: "SOC Master",    emoji: "⚙️",  color: "#60a5fa", bgClass: "from-blue-500/20 to-blue-900/10" },
  { id: "rag_master",    name: "Knowledge Master", emoji: "📚", color: "#fbbf24", bgClass: "from-amber-500/20 to-amber-900/10" },
  { id: "governance_master", name: "Governance Master", emoji: "🏛️", color: "#c084fc", bgClass: "from-purple-500/20 to-purple-900/10" },
] as const;
