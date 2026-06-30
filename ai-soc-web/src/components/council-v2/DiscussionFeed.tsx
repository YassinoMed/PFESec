"use client";

import { useEffect, useRef, useState } from "react";
import type { DiscussionMessage, CouncilEventType } from "@/types/council";
import { TypingIndicator } from "./ui/TypingIndicator";

interface DiscussionFeedProps {
  messages: DiscussionMessage[];
  isStreaming: boolean;
}

type FilterKey = "all" | "masters" | "experts" | "coordinator" | "conflicts";

const ROLE_COLORS: Record<string, string> = {
  coordinator: "#a78bfa",
  master: "#60a5fa",
  expert: "#38bdf8",
  model: "#f472b6",
  engine: "#fbbf24",
};

const EVENT_BADGES: Partial<Record<CouncilEventType, { label: string; color: string }>> = {
  master_activation: { label: "ACTIVATION", color: "#22c55e" },
  expert_query: { label: "QUERY", color: "#38bdf8" },
  expert_response: { label: "RESPONSE", color: "#34d399" },
  discussion: { label: "DEBATE", color: "#a78bfa" },
  contradiction: { label: "CONFLICT", color: "#f87171" },
  contradiction_resolved: { label: "RESOLVED", color: "#22c55e" },
  consensus_final: { label: "CONSENSUS", color: "#fbbf24" },
  report: { label: "REPORT", color: "#34d399" },
};

const FILTER_CONFIG: Record<FilterKey, { label: string; match: (m: DiscussionMessage) => boolean }> = {
  all: { label: "All", match: () => true },
  masters: { label: "Masters", match: m => m.role === "master" },
  experts: { label: "Experts", match: m => m.role === "expert" || m.role === "model" },
  coordinator: { label: "Coordinator", match: m => m.role === "coordinator" || m.role === "engine" },
  conflicts: { label: "Conflicts", match: m => m.eventType === "contradiction" || m.eventType === "contradiction_resolved" },
};

export function DiscussionFeed({ messages, isStreaming }: DiscussionFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [autoScroll, setAutoScroll] = useState(true);

  const filtered = messages.filter(FILTER_CONFIG[filter].match);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [filtered.length, autoScroll]);

  // Detect manual scroll to disable auto-scroll
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    setAutoScroll(atBottom);
  };

  return (
    <div className="glass rounded-xl flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">🗣️</span>
          <h3 className="text-xs font-semibold text-white/70 uppercase tracking-wider">Inter-Agent Discussion</h3>
          <span className="text-[10px] text-white/30 tabular-nums">{messages.length} messages</span>
        </div>
        {/* Filters */}
        <div className="flex gap-1">
          {(Object.keys(FILTER_CONFIG) as FilterKey[]).map(k => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-all ${
                filter === k
                  ? "bg-white/10 text-white"
                  : "text-white/30 hover:text-white/50 hover:bg-white/[0.04]"
              }`}
            >
              {FILTER_CONFIG[k].label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5 min-h-0"
      >
        {filtered.length === 0 && (
          <div className="flex items-center justify-center h-full text-white/20 text-xs">
            En attente des discussions inter-agents...
          </div>
        )}
        {filtered.map((msg, i) => {
          const borderColor = ROLE_COLORS[msg.role] || "#64748b";
          const badge = EVENT_BADGES[msg.eventType];

          return (
            <div
              key={msg.id}
              className="flex gap-3 py-2 px-2 rounded-lg hover:bg-white/[0.02] transition-colors animate-fade-up"
              style={{ animationDelay: `${Math.min(i * 20, 200)}ms`, borderLeft: `3px solid ${borderColor}30` }}
            >
              {/* Avatar */}
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0 mt-0.5"
                style={{ backgroundColor: `${borderColor}15` }}
              >
                {msg.speakerEmoji}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-semibold" style={{ color: borderColor }}>
                    {msg.speaker}
                  </span>
                  {msg.target && (
                    <>
                      <span className="text-[10px] text-white/20">→</span>
                      <span className="text-[10px] text-white/40">{msg.target}</span>
                    </>
                  )}
                  {badge && (
                    <span
                      className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase"
                      style={{ color: badge.color, backgroundColor: `${badge.color}15` }}
                    >
                      {badge.label}
                    </span>
                  )}
                  <span className="text-[10px] text-white/20 tabular-nums ml-auto flex-shrink-0">
                    {new Date(msg.timestamp).toLocaleTimeString("en-GB")}
                  </span>
                </div>
                <p className="text-xs text-white/60 leading-relaxed">{msg.content}</p>
                {msg.elapsed_ms > 0 && (
                  <span className="text-[10px] text-white/20 mt-0.5 inline-block">
                    {msg.elapsed_ms >= 1000 ? `${(msg.elapsed_ms / 1000).toFixed(1)}s` : `${msg.elapsed_ms.toFixed(0)}ms`}
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {isStreaming && <TypingIndicator name="Agent is deliberating" color="#a78bfa" />}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Scroll-to-bottom */}
      {!autoScroll && messages.length > 0 && (
        <button
          onClick={() => {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
            setAutoScroll(true);
          }}
          className="absolute bottom-14 right-4 bg-white/10 hover:bg-white/20 text-white/60 text-[10px] px-3 py-1 rounded-full transition-all backdrop-blur-sm"
        >
          ↓ New messages
        </button>
      )}
    </div>
  );
}
