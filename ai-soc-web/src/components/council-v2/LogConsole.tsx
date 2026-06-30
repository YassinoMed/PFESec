"use client";

import React, { useEffect, useRef, useState } from "react";
import type { CouncilEvent } from "@/types/council";

interface LogConsoleProps {
  events: CouncilEvent[];
}

type LogFilter = "all" | "info" | "warn" | "success" | "error";

interface LogLine {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "SUCCESS" | "ERROR";
  source: string;
  message: string;
}

export function LogConsole({ events }: LogConsoleProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<LogFilter>("all");

  const logLines = events.map((evt, idx): LogLine => {
    let level: LogLine["level"] = "INFO";
    if (evt.type === "error") level = "ERROR";
    else if (evt.type === "contradiction") level = "WARN";
    else if (evt.type === "master_completed" || evt.type === "consensus_final" || evt.type === "contradiction_resolved") {
      level = "SUCCESS";
    } else if (evt.type === "expert_query") {
      level = "WARN";
    }

    return {
      id: `log-${idx}-${evt.timestamp}`,
      timestamp: new Date(evt.timestamp).toLocaleTimeString("en-GB"),
      level,
      source: evt.source.toUpperCase(),
      message: evt.message,
    };
  });

  const filteredLines = logLines.filter(line => {
    if (filter === "all") return true;
    if (filter === "info") return line.level === "INFO";
    if (filter === "warn") return line.level === "WARN";
    if (filter === "success") return line.level === "SUCCESS";
    if (filter === "error") return line.level === "ERROR";
    return true;
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [filteredLines.length]);

  const getLevelColor = (level: LogLine["level"]) => {
    switch (level) {
      case "ERROR": return "text-red-400";
      case "WARN": return "text-amber-400";
      case "SUCCESS": return "text-green-400";
      default: return "text-cyan-400";
    }
  };

  return (
    <div className="glass rounded-xl p-4 flex flex-col h-full bg-[#050810]/60 border border-white/[0.04]">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
          <h3 className="text-xs font-mono font-bold tracking-widest text-white/50 uppercase">
            System Log Console
          </h3>
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-1 font-mono text-[9px]">
          {(["all", "info", "warn", "success", "error"] as LogFilter[]).map(btn => (
            <button
              key={btn}
              onClick={() => setFilter(btn)}
              className={`px-1.5 py-0.5 rounded border uppercase transition-all ${
                filter === btn
                  ? "bg-white/10 border-white/20 text-white font-bold"
                  : "bg-transparent border-transparent text-white/40 hover:text-white/60"
              }`}
            >
              {btn}
            </button>
          ))}
        </div>
      </div>

      {/* Terminal log lines */}
      <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-1 min-h-[140px] max-h-[300px]">
        {filteredLines.map(line => (
          <div key={line.id} className="flex items-start gap-2 hover:bg-white/[0.02] py-0.5 px-1 rounded">
            <span className="text-white/25 flex-shrink-0">[{line.timestamp}]</span>
            <span className={`font-bold flex-shrink-0 ${getLevelColor(line.level)}`}>
              [{line.level}]
            </span>
            <span className="text-white/40 flex-shrink-0">[{line.source}]</span>
            <span className="text-white/70 flex-1 leading-relaxed">{line.message}</span>
          </div>
        ))}
        {filteredLines.length === 0 && (
          <p className="text-white/20 text-center py-6 italic">No log items matching filter.</p>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
