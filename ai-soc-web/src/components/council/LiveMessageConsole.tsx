"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

export type MessageType =
  | "mission"
  | "validation"
  | "evidence"
  | "warning"
  | "consensus"
  | "recommendation"
  | "completed"
  | "waiting"
  | "retry"
  | "fallback";

export interface ConsoleMessage {
  time: string;
  speaker: string;
  type: MessageType;
  content: string;
}

interface LiveMessageConsoleProps {
  messages: ConsoleMessage[];
}

const getBadgeStyle = (type: MessageType) => {
  switch (type) {
    case "mission":
      return "bg-blue-600/20 text-blue-400 border-blue-600/30";
    case "validation":
      return "bg-purple-600/20 text-purple-400 border-purple-600/30";
    case "evidence":
      return "bg-emerald-600/20 text-emerald-400 border-emerald-600/30";
    case "warning":
      return "bg-amber-600/20 text-amber-400 border-amber-600/30 animate-pulse";
    case "consensus":
      return "bg-indigo-600/20 text-indigo-400 border-indigo-600/30";
    case "recommendation":
      return "bg-cyan-600/20 text-cyan-400 border-cyan-600/30";
    case "completed":
      return "bg-green-600/20 text-green-400 border-green-600/30";
    case "waiting":
      return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
    case "retry":
      return "bg-rose-600/20 text-rose-400 border-rose-600/30";
    case "fallback":
      return "bg-red-600/20 text-red-400 border-red-600/30";
    default:
      return "bg-neutral-600/20 text-neutral-400 border-neutral-600/30";
  }
};

export default function LiveMessageConsole({ messages }: LiveMessageConsoleProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col rounded-lg border border-white/5 bg-black/60 font-mono text-xs shadow-inner h-[340px]">
      {/* Console Header */}
      <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.02] px-4 py-2 text-tertiary text-[10px] select-none">
        <span>CONSOLE LIVE AI COUNCIL</span>
        <div className="flex gap-1.5">
          <span className="h-2 w-2 rounded-full bg-block/60" />
          <span className="h-2 w-2 rounded-full bg-warn/60" />
          <span className="h-2 w-2 rounded-full bg-accept/60 animate-pulse" />
        </div>
      </div>

      {/* Message List */}
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin select-text">
        {messages.map((msg, index) => (
          <div
            key={index}
            className="flex items-start gap-3 transition-opacity duration-300 animate-fade-in border-l-2 border-white/5 pl-2 hover:border-primary/30"
          >
            {/* Timestamp */}
            <span className="text-[10px] text-tertiary select-none tabular-nums shrink-0 pt-0.5">
              [{msg.time}]
            </span>

            {/* Badge Type */}
            <span
              className={cn(
                "rounded border px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-wider shrink-0 select-none",
                getBadgeStyle(msg.type)
              )}
            >
              {msg.type}
            </span>

            {/* Message Body */}
            <div className="min-w-0 flex-1">
              <span className="font-semibold text-[#f0f4ff] mr-1.5 select-none">{msg.speaker}:</span>
              <span className="text-secondary whitespace-pre-wrap break-words leading-relaxed select-text">
                {msg.content}
              </span>
            </div>
          </div>
        ))}

        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center text-tertiary select-none">
            <span className="animate-pulse">🟢 En attente de soumission...</span>
            <span className="text-[10px] mt-1 text-neutral-500">
              Soumettez un incident pour voir le conseil délibérer en direct.
            </span>
          </div>
        )}
      </div>

      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
