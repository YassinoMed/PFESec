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
    <section className="stitch-glass-panel flex h-[42%] flex-col overflow-hidden rounded-xl">
      {/* Onglets */}
      <div
        className="sentinel-caps flex border-b"
        style={{
          backgroundColor: "rgba(51, 52, 62, 0.8)",
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
                backgroundColor: isActive ? "rgba(56, 56, 67, 0.5)" : "transparent",
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Liste des preuves */}
      <div className="sentinel-scroll flex flex-col gap-2 overflow-y-auto p-5">
        {active.map((e, i) => (
          <div
            key={i}
            className="rounded p-2"
            style={{
              borderLeft: `2px solid ${toneColor[e.tone]}`,
              backgroundColor: "rgba(51, 52, 62, 0.3)",
            }}
          >
            <span className="sentinel-mono text-xs font-bold" style={{ color: toneColor[e.tone] }}>
              {e.source}:
            </span>{" "}
            <span
              className="sentinel-mono text-xs"
              style={{ color: "var(--stitch-on-surface)" }}
            >
              {e.text}
            </span>
          </div>
        ))}
        {active.length === 0 && (
          <div
            className="sentinel-mono py-6 text-center text-xs"
            style={{ color: "var(--stitch-on-surface-variant)" }}
          >
            Aucune preuve disponible pour cet onglet.
          </div>
        )}
      </div>
    </section>
  );
}
