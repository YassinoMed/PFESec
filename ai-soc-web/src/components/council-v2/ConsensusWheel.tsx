"use client";

import React from "react";
import type { WeightedConsensusData } from "@/types/council";
import { MASTERS } from "@/lib/councilApi";

interface ConsensusWheelProps {
  consensus: WeightedConsensusData | null;
}

export function ConsensusWheel({ consensus }: ConsensusWheelProps) {
  const finalScore = consensus?.score ?? 0;
  const verdict = consensus?.verdict_final ?? "PENDING";
  const confidence = consensus?.confidence_level ?? "LOCKED";
  
  // Weights configuration
  const weights = consensus?.weights_used ?? {
    threat_master: 0.35,
    soc_master: 0.30,
    rag_master: 0.25,
    governance_master: 0.10,
  };

  // Compute SVG angles
  let currentAngle = 0;
  const radius = 55;
  const circumference = 2 * Math.PI * radius;

  const masterVotes = MASTERS.map(m => {
    const verdictData = consensus?.master_verdicts?.[m.id];
    const weight = weights[m.id] ?? 0.25;
    const voteVerdict = verdictData?.conclusion ?? "UNKNOWN";
    const voteScore = verdictData?.score ?? 0;
    
    let strokeColor = "rgba(255,255,255,0.06)";
    if (voteVerdict === "BLOCK") strokeColor = "#f87171"; // Red
    else if (voteVerdict === "ACCEPT") strokeColor = "#34d399"; // Green
    else if (voteVerdict === "UNCERTAIN") strokeColor = "#fbbf24"; // Amber

    return {
      ...m,
      weight,
      verdict: voteVerdict,
      score: voteScore,
      strokeColor,
    };
  });

  return (
    <div className="glass rounded-xl p-4 flex flex-col h-full justify-between">
      <div>
        <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-4 flex items-center gap-1.5">
          <span>⚖️</span> Weighted Consensus Wheel
        </h3>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 my-2">
          {/* SVG Segmented Donut Chart */}
          <div className="relative w-36 h-36 flex-shrink-0 flex items-center justify-center">
            <svg width="144" height="144" className="rotate-[-90deg]">
              {/* Central shadow circle */}
              <circle cx="72" cy="72" r={radius} fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="12" />
              {masterVotes.map((mv) => {
                const strokeDashoffset = circumference - (mv.weight * circumference);
                const rotation = currentAngle;
                currentAngle += mv.weight * 360;

                return (
                  <circle
                    key={mv.id}
                    cx="72"
                    cy="72"
                    r={radius}
                    fill="none"
                    stroke={mv.strokeColor}
                    strokeWidth="12"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    transform={`rotate(${rotation} 72 72)`}
                    className="transition-all duration-1000 ease-out"
                    style={{
                      filter: mv.verdict !== "UNKNOWN" ? `drop-shadow(0 0 4px ${mv.strokeColor}80)` : "none",
                    }}
                  />
                );
              })}
            </svg>

            {/* Inner Dashboard read-out */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-[10px] uppercase tracking-widest text-white/40">Consensus</span>
              <span className="text-2xl font-bold text-white tabular-nums">
                {finalScore > 0 ? `${finalScore.toFixed(0)}%` : "—"}
              </span>
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full mt-1 ${
                  verdict === "BLOCK" ? "text-red-400 bg-red-500/10" :
                  verdict === "ACCEPT" ? "text-green-400 bg-green-500/10" :
                  "text-white/30 bg-white/5"
                }`}
              >
                {verdict}
              </span>
            </div>
          </div>

          {/* Legend / Contributions */}
          <div className="flex-1 w-full space-y-2">
            {masterVotes.map((mv) => {
              const active = mv.verdict !== "UNKNOWN";
              return (
                <div
                  key={mv.id}
                  className="flex items-center justify-between text-xs p-1.5 rounded bg-white/[0.01] hover:bg-white/[0.03] transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{mv.emoji}</span>
                    <span className="font-medium text-white/70">{mv.name}</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-white/5 text-white/40">
                      W: {(mv.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-right">
                    {active ? (
                      <span className="font-mono font-bold" style={{ color: mv.strokeColor }}>
                        {mv.verdict} ({mv.score.toFixed(0)}%)
                      </span>
                    ) : (
                      <span className="text-white/20 font-mono">WAITING</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer explanation */}
      {consensus?.decision_justification && (
        <div className="mt-2 text-[11px] text-white/45 bg-white/[0.02] border border-white/[0.04] rounded-lg p-2.5">
          <span className="font-semibold text-white/75 block mb-0.5">Fusion Verdict Justification:</span>
          <p className="line-clamp-2 leading-relaxed">{consensus.decision_justification}</p>
        </div>
      )}
    </div>
  );
}
