"use client";

import { useState } from "react";

export interface Evidence {
  source: string;
  text: string;
  tone: "tertiary" | "secondary" | "primary" | "error";
}

type Tab = "rag" | "ioc" | "mitre";

const toneColor: Record<Evidence["tone"], string> = {
  tertiary: "var(--stitch-tertiary)",
  secondary: "var(--stitch-secondary)",
  primary: "var(--stitch-primary)",
  error: "var(--stitch-error)",
};

export function EvidenceRagPanel({
  rag,
  ioc,
  mitre,
}: {
  rag: Evidence[];
  ioc: Evidence[];
  mitre: Evidence[];
}) {
  const [tab, setTab] = useState<Tab>("rag");
  const tabs: { id: Tab; label: string }[] = [
    { id: "rag", label: "RAG Sources" },
    { id: "ioc", label: "IOC Extract" },
    { id: "mitre", label: "MITRE Map" },
  ];
  const active = tab === "rag" ? rag : tab === "ioc" ? ioc : mitre;

  return (
    <section className="stitch-glass-panel stitch-animate-in stitch-delay-300 flex flex-[1] flex-col overflow-hidden rounded-xl">
      {/* Onglets — bg-surface-container-highest/60 comme le design */}
      <div
        className="sentinel-caps flex border-b"
        style={{
          backgroundColor: "rgba(51, 52, 62, 0.6)",
          borderColor: "rgba(60, 73, 78, 0.3)",
        }}
      >
        {tabs.map((t) => {
          const isActive = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="cursor-pointer px-4 py-3 transition-colors"
              style={{
                color: isActive
                  ? "var(--stitch-tertiary)"
                  : "var(--stitch-on-surface-variant)",
                borderBottom: isActive
                  ? "2px solid var(--stitch-tertiary)"
                  : "2px solid transparent",
                backgroundColor: isActive ? "rgba(56, 56, 67, 0.4)" : "transparent",
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Liste des preuves — backdrop-blur-sm + font-code-sm comme le design */}
      <div
        className="stitch-panel-body sentinel-scroll flex flex-col gap-2 overflow-y-auto"
        style={{
          fontFamily: "var(--font-fira), 'JetBrains Mono', ui-monospace, monospace",
          fontSize: "12px",
          lineHeight: "1.4",
        }}
      >
        {active.map((e, i) => (
          <div
            key={i}
            className="stitch-glass-micro rounded p-2"
            style={{
              borderLeft: `2px solid ${toneColor[e.tone]}`,
              backgroundColor: "rgba(51, 52, 62, 0.3)",
            }}
          >
            <span className="font-bold" style={{ color: toneColor[e.tone] }}>
              {e.source}:
            </span>{" "}
            <span style={{ color: "var(--stitch-on-surface)" }}>
              {e.text}
            </span>
          </div>
        ))}
        {active.length === 0 && (
          <div
            className="py-6 text-center"
            style={{ color: "var(--stitch-on-surface-variant)" }}
          >
            No evidence available for this tab.
          </div>
        )}
      </div>
    </section>
  );
}
