"use client";

import React from "react";
import type { TimelineEntry } from "@/types/council";

interface TimelinePanelProps {
  timeline: TimelineEntry[];
}

export function TimelinePanel({ timeline }: TimelinePanelProps) {
  return (
    <div className="glass rounded-xl p-4 flex flex-col h-full">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-4 flex items-center gap-1.5">
        <span>🕒</span> Full Analysis Timeline
      </h3>

      <div className="flex-1 overflow-y-auto space-y-4 relative pl-4 max-h-[400px]">
        {/* Central timeline line */}
        <div className="absolute left-6 top-1 bottom-1 w-0.5 bg-white/[0.06] pointer-events-none" />

        {timeline.map((entry, idx) => {
          const duration = entry.duration_ms;
          return (
            <div
              key={entry.id}
              className="flex gap-4 relative animate-fade-up"
              style={{ animationDelay: `${Math.min(idx * 20, 300)}ms` }}
            >
              {/* Timeline marker node */}
              <div className="relative z-10 w-4 h-4 rounded-full bg-[#090d1a] border-2 border-primary flex items-center justify-center flex-shrink-0 mt-1 shadow-glow">
                <span className="text-[7px] text-white">{entry.agentEmoji}</span>
              </div>

              {/* Event card */}
              <div className="flex-1 bg-white/[0.02] border border-white/[0.04] rounded-lg p-2.5 hover:bg-white/[0.04] transition-colors">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-bold text-white/70">{entry.agent}</span>
                  <span className="text-[9px] text-white/35 font-mono">
                    {new Date(entry.timestamp).toLocaleTimeString("en-GB")}
                  </span>
                </div>
                <p className="text-[11px] text-white/50 leading-relaxed">{entry.action}</p>
                {duration > 0 && (
                  <span className="text-[9px] text-primary/75 mt-1 block">
                    ⏱ {duration >= 1000 ? `${(duration / 1000).toFixed(2)}s` : `${duration.toFixed(0)}ms`}
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {timeline.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <span className="text-xl mb-1 text-white/20">⏳</span>
            <p className="text-xs text-white/20">Waiting for incident execution sequence...</p>
          </div>
        )}
      </div>
    </div>
  );
}
