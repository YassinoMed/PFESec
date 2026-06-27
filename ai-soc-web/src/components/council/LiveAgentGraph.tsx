"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Brain, Cpu, Layers, ShieldAlert, Sparkles } from "lucide-react";

export type ExpertState =
  | "idle"
  | "analysing"
  | "waiting"
  | "cross_validation"
  | "consensus"
  | "finished"
  | "error";

interface ExpertNode {
  id: string;
  name: string;
  state: ExpertState;
  colorClass: string;
}

interface LiveAgentGraphProps {
  experts: ExpertNode[];
  activeExpertId: string | null;
  phase: string; // e.g., "comprehension", "planning", "analysis", "debate", "consensus", "done"
}

const getStateColor = (state: ExpertState) => {
  switch (state) {
    case "idle":
      return "bg-neutral-600 border-neutral-500 shadow-neutral-900";
    case "analysing":
      return "bg-blue-600 border-blue-400 shadow-blue-500/50 animate-pulse";
    case "waiting":
      return "bg-yellow-500 border-yellow-300 shadow-yellow-500/40";
    case "cross_validation":
      return "bg-orange-500 border-orange-300 shadow-orange-500/40 animate-pulse";
    case "consensus":
      return "bg-purple-600 border-purple-400 shadow-purple-500/50";
    case "finished":
      return "bg-accept border-emerald-400 shadow-emerald-500/40";
    case "error":
      return "bg-block border-red-400 shadow-red-500/50 animate-bounce";
    default:
      return "bg-neutral-600";
  }
};

const getStateLabel = (state: ExpertState) => {
  switch (state) {
    case "idle":
      return "🟢 Idle";
    case "analysing":
      return "🔵 Analysing";
    case "waiting":
      return "🟡 Waiting";
    case "cross_validation":
      return "🟠 Cross Validation";
    case "consensus":
      return "🟣 Consensus";
    case "finished":
      return "✅ Finished";
    case "error":
      return "❌ Error";
    default:
      return "Unknown";
  }
};

export default function LiveAgentGraph({ experts, activeExpertId, phase }: LiveAgentGraphProps) {
  // Show a subset of experts to keep layout clean and responsive
  const displayExperts = experts.slice(0, 6);

  return (
    <div className="relative flex flex-col items-center justify-between rounded-lg border border-white/5 bg-black/40 p-6 overflow-hidden h-[340px]">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />

      {/* SVG Connections & Glows */}
      <svg className="absolute inset-0 h-full w-full pointer-events-none">
        <defs>
          <filter id="glow-effect" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Connections from Master AI to Experts */}
        {displayExperts.map((expert, idx) => {
          const startX = "50%";
          const startY = "40";
          const endX = `${12 + idx * (76 / Math.max(displayExperts.length - 1, 1))}%`;
          const endY = "160";
          const isActive = activeExpertId === expert.id || expert.state === "analysing";

          return (
            <g key={`to-${expert.id}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className={cn(
                  "transition-all duration-500",
                  isActive ? "stroke-primary/50 stroke-[2.5]" : "stroke-white/5 stroke-[1.5]"
                )}
                filter={isActive ? "url(#glow-effect)" : undefined}
              />
              {isActive && (
                <line
                  x1={startX}
                  y1={startY}
                  x2={endX}
                  y2={endY}
                  className="stroke-primary stroke-[2] [stroke-dasharray:10,15]"
                  style={{ animation: "dash 1.5s linear infinite" }}
                />
              )}
            </g>
          );
        })}

        {/* Connections from Experts to Consensus */}
        {displayExperts.map((expert, idx) => {
          const startX = `${12 + idx * (76 / Math.max(displayExperts.length - 1, 1))}%`;
          const startY = "195";
          const endX = "50%";
          const endY = "270";
          const isDone = expert.state === "finished" || phase === "consensus" || phase === "done";

          return (
            <g key={`from-${expert.id}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className={cn(
                  "transition-all duration-500",
                  isDone ? "stroke-accept/40 stroke-[2]" : "stroke-white/5 stroke-[1.5]"
                )}
              />
              {isDone && phase === "consensus" && (
                <line
                  x1={startX}
                  y1={startY}
                  x2={endX}
                  y2={endY}
                  className="stroke-accept stroke-[1.5] [stroke-dasharray:6,10]"
                  style={{ animation: "dash 1.2s linear infinite reverse" }}
                />
              )}
            </g>
          );
        })}

        {/* Connection from Consensus to Final Report */}
        <line
          x1="50%"
          y1="305"
          x2="50%"
          y2="330"
          className={cn(
            "transition-all duration-500",
            phase === "done" ? "stroke-accept/60 stroke-[3]" : "stroke-white/5 stroke-[1.5]"
          )}
          filter={phase === "done" ? "url(#glow-effect)" : undefined}
        />
      </svg>

      {/* Layer 1: Master AI Node */}
      <div className="relative z-10 flex flex-col items-center">
        <div
          className={cn(
            "flex h-11 w-11 items-center justify-center rounded-full border bg-[#0d1630] text-primary transition-all duration-500 shadow-md",
            phase === "comprehension" || phase === "planning"
              ? "border-primary shadow-primary/40 scale-105 animate-pulse"
              : "border-primary/30"
          )}
        >
          <Brain size={20} />
        </div>
        <span className="mt-1 font-display text-[10px] font-semibold text-[#f0f4ff]">Master AI Engine</span>
      </div>

      {/* Layer 2: Experts Row */}
      <div className="relative z-10 flex w-full justify-around pt-6">
        {displayExperts.map((expert) => {
          const isActive = activeExpertId === expert.id;
          return (
            <div key={expert.id} className="flex flex-col items-center max-w-[80px] text-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-lg border bg-[#161b22] text-secondary transition-all duration-300",
                  isActive ? "border-primary text-primary scale-110 shadow-[0_0_8px_rgba(59,130,246,0.5)]" : "border-white/5"
                )}
              >
                <Cpu size={14} />
              </div>
              <span className="mt-1 truncate w-full text-[9px] font-semibold text-[#f0f4ff]">
                {expert.name}
              </span>
              <div className="flex items-center gap-1 mt-0.5">
                <span className={cn("h-1.5 w-1.5 rounded-full border shadow-inner", getStateColor(expert.state))} />
                <span className="text-[7px] font-mono text-tertiary uppercase tracking-wider">
                  {expert.state.replace("_", " ")}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Layer 3: Consensus Node */}
      <div className="relative z-10 flex flex-col items-center pt-2">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full border bg-[#0f1b15] text-[#22c55e] transition-all duration-500 shadow-md",
            phase === "consensus"
              ? "border-accept shadow-accept/40 scale-105 animate-pulse"
              : "border-white/5 text-secondary"
          )}
        >
          <Layers size={16} />
        </div>
        <span className="mt-1 font-display text-[9px] font-semibold text-[#f0f4ff]">Consensus Engine</span>
      </div>

      {/* Layer 4: Final Report Node */}
      <div className="relative z-10 flex flex-col items-center">
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg border transition-all duration-500 shadow-md",
            phase === "done"
              ? "border-accept bg-[#102a1c] text-accept scale-105 shadow-accept/30"
              : "border-white/5 bg-[#161b22] text-tertiary"
          )}
        >
          <Sparkles size={14} />
        </div>
        <span className="mt-1 font-display text-[9px] font-semibold text-[#f0f4ff]">Final Report</span>
      </div>
    </div>
  );
}
