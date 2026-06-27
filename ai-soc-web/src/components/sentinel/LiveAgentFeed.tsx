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

/** Extrait le nom du speaker sans l'emoji */
const speakerName = (raw: string): string => {
  return raw.replace(/^[\p{Emoji}\s]+/u, "").trim() || raw;
};

/** Extrait l'emoji (premier caractère si emoji, sinon premier char) */
const speakerEmoji = (raw: string): string => {
  const match = raw.match(/^(\p{Emoji})/u);
  return match ? match[1] : raw.charAt(0);
};

export function LiveAgentFeed({
  messages,
  typing,
}: {
  messages: ConsoleMessage[];
  typing?: string | null;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, typing]);

  return (
    <section className="stitch-glass-panel stitch-animate-in stitch-delay-200 relative z-10 flex flex-[2] flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="stitch-panel-header flex items-center justify-between relative z-10"
      >
        <h2 className="sentinel-headline flex items-center gap-2">
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

      {/* Messages — font-code-sm (12px mono) comme le design */}
      <div
        ref={scrollRef}
        className="stitch-panel-body sentinel-scroll relative z-10 flex flex-1 flex-col gap-4 overflow-y-auto"
        style={{ fontFamily: "var(--font-fira), 'JetBrains Mono', ui-monospace, monospace", fontSize: "12px", lineHeight: "1.4" }}
      >
        {messages.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <span
              className="stitch-pulse-dot"
              style={{
                color: "var(--stitch-on-surface-variant)",
                fontSize: "12px",
              }}
            >
              ◌ Waiting for incident submission...
            </span>
            <span
              className="mt-1"
              style={{
                color: "var(--stitch-on-surface-variant)",
                fontSize: "10px",
                opacity: 0.6,
              }}
            >
              Submit an incident to see the council deliberate live.
            </span>
          </div>
        )}

        {messages.map((msg, i) => {
          const emoji = speakerEmoji(msg.speaker);
          const name = speakerName(msg.speaker);
          const color = speakerColor[emoji] ?? "var(--stitch-on-surface)";
          const border = speakerBorder[emoji] ?? "rgba(133, 147, 153, 0.3)";
          return (
            <div key={i} className="stitch-fade-in flex gap-3">
              {/* Avatar avec backdrop-blur-sm */}
              <div
                className="stitch-glass-micro flex h-8 w-8 shrink-0 items-center justify-center rounded border"
                style={{
                  backgroundColor: "rgba(51, 52, 62, 0.8)",
                  borderColor: border,
                }}
              >
                <span style={{ fontSize: "16px" }}>{emoji}</span>
              </div>

              {/* Bulle avec backdrop-blur-md */}
              <div
                className="stitch-glass-micro max-w-[85%] rounded-r-lg rounded-bl-lg border p-3"
                style={{
                  backgroundColor: "rgba(51, 52, 62, 0.5)",
                  borderColor: "rgba(60, 73, 78, 0.2)",
                }}
              >
                <div className="mb-1 flex items-center gap-2">
                  <span
                    className="sentinel-mono"
                    style={{
                      color,
                      fontWeight: 700,
                      fontSize: "14px",
                    }}
                  >
                    {name}
                  </span>
                  <span
                    style={{
                      color: "var(--stitch-on-surface-variant)",
                      fontSize: "10px",
                    }}
                  >
                    {msg.time}
                  </span>
                </div>
                <div style={{ color: "var(--stitch-on-surface)" }}>
                  {msg.content}
                </div>
              </div>
            </div>
          );
        })}

        {/* Typing indicator — bulle avec dots animés (exact du design) */}
        {typing && (
          <div className="stitch-fade-in flex gap-3 mt-2">
            <div
              className="stitch-glass-micro flex h-8 w-8 shrink-0 items-center justify-center rounded border"
              style={{
                backgroundColor: "rgba(51, 52, 62, 0.8)",
                borderColor: "rgba(60, 73, 78, 0.3)",
              }}
            >
              <span
                className="stitch-pulse-dot"
                style={{ color: "var(--stitch-tertiary)", fontSize: "16px" }}
              >
                ⋮
              </span>
            </div>
            <div
              className="stitch-glass-micro flex items-center gap-2 rounded-r-lg rounded-bl-lg border px-3 py-1.5"
              style={{
                backgroundColor: "rgba(51, 52, 62, 0.3)",
                borderColor: "rgba(60, 73, 78, 0.1)",
                color: "var(--stitch-on-surface-variant)",
                fontSize: "12px",
                fontStyle: "italic",
              }}
            >
              {typing} is analyzing
              <span className="stitch-typing-dots">
                <span className="stitch-typing-dot" />
                <span className="stitch-typing-dot" />
                <span className="stitch-typing-dot" />
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
