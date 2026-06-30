"use client";

import { useState } from "react";
import type { CouncilResultFull } from "@/types/council";
import { resolveAgent } from "@/lib/councilApi";
import { ChevronDown, ChevronRight } from "lucide-react";

interface ExpertDrilldownProps {
  result: CouncilResultFull | null;
}

export function ExpertDrilldown({ result }: ExpertDrilldownProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!result?.experts || result.experts.length === 0) {
    return (
      <div className="glass rounded-xl p-4">
        <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
          🔬 Expert Drilldown
        </h3>
        <p className="text-xs text-white/20">Waiting for expert analysis results...</p>
      </div>
    );
  }

  // Group experts by their category (maps to master)
  const groups: Record<string, typeof result.experts> = {};
  for (const exp of result.experts) {
    const cat = exp.category || "unknown";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(exp);
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
        🔬 Expert ↔ Model Drilldown
      </h3>
      <div className="space-y-2">
        {Object.entries(groups).map(([category, experts]) => (
          <div key={category} className="rounded-lg border border-white/[0.06] overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === category ? null : category)}
              className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-white/[0.03] transition-colors"
            >
              {expanded === category ? <ChevronDown size={12} className="text-white/30" /> : <ChevronRight size={12} className="text-white/30" />}
              <span className="text-[11px] font-semibold text-white/60 uppercase">{category.replace(/_/g, " ")}</span>
              <span className="text-[10px] text-white/20 ml-auto">{experts.length} experts</span>
            </button>
            {expanded === category && (
              <div className="border-t border-white/[0.04] px-3 py-2 space-y-2">
                {experts.map((exp, i) => {
                  const agent = resolveAgent(exp.expert_id);
                  return (
                    <div key={`${exp.expert_id}-${i}`} className="rounded-lg bg-white/[0.02] p-2.5">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-sm">{agent.emoji}</span>
                        <span className="text-xs font-semibold text-white/70">{agent.name}</span>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                            exp.status === "success" ? "text-green-400 bg-green-400/10" :
                            exp.status === "error" ? "text-red-400 bg-red-400/10" :
                            "text-amber-400 bg-amber-400/10"
                          }`}
                        >
                          {exp.status}
                        </span>
                        {exp.confidence > 0 && (
                          <span className="text-[10px] text-white/30 ml-auto tabular-nums">
                            {(exp.confidence * 100).toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-white/50 leading-relaxed">{exp.conclusion}</p>
                      {exp.evidence.length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {exp.evidence.slice(0, 3).map((e, j) => (
                            <span key={j} className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.04] text-white/30">
                              {e.slice(0, 60)}
                            </span>
                          ))}
                        </div>
                      )}
                      {exp.inference_ms > 0 && (
                        <div className="text-[10px] text-white/20 mt-1">
                          ⏱ {exp.inference_ms >= 1000 ? `${(exp.inference_ms / 1000).toFixed(1)}s` : `${exp.inference_ms}ms`}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
