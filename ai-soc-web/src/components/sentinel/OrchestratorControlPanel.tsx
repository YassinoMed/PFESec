"use client";

import { Pause, RotateCcw, RefreshCw } from "lucide-react";

export interface OrchestratorState {
  status: "ORCHESTRATING" | "PAUSED" | "IDLE";
  classification: string;
  confidence: number;
  progress: number;
}

export function OrchestratorControlPanel({
  state,
  onPause,
  onRestart,
  query = "",
  onQueryChange = () => {},
}: {
  state: OrchestratorState;
  onPause: () => void;
  onRestart: () => void;
  query?: string;
  onQueryChange?: (val: string) => void;
}) {
  const isCritical = state.confidence >= 80;

  return (
    <section className="stitch-glass-panel stitch-animate-in stitch-delay-100 relative z-10 flex max-w-sm flex-1 flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="stitch-panel-header flex items-center justify-between"
      >
        <h2 className="sentinel-headline flex items-center gap-2">
          <span style={{ color: "var(--stitch-primary)" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M3 3v18h18M7 14l3-3 4 4 5-6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          Orchestrator Control
        </h2>
        <span
          className="stitch-pulse-dot h-3 w-3 rounded-full"
          style={{ backgroundColor: "var(--stitch-primary)" }}
        />
      </div>

      {/* Body */}
      <div className="stitch-panel-body sentinel-scroll flex flex-1 flex-col gap-4 overflow-y-auto">
        {/* INPUT CARD */}
        <div
          className="rounded-lg border p-4"
          style={{
            backgroundColor: "rgba(30, 30, 42, 0.4)",
            borderColor: "rgba(0, 209, 255, 0.2)",
          }}
        >
          <div
            className="sentinel-caps mb-2 text-xs"
            style={{ color: "var(--stitch-primary)" }}
          >
            Threat Event Query
          </div>
          <textarea
            className="w-full bg-neutral-950 border rounded p-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono resize-none h-20"
            style={{
              borderColor: "rgba(255, 255, 255, 0.1)",
              backgroundColor: "rgba(0, 0, 0, 0.3)",
            }}
            placeholder="Saisir la menace à analyser..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            disabled={state.status === "ORCHESTRATING"}
          />
        </div>

        {/* CURRENT STATUS */}
        <div
          className="rounded-lg border p-4"
          style={{
            backgroundColor: "rgba(56, 56, 67, 0.4)",
            borderColor: "rgba(60, 73, 78, 0.5)",
          }}
        >
          <div
            className="sentinel-caps mb-1"
            style={{ color: "var(--stitch-on-surface-variant)" }}
          >
            Current Status
          </div>
          <div
            className="sentinel-mono flex items-center gap-2"
            style={{ color: "var(--stitch-primary)" }}
          >
            <RefreshCw
              size={16}
              className={state.status === "ORCHESTRATING" ? "animate-spin" : ""}
            />
            {state.status}
          </div>
        </div>

        {/* CLASSIFICATION — glow critical quand menace élevée */}
        <div
          className={`rounded-lg border p-4 ${
            isCritical ? "stitch-glow-critical" : ""
          }`}
          style={{
            backgroundColor: "rgba(147, 0, 10, 0.2)",
            borderColor: "rgba(255, 180, 171, 0.3)",
          }}
        >
          <div
            className="sentinel-caps mb-1"
            style={{ color: "var(--stitch-on-surface-variant)" }}
          >
            Classification
          </div>
          <div
            className="text-base font-semibold"
            style={{
              color: isCritical ? "var(--stitch-error)" : "var(--stitch-on-surface)",
              fontSize: "16px",
              lineHeight: "1.6",
            }}
          >
            {state.classification}
          </div>
          <div
            className="mt-1"
            style={{
              color: "var(--stitch-on-surface-variant)",
              fontSize: "12px",
            }}
          >
            Confidence Score: {state.confidence}%
          </div>
        </div>

        {/* ANALYSIS PROGRESS — gradient violet→cyan avec glow */}
        <div className="mt-4">
          <div className="sentinel-caps mb-2 flex justify-between">
            <span style={{ color: "var(--stitch-on-surface-variant)" }}>
              Analysis Progress
            </span>
            <span style={{ color: "var(--stitch-primary)" }}>
              {state.progress}%
            </span>
          </div>
          <div
            className="h-2 w-full overflow-hidden rounded-full border"
            style={{
              backgroundColor: "var(--stitch-container-highest)",
              borderColor: "rgba(60, 73, 78, 0.2)",
            }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${state.progress}%`,
                background:
                  "linear-gradient(90deg, var(--stitch-secondary), var(--stitch-primary))",
                boxShadow: "0 0 10px rgba(0,209,255,0.5)",
              }}
            />
          </div>
        </div>

        {/* Boutons de contrôle */}
        <div className="mt-auto grid grid-cols-2 gap-2 pt-4">
          <ControlButton
            icon={<Pause size={16} />}
            label="Pause"
            onClick={onPause}
          />
          <ControlButton
            icon={<RotateCcw size={16} />}
            label="Restart"
            onClick={onRestart}
          />
        </div>
      </div>
    </section>
  );
}

function ControlButton({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="sentinel-caps flex items-center justify-center gap-1 rounded border px-3 py-2 transition-colors"
      style={{
        backgroundColor: "rgba(51, 52, 62, 0.6)",
        borderColor: "rgba(60, 73, 78, 0.5)",
        color: "var(--stitch-on-surface)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "rgba(56, 56, 67, 0.8)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "rgba(51, 52, 62, 0.6)";
      }}
    >
      {icon}
      {label}
    </button>
  );
}
