"use client";

import type { MasterState } from "@/types/council";
import { PulseOrb } from "./ui/PulseOrb";

interface MasterCardProps {
  master: MasterState;
  onClick?: () => void;
}

const PHASE_LABELS: Record<string, string> = {
  idle: "Standby",
  activated: "Activated",
  querying_experts: "Querying Experts",
  analyzing: "Analyzing",
  debating: "Debating",
  completed: "Completed",
};

export function MasterCard({ master, onClick }: MasterCardProps) {
  const isActive = master.phase !== "idle";
  const isDone = master.phase === "completed";

  return (
    <button
      onClick={onClick}
      className="glass rounded-xl p-4 text-left relative overflow-hidden transition-all duration-500 hover:border-white/[0.14] group w-full"
      style={{
        borderColor: isActive ? `${master.color}30` : undefined,
        boxShadow: isActive ? `0 0 24px ${master.color}12` : undefined,
      }}
    >
      {/* Background gradient */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at 50% 0%, ${master.color}10, transparent 70%)`,
        }}
      />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-base"
              style={{ backgroundColor: `${master.color}15` }}
            >
              {master.emoji}
            </div>
            <div>
              <h4 className="text-[13px] font-semibold text-white">{master.name}</h4>
              <div className="flex items-center gap-1.5 text-[10px] text-white/40">
                <PulseOrb color={master.color} size={5} active={isActive && !isDone} />
                {PHASE_LABELS[master.phase] || master.phase}
              </div>
            </div>
          </div>
          {isActive && (
            <div
              className="text-lg font-bold tabular-nums"
              style={{ color: master.score >= 70 ? "#22c55e" : master.score >= 40 ? "#fbbf24" : master.color }}
            >
              {master.score > 0 ? `${master.score.toFixed(0)}%` : "—"}
            </div>
          )}
        </div>

        {/* Progress bar */}
        <div className="h-1 rounded-full bg-white/[0.06] mb-3 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${master.progress}%`,
              backgroundColor: master.color,
              boxShadow: `0 0 8px ${master.color}60`,
            }}
          />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center">
            <div className="text-xs font-semibold text-white/80">{master.experts_total}</div>
            <div className="text-[9px] text-white/30 uppercase">Experts</div>
          </div>
          <div className="text-center">
            <div className="text-xs font-semibold text-white/80">{master.models_used.length}</div>
            <div className="text-[9px] text-white/30 uppercase">Models</div>
          </div>
          <div className="text-center">
            <div className="text-xs font-semibold text-white/80">{master.evidence_count}</div>
            <div className="text-[9px] text-white/30 uppercase">Evidence</div>
          </div>
        </div>
      </div>
    </button>
  );
}
