"use client";

import type { CoordinatorPhase } from "@/types/council";
import { PulseOrb } from "./ui/PulseOrb";
import { GlowBadge } from "./ui/GlowBadge";

interface CoordinatorPanelProps {
  phase: CoordinatorPhase;
  eventCount: number;
  latestMessage?: string;
}

const PHASE_CONFIG: Record<CoordinatorPhase, { label: string; color: string; description: string }> = {
  idle:           { label: "Standby",         color: "#64748b", description: "En attente d'une requête" },
  planning:       { label: "Planning",        color: "#a78bfa", description: "Analyse de la requête et planification" },
  dispatching:    { label: "Dispatching",     color: "#38bdf8", description: "Activation des Masters AI" },
  waiting:        { label: "Monitoring",      color: "#fbbf24", description: "Surveillance des analyses en cours" },
  consensus:      { label: "Consensus",       color: "#34d399", description: "Consolidation des résultats" },
  final_decision: { label: "Final Decision",  color: "#22c55e", description: "Décision finale rendue" },
};

export function CoordinatorPanel({ phase, eventCount, latestMessage }: CoordinatorPanelProps) {
  const cfg = PHASE_CONFIG[phase];

  return (
    <div className="glass rounded-xl p-4 relative overflow-hidden">
      {/* Animated glow border */}
      <div
        className="absolute inset-0 rounded-xl opacity-30 pointer-events-none transition-all duration-1000"
        style={{
          boxShadow: `inset 0 0 30px ${cfg.color}20, 0 0 40px ${cfg.color}15`,
        }}
      />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
              style={{ backgroundColor: `${cfg.color}15`, boxShadow: `0 0 20px ${cfg.color}25` }}
            >
              🧠
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Global Coordinator AI</h3>
              <p className="text-[11px] text-white/40">{cfg.description}</p>
            </div>
          </div>
          <GlowBadge label={cfg.label} color={cfg.color} pulse={phase !== "idle" && phase !== "final_decision"} />
        </div>

        {/* Phase pipeline */}
        <div className="flex items-center gap-1 mb-3">
          {(Object.keys(PHASE_CONFIG) as CoordinatorPhase[]).filter(p => p !== "idle").map((p, i) => {
            const pCfg = PHASE_CONFIG[p];
            const phases = (Object.keys(PHASE_CONFIG) as CoordinatorPhase[]).filter(x => x !== "idle");
            const currentIdx = phases.indexOf(phase === "idle" ? "planning" : phase);
            const thisIdx = i;
            const isActive = thisIdx <= currentIdx && phase !== "idle";

            return (
              <div key={p} className="flex items-center gap-1 flex-1">
                <div
                  className="h-1.5 rounded-full flex-1 transition-all duration-700"
                  style={{
                    backgroundColor: isActive ? pCfg.color : "rgba(255,255,255,0.06)",
                    boxShadow: isActive ? `0 0 8px ${pCfg.color}50` : "none",
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-4 text-[11px] text-white/40">
          <div className="flex items-center gap-1.5">
            <PulseOrb color={cfg.color} size={6} active={phase !== "idle"} />
            <span>{eventCount} events</span>
          </div>
          {latestMessage && (
            <div className="flex-1 truncate text-white/30 italic">
              {latestMessage.slice(0, 80)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
