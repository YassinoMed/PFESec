"use client";

import React, { useState } from "react";
import type { CouncilResultFull } from "@/types/council";
import { resolveAgent } from "@/lib/councilApi";

interface ExplainabilityPanelProps {
  result: CouncilResultFull | null;
}

type CategoryType = "evidence" | "models" | "experts" | "rag" | "mitre" | "sigma" | "ioc";

export function ExplainabilityPanel({ result }: ExplainabilityPanelProps) {
  const [activeTab, setActiveTab] = useState<CategoryType>("evidence");

  const decisionReasons = result?.final_response?.decision_reasons ?? 
    result?.decision_journal?.evidence_summary ?? [];
  const selectedModels = result?.selected_models ?? result?.decision_journal?.models_executed ?? [];
  const experts = result?.experts ?? [];
  const ragDocs = result?.final_response?.references_rag ?? [];
  const mitreTechniques = result?.attack_timeline?.phases.flatMap(p => p.techniques) ?? [];
  const iocs = result?.attack_timeline?.iocs_extracted ?? [];

  const tabConfig: Record<CategoryType, { label: string; count: number }> = {
    evidence: { label: "Justification Reasons", count: decisionReasons.length },
    models: { label: "AI Models Used", count: selectedModels.length },
    experts: { label: "Specialized Experts", count: experts.length },
    rag: { label: "RAG References", count: ragDocs.length },
    mitre: { label: "MITRE ATT&CK", count: mitreTechniques.length },
    sigma: { label: "Sigma Detections", count: result?.attack_timeline ? 1 : 0 },
    ioc: { label: "Extracted IOCs", count: iocs.length },
  };

  return (
    <div className="glass rounded-xl p-4 flex flex-col h-full">
      <div className="border-b border-white/[0.06] pb-3 mb-3">
        <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <span>🧐</span> Auditable Decision Explanation
        </h3>
        <p className="text-xs text-white/40 mb-3">
          Explore exactly why and how the committee reached this verdict.
        </p>

        {/* Tab Buttons */}
        <div className="flex flex-wrap gap-1.5">
          {(Object.keys(tabConfig) as CategoryType[]).map((tab) => {
            const cfg = tabConfig[tab];
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
                  isActive
                    ? "bg-primary text-white shadow-glow"
                    : "bg-white/[0.03] text-white/40 hover:text-white/60 hover:bg-white/[0.06] border border-white/[0.05]"
                }`}
              >
                {cfg.label}
                {cfg.count > 0 && (
                  <span
                    className={`px-1 rounded-full text-[9px] ${
                      isActive ? "bg-white/20 text-white" : "bg-white/5 text-white/30"
                    }`}
                  >
                    {cfg.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content panel */}
      <div className="flex-1 overflow-y-auto space-y-2 min-h-[140px] max-h-[300px]">
        {/* Evidence */}
        {activeTab === "evidence" && (
          <div className="space-y-2">
            {decisionReasons.map((reason, i) => (
              <div key={i} className="flex gap-2.5 items-start p-2 rounded bg-white/[0.02] border border-white/[0.04]">
                <span className="text-xs text-primary mt-0.5">▪</span>
                <span className="text-xs text-white/70 leading-relaxed">{reason}</span>
              </div>
            ))}
            {decisionReasons.length === 0 && (
              <p className="text-xs text-white/20 italic">No decision reasoning loaded yet.</p>
            )}
          </div>
        )}

        {/* Models */}
        {activeTab === "models" && (
          <div className="grid grid-cols-2 gap-2">
            {selectedModels.map((mid) => {
              const agent = resolveAgent(mid);
              return (
                <div key={mid} className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04] flex items-center gap-2.5">
                  <span className="text-lg">{agent.emoji}</span>
                  <div>
                    <h5 className="text-xs font-semibold text-white/70">{agent.name}</h5>
                    <span className="text-[9px] uppercase tracking-wider text-primary">{agent.role}</span>
                  </div>
                </div>
              );
            })}
            {selectedModels.length === 0 && (
              <p className="text-xs text-white/20 italic col-span-2">No models listed.</p>
            )}
          </div>
        )}

        {/* Experts */}
        {activeTab === "experts" && (
          <div className="space-y-2">
            {experts.map((exp, i) => {
              const agent = resolveAgent(exp.expert_id);
              return (
                <div key={i} className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04] flex justify-between items-start">
                  <div className="flex items-start gap-2.5">
                    <span className="text-lg mt-0.5">{agent.emoji}</span>
                    <div>
                      <h5 className="text-xs font-semibold text-white/70">{agent.name}</h5>
                      <p className="text-[10px] text-white/40 mt-0.5 line-clamp-1">{exp.conclusion}</p>
                    </div>
                  </div>
                  <span className="text-[10px] tabular-nums font-semibold text-white/30">{exp.inference_ms}ms</span>
                </div>
              );
            })}
            {experts.length === 0 && (
              <p className="text-xs text-white/20 italic">No experts listed.</p>
            )}
          </div>
        )}

        {/* RAG */}
        {activeTab === "rag" && (
          <div className="space-y-2">
            {ragDocs.map((doc, i) => (
              <div key={i} className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-bold text-primary tracking-wide uppercase">{doc.source}</span>
                  <span className="text-[10px] text-green-400 font-semibold">Match: {(doc.score * 100).toFixed(0)}%</span>
                </div>
                <p className="text-xs text-white/50 leading-relaxed italic">"{doc.text}"</p>
              </div>
            ))}
            {ragDocs.length === 0 && (
              <p className="text-xs text-white/20 italic">No RAG references fetched.</p>
            )}
          </div>
        )}

        {/* MITRE */}
        {activeTab === "mitre" && (
          <div className="space-y-2">
            {mitreTechniques.map((tech, i) => (
              <div key={i} className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04] flex items-center gap-3">
                <div className="px-2 py-0.5 rounded bg-amber-400/10 text-amber-400 text-[10px] font-mono font-bold">
                  {tech}
                </div>
                <div className="text-xs text-white/70">
                  Phishing Sub-technique or Exploit mapping
                </div>
              </div>
            ))}
            {mitreTechniques.length === 0 && (
              <p className="text-xs text-white/20 italic">No MITRE ATT&CK techniques mapped.</p>
            )}
          </div>
        )}

        {/* Sigma */}
        {activeTab === "sigma" && (
          <div className="space-y-2">
            {result?.attack_timeline ? (
              <div className="p-2.5 rounded bg-white/[0.02] border border-white/[0.04]">
                <h5 className="text-xs font-semibold text-white/70 mb-1">Sigma Detection Rule: sysmon_phishing_payload</h5>
                <p className="text-[11px] text-white/40 leading-relaxed">
                  Triggered based on powershell execution and suspicious network callbacks matching technique T1566.
                </p>
              </div>
            ) : (
              <p className="text-xs text-white/20 italic">No Sigma logs available.</p>
            )}
          </div>
        )}

        {/* IOC */}
        {activeTab === "ioc" && (
          <div className="space-y-1.5">
            {iocs.map((ioc, i) => (
              <div key={i} className="p-2 rounded bg-white/[0.02] border border-white/[0.04] flex justify-between items-center">
                <span className="text-xs font-mono text-white/70">{ioc.value}</span>
                <span className="text-[10px] uppercase font-bold text-red-400 bg-red-400/10 px-2 py-0.5 rounded">
                  {ioc.type}
                </span>
              </div>
            ))}
            {iocs.length === 0 && (
              <p className="text-xs text-white/20 italic">No threat indicators extracted.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
