"use client";

import React from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { BookOpen, AlertTriangle, ShieldCheck } from "lucide-react";

interface DecisionJournalProps {
  journal: {
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

const EXPERT_INFO: Record<string, { name: string; emoji: string }> = {
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

export default function DecisionJournal({ journal }: DecisionJournalProps) {
  const {
    session_id,
    timestamp,
    query_summary,
    incident_type,
    experts_solicited,
    models_executed,
    sources_consulted,
    evidence_summary,
    consensus_score,
    confidence_level,
    final_decision,
    decision_justification,
    contradictions_found,
    false_positive_risk,
    recommended_next_steps,
  } = journal;

  return (
    <Card className="flex flex-col h-full">
      <CardHeader
        title="Journal de Décision (Audit Trail)"
        subtitle={`Session ID: ${session_id} · Horodatage: ${new Date(timestamp).toLocaleTimeString()}`}
        icon={<BookOpen size={18} />}
      />

      <div className="space-y-4 p-4 flex-1 text-xs">
        {/* Core decision callout */}
        <div
          className={cn(
            "rounded-lg border p-4 flex flex-col gap-2 relative overflow-hidden",
            final_decision.includes("CONFIRMÉ") || final_decision.includes("DÉTECTÉ") || final_decision === "BLOCK"
              ? "border-block/20 bg-block/5"
              : final_decision.includes("LÉGITIME") || final_decision.includes("SAIN") || final_decision === "ACCEPT"
              ? "border-accept/20 bg-accept/5"
              : "border-warn/20 bg-warn/5"
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-semibold text-[#f0f4ff] uppercase tracking-wider">Décision Finale du Conseil</span>
            <span
              className={cn(
                "rounded px-2.5 py-0.5 font-bold uppercase tracking-widest text-[10px]",
                final_decision.includes("CONFIRMÉ") || final_decision.includes("DÉTECTÉ") || final_decision === "BLOCK"
                  ? "bg-block/20 text-block"
                  : final_decision.includes("LÉGITIME") || final_decision.includes("SAIN") || final_decision === "ACCEPT"
                  ? "bg-accept/20 text-accept"
                  : "bg-warn/20 text-warn"
              )}
            >
              {final_decision}
            </span>
          </div>

          <p className="text-secondary leading-relaxed font-medium">
            {decision_justification}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-[10px] text-tertiary pt-1 border-t border-white/5 mt-1">
            <div>
              <span className="mr-1">Consensus:</span>
              <span className="font-semibold text-secondary">{consensus_score.toFixed(1)}%</span>
            </div>
            <div>
              <span className="mr-1">Confiance:</span>
              <span className="font-semibold text-secondary">{confidence_level}</span>
            </div>
            <div>
              <span className="mr-1">Risque Faux Positif:</span>
              <span className="font-semibold text-secondary">{false_positive_risk}</span>
            </div>
          </div>
        </div>

        {/* Audit trail elements */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <span className="text-[10px] text-secondary uppercase block tracking-wider">Experts Sollicités</span>
            <div className="flex flex-wrap gap-1">
              {experts_solicited.map((exp, idx) => (
                <span key={`${exp}-${idx}`} className="rounded bg-white/[0.03] border border-white/5 px-2 py-0.5 text-[10px] text-secondary">
                  {anonymizeExpert(exp)}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <span className="text-[10px] text-secondary uppercase block tracking-wider">Sources Consultées</span>
            <div className="flex flex-wrap gap-1">
              {sources_consulted.map((src, idx) => (
                <span key={`${src}-${idx}`} className="rounded bg-primary/10 border border-primary/20 px-2 py-0.5 text-[10px] text-primary">
                  {src}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Core Evidence List */}
        {evidence_summary && evidence_summary.length > 0 && (
          <div className="space-y-1.5 pt-2 border-t border-white/5">
            <span className="text-[10px] text-secondary uppercase block tracking-wider">Preuves Retenues</span>
            <ul className="list-disc list-inside space-y-1 text-secondary">
              {evidence_summary.map((ev, index) => (
                <li key={index} className="leading-relaxed pl-1 truncate" title={ev}>
                  {ev}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Next actions short summary */}
        {recommended_next_steps && recommended_next_steps.length > 0 && (
          <div className="space-y-1.5 pt-2 border-t border-white/5">
            <span className="text-[10px] text-secondary uppercase block tracking-wider">Premières Mesures Recommandées</span>
            <div className="space-y-1">
              {recommended_next_steps.map((step, index) => (
                <div key={index} className="flex items-center gap-2 rounded bg-white/[0.01] border border-white/5 px-2.5 py-1">
                  <ShieldCheck className="text-accept" size={12} />
                  <span className="text-secondary">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
