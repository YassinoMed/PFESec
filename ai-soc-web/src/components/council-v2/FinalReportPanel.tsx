"use client";

import React from "react";
import type { CouncilResultFull } from "@/types/council";
import { Download, Shield, AlertCircle, FileText, ChevronRight } from "lucide-react";

interface FinalReportPanelProps {
  result: CouncilResultFull | null;
}

export function FinalReportPanel({ result }: FinalReportPanelProps) {
  if (!result) {
    return (
      <div className="glass rounded-xl p-6 text-center">
        <FileText className="mx-auto text-white/10 mb-2" size={32} />
        <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider">Final Incident Report</h3>
        <p className="text-xs text-white/20 mt-1">Waiting for committee deliberation to complete...</p>
      </div>
    );
  }

  const verdict = result.weighted_consensus?.verdict_final ?? "UNKNOWN";
  const confidence = result.weighted_consensus?.confidence_level ?? "UNKNOWN";
  const score = result.weighted_consensus?.score ?? 0;
  
  // Extract response plan containment/eradication actions
  const containment = result.response_plan?.containment ?? [];
  const eradication = result.response_plan?.eradication ?? [];
  const recovery = result.response_plan?.recovery ?? [];
  const prevention = result.response_plan?.prevention ?? [];

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `SecureRAG_Council_Report_${result.session_id || "export"}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="glass rounded-xl p-5 space-y-5 animate-fade-up">
      {/* Header briefing */}
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-4 gap-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            verdict === "BLOCK" ? "bg-red-500/10 text-red-400" : "bg-green-500/10 text-green-400"
          }`}>
            <Shield size={20} />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">AI Council Security Briefing</h3>
            <span className="text-[10px] text-white/30 uppercase tracking-wider font-mono">
              Session ID: {result.session_id} · Ref: {result.classification}
            </span>
          </div>
        </div>

        <button
          onClick={handleExport}
          className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-dim text-white text-xs font-semibold flex items-center gap-2 shadow-glow transition-all"
        >
          <Download size={14} /> Export Report JSON
        </button>
      </div>

      {/* Main summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[10px] text-white/40 uppercase block mb-1">Final Verdict</span>
          <span className={`text-lg font-black tracking-wide ${
            verdict === "BLOCK" ? "text-red-400" : "text-green-400"
          }`}>
            {verdict}
          </span>
        </div>
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[10px] text-white/40 uppercase block mb-1">Stability Consensus</span>
          <span className="text-lg font-black text-white tabular-nums">
            {score.toFixed(1)}% <span className="text-xs text-white/40 font-medium">({confidence})</span>
          </span>
        </div>
        <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
          <span className="text-[10px] text-white/40 uppercase block mb-1">Resolution Protocol</span>
          <span className="text-xs font-semibold text-cyan-400 block mt-1">
            {result.response_plan?.containment ? "AUTOMATED ORCHESTRATION" : "MANUAL INTERVENTION"}
          </span>
        </div>
      </div>

      {/* RAG & Justification Summary */}
      {result.weighted_consensus?.decision_justification && (
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
          <h4 className="text-xs font-bold text-white/80 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <AlertCircle size={14} className="text-primary" /> Incident Mitigation Rationale
          </h4>
          <p className="text-xs text-white/60 leading-relaxed font-sans">
            {result.weighted_consensus.decision_justification}
          </p>
        </div>
      )}

      {/* Response Plan playbooks */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-white/70 uppercase tracking-wider">
          🛠 Immediate Action Plan (Incident Response Playbook)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Containment actions */}
          <div className="p-3.5 rounded-xl bg-white/[0.01] border border-white/[0.03]">
            <h5 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2.5">
              1. Containment (Confinement)
            </h5>
            {containment.length > 0 ? (
              <div className="space-y-2">
                {containment.map((act, i) => (
                  <div key={i} className="flex gap-2.5 items-start text-xs">
                    <ChevronRight size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white/85">{act.action}</span>
                      <p className="text-white/40 text-[10px] leading-relaxed mt-0.5">{act.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-white/20 italic">No direct containment actions listed.</p>
            )}
          </div>

          {/* Eradication & Remediation */}
          <div className="p-3.5 rounded-xl bg-white/[0.01] border border-white/[0.03]">
            <h5 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5">
              2. Eradication & Remediation
            </h5>
            {eradication.length > 0 ? (
              <div className="space-y-2">
                {eradication.map((act, i) => (
                  <div key={i} className="flex gap-2.5 items-start text-xs">
                    <ChevronRight size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white/85">{act.action}</span>
                      <p className="text-white/40 text-[10px] leading-relaxed mt-0.5">{act.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-white/20 italic">No direct eradication actions listed.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
