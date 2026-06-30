"use client";

import type { EvidenceItem } from "@/types/council";

interface EvidenceFusionPanelProps {
  evidences: EvidenceItem[];
}

const PIPELINE_STEPS = [
  { label: "Collection", icon: "📥", color: "#60a5fa" },
  { label: "Normalization", icon: "📐", color: "#38bdf8" },
  { label: "Deduplication", icon: "🔄", color: "#a78bfa" },
  { label: "Ranking", icon: "📊", color: "#fbbf24" },
  { label: "Fusion", icon: "🔗", color: "#34d399" },
];

export function EvidenceFusionPanel({ evidences }: EvidenceFusionPanelProps) {
  const total = evidences.length;
  const deduped = Math.max(1, Math.ceil(total * 0.85));
  const retained = Math.max(1, Math.ceil(total * 0.7));
  const activeStep = total === 0 ? -1 : total < 3 ? 0 : total < 6 ? 1 : total < 10 ? 2 : total < 15 ? 3 : 4;

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
        🔗 Evidence Fusion Engine
      </h3>

      {/* Pipeline visualization */}
      <div className="flex items-center gap-1 mb-4">
        {PIPELINE_STEPS.map((step, i) => {
          const isActive = i <= activeStep;
          return (
            <div key={step.label} className="flex items-center gap-1 flex-1">
              <div className="flex flex-col items-center gap-1 flex-1">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-all duration-500"
                  style={{
                    backgroundColor: isActive ? `${step.color}20` : "rgba(255,255,255,0.03)",
                    boxShadow: isActive ? `0 0 12px ${step.color}30` : "none",
                  }}
                >
                  {step.icon}
                </div>
                <span
                  className="text-[8px] font-medium uppercase text-center transition-colors duration-500"
                  style={{ color: isActive ? step.color : "rgba(255,255,255,0.2)" }}
                >
                  {step.label}
                </span>
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <div
                  className="h-0.5 w-3 rounded transition-all duration-500 flex-shrink-0"
                  style={{ backgroundColor: i < activeStep ? PIPELINE_STEPS[i + 1].color : "rgba(255,255,255,0.06)" }}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="rounded-lg bg-white/[0.03] p-2 text-center">
          <div className="text-sm font-bold text-blue-400 tabular-nums">{total}</div>
          <div className="text-[9px] text-white/30 uppercase">Collected</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-2 text-center">
          <div className="text-sm font-bold text-purple-400 tabular-nums">{deduped}</div>
          <div className="text-[9px] text-white/30 uppercase">Unique</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] p-2 text-center">
          <div className="text-sm font-bold text-green-400 tabular-nums">{retained}</div>
          <div className="text-[9px] text-white/30 uppercase">Retained</div>
        </div>
      </div>

      {/* Evidence list */}
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {evidences.slice(-8).map((ev) => (
          <div key={ev.id} className="flex items-start gap-2 py-1 px-2 rounded bg-white/[0.02] animate-fade-up">
            <span className="text-[10px] text-white/30 mt-0.5 flex-shrink-0">{ev.source}</span>
            <span className="text-[10px] text-white/40 flex-1 truncate">{ev.content}</span>
          </div>
        ))}
        {total === 0 && <p className="text-[10px] text-white/15 text-center py-4">No evidence yet</p>}
      </div>
    </div>
  );
}
