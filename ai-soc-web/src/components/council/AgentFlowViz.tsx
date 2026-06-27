"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Brain, Cpu, ShieldCheck } from "lucide-react";

interface AgentFlowVizProps {
  classification: string;
  selectedExperts: string[];
  consensusScore: number;
  finalDecision: string;
}

const anonymizeExpert = (id: string): string => {
  const map: Record<string, string> = {
    cysecbert: "Expert 1",
    secbert: "Expert 2",
    phishsense: "Expert 3",
    "phishsense-merged": "Expert 3",
    securityllm: "Expert 4",
    "securityllm-merged": "Expert 4",
    security_rag: "Expert RAG",
    rag: "Expert RAG",
  };
  if (id in map) return map[id];
  // Format virtual experts: phishing_expert -> Phishing Expert
  return id
    .replace(/_expert/g, "")
    .replace(/_virtual/g, "")
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
};

export default function AgentFlowViz({
  classification,
  selectedExperts,
  consensusScore,
  finalDecision,
}: AgentFlowVizProps) {
  const experts = selectedExperts.slice(0, 5); // display up to 5 for space

  return (
    <div className="relative flex flex-col items-center justify-between rounded-lg border border-white/5 bg-black/40 p-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none" />

      {/* SVG Canvas for connecting lines and animated dashes */}
      <svg className="absolute inset-0 h-full w-full pointer-events-none" style={{ minHeight: "260px" }}>
        {/* Animated paths from Master AI to Experts */}
        {experts.map((_, index) => {
          const startX = "50%";
          const startY = "30";
          const endX = `${15 + index * (70 / Math.max(experts.length - 1, 1))}%`;
          const endY = "120";

          return (
            <g key={`path-to-${index}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className="stroke-primary/10 stroke-[1.5]"
              />
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className="stroke-primary/40 stroke-[2] [stroke-dasharray:10,15]"
                style={{
                  animation: `dash ${2 + index * 0.4}s linear infinite`,
                }}
              />
            </g>
          );
        })}

        {/* Animated paths from Experts to Consensus */}
        {experts.map((_, index) => {
          const startX = `${15 + index * (70 / Math.max(experts.length - 1, 1))}%`;
          const startY = "155";
          const endX = "50%";
          const endY = "235";

          return (
            <g key={`path-from-${index}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className="stroke-white/5 stroke-[1.5]"
              />
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                className="stroke-accept/40 stroke-[1.5] [stroke-dasharray:8,12]"
                style={{
                  animation: `dash ${1.8 + index * 0.3}s linear infinite reverse`,
                }}
              />
            </g>
          );
        })}
      </svg>

      {/* Node 1: Master AI (Origin) */}
      <div className="relative z-10 flex flex-col items-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-primary/50 bg-[#0e1630] text-primary shadow-glow animate-pulse">
          <Brain size={22} />
        </div>
        <span className="mt-2 font-display text-xs font-semibold text-[#f0f4ff]">Master AI Engine</span>
        <span className="text-[10px] text-tertiary uppercase tracking-wider">{classification.replace(/_/g, " ")}</span>
      </div>

      {/* Node Row 2: Selected Experts */}
      <div className="relative z-10 flex w-full justify-around py-12">
        {experts.map((expert, index) => (
          <div key={expert} className="flex flex-col items-center max-w-[90px] text-center">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-[#161b22] text-secondary hover:border-primary/40 hover:text-primary transition-all duration-300">
              <Cpu size={16} />
            </div>
            <span className="mt-1.5 truncate w-full text-[10px] font-medium text-[#f0f4ff]">
              {anonymizeExpert(expert)}
            </span>
          </div>
        ))}
      </div>

      {/* Node 3: Consensus & Result (Destination) */}
      <div className="relative z-10 flex flex-col items-center">
        <div
          className={cn(
            "flex h-11 w-11 items-center justify-center rounded-full border bg-[#0d1f14] shadow-lg",
            finalDecision === "BLOCK"
              ? "border-block/40 text-block bg-[#200d0d]"
              : finalDecision === "ACCEPT"
              ? "border-accept/40 text-accept"
              : "border-warn/40 text-warn bg-[#201c0d]"
          )}
        >
          <ShieldCheck size={20} />
        </div>
        <span className="mt-1.5 font-display text-xs font-semibold text-[#f0f4ff]">
          Consensus: {consensusScore.toFixed(0)}%
        </span>
        <span
          className={cn(
            "text-[10px] font-bold uppercase tracking-widest mt-0.5",
            finalDecision === "BLOCK"
              ? "text-block"
              : finalDecision === "ACCEPT"
              ? "text-accept"
              : "text-warn"
          )}
        >
          {finalDecision}
        </span>
      </div>

      {/* CSS Keyframes injected dynamically */}
      <style jsx global>{`
        @keyframes dash {
          to {
            stroke-dashoffset: -40;
          }
        }
      `}</style>
    </div>
  );
}
