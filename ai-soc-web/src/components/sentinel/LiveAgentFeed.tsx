"use client";

import { useEffect, useRef } from "react";
import type { ConsoleMessage } from "@/components/council/LiveMessageConsole";
import { Filter } from "lucide-react";

const speakerColor: Record<string, string> = {
  "🧠": "var(--stitch-primary)",
  "📧": "var(--stitch-tertiary)",
  "🛡": "var(--stitch-secondary)",
  "📡": "var(--stitch-success)",
  "🗺️": "var(--stitch-warning)",
};

const speakerBorder: Record<string, string> = {
  "🧠": "rgba(0, 209, 255, 0.3)",
  "📧": "rgba(150, 233, 255, 0.3)",
  "🛡": "rgba(208, 188, 255, 0.3)",
  "📡": "rgba(126, 240, 184, 0.3)",
  "🗺️": "rgba(255, 209, 102, 0.3)",
};

export function LiveAgentFeed({
  messages,
  typing,
}: {
  messages: ConsoleMessage[];
  typing?: string | null;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas à chaque nouveau message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, typing]);

  return (
    <section className="stitch-glass-panel relative z-10 flex flex-[2] flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="flex items-center justify-between border-b px-5 py-4"
        style={{
          backgroundColor: "rgba(40, 41, 51, 0.5)",
          borderColor: "rgba(60, 73, 78, 0.3)",
        }}
      >
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <span style={{ color: "var(--stitch-tertiary)" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M3 12c0-5 4-9 9-9s9 4 9 9-4 9-9 9-9-4-9-9z M12 8v4l3 2"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          Live Agent Feed
        </h2>
        <div
          className="sentinel-caps flex items-center gap-1"
          style={{ color: "var(--stitch-on-surface-variant)" }}
        >
          <Filter size={14} />
          Filter
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="sentinel-scroll flex flex-1 flex-col gap-4 overflow-y-auto p-5"
      >
        {messages.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <span
              className="stitch-pulse-dot text-sm"
              style={{ color: "var(--stitch-on-surface-variant)" }}
            >
              ◌ En attente d'un incident à analyser...
            </span>
          </div>
        )}

        {messages.map((msg, i) => {
          const speakerKey = msg.speaker.trim().charAt(0);
          const color = speakerColor[speakerKey] ?? "var(--stitch-on-surface)";
          const border = speakerBorder[speakerKey] ?? "rgba(133, 147, 153, 0.3)";
          return (
            <div key={i} className="stitch-fade-in flex gap-3">
              {/* Avatar emoji */}
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded border"
                style={{
                  backgroundColor: "var(--stitch-container-highest)",
                  borderColor: border,
                }}
              >
                <span className="text-base">{speakerKey}</span>
              </div>

              {/* Bulle */}
              <div
                className="max-w-[85%] rounded-r-lg rounded-bl-lg border p-3"
                style={{
                  backgroundColor: "rgba(51, 52, 62, 0.6)",
                  borderColor: "rgba(60, 73, 78, 0.2)",
                }}
              >
                <div className="mb-1 flex items-center gap-2">
                  <span
                    className="sentinel-mono text-xs font-bold"
                    style={{ color }}
                  >
                    {msg.speaker.replace(/^[^\sa-zA-Z]+/, "").trim() || msg.speaker}
                  </span>
                  <span
                    className="sentinel-mono text-[10px]"
                    style={{ color: "var(--stitch-on-surface-variant)" }}
                  >
                    {msg.time}
                  </span>
                </div>
                <div
                  className="text-xs leading-relaxed"
                  style={{ color: "var(--stitch-on-surface)" }}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          );
        })}

        {/* Indicateur de saisie */}
        {typing && (
          <div className="stitch-fade-in flex gap-3">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded border"
              style={{
                backgroundColor: "var(--stitch-container-highest)",
                borderColor: "rgba(60, 73, 78, 0.3)",
              }}
            >
              <span
                className="stitch-pulse-dot"
                style={{ color: "var(--stitch-on-surface-variant)" }}
              >
                •••
              </span>
            </div>
            <div
              className="text-xs italic"
              style={{ color: "var(--stitch-on-surface-variant)" }}
            >
              {typing} is analyzing...
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
