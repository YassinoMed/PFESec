"use client";

import type { ConflictItem } from "@/types/council";
import { resolveAgent } from "@/lib/councilApi";

interface ConflictResolutionPanelProps {
  conflicts: ConflictItem[];
}

export function ConflictResolutionPanel({ conflicts }: ConflictResolutionPanelProps) {
  if (conflicts.length === 0) {
    return (
      <div className="glass rounded-xl p-4">
        <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
          ⚡ Conflict Resolution
        </h3>
        <div className="flex items-center justify-center py-6 text-white/15 text-xs">
          No conflicts detected
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
        ⚡ Conflict Resolution
      </h3>
      <div className="space-y-2">
        {conflicts.map(c => {
          const leftAgent = resolveAgent(c.left);
          const rightAgent = resolveAgent(c.right);
          const isResolved = c.status === "resolved";

          return (
            <div
              key={c.id}
              className="rounded-lg p-3 border transition-all duration-500 animate-fade-up"
              style={{
                borderColor: isResolved ? "rgba(34,197,94,0.2)" : "rgba(248,113,113,0.3)",
                backgroundColor: isResolved ? "rgba(34,197,94,0.05)" : "rgba(248,113,113,0.05)",
              }}
            >
              {/* Versus header */}
              <div className="flex items-center gap-3 mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{leftAgent.emoji}</span>
                  <span className="text-xs font-semibold text-white/70">{leftAgent.name}</span>
                </div>
                <span className="text-xs font-bold text-red-400/60">VS</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-sm">{rightAgent.emoji}</span>
                  <span className="text-xs font-semibold text-white/70">{rightAgent.name}</span>
                </div>
                <span
                  className={`ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                    isResolved ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"
                  }`}
                >
                  {c.status}
                </span>
              </div>
              <p className="text-[11px] text-white/40 leading-relaxed">{c.detail}</p>
              {c.resolution && (
                <p className="text-[11px] text-green-400/60 mt-1.5 flex items-center gap-1">
                  <span>✅</span> {c.resolution}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
