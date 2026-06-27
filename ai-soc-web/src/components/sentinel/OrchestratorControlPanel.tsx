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
}: {
  state: OrchestratorState;
  onPause: () => void;
  onRestart: () => void;
}) {
  const isCritical = state.confidence >= 80;

  return (
    <section className="stitch-glass-panel flex max-w-sm flex-1 flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="flex items-center justify-between border-b px-5 py-4"
        style={{
          backgroundColor: "rgba(40, 41, 51, 0.5)",
          borderColor: "rgba(60, 73, 78, 0.3)",
        }}
      >
        <h2 className="flex items-center gap-2 text-lg font-semibold">
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
      <div className="sentinel-scroll flex flex-1 flex-col gap-4 overflow-y-auto p-5">
        {/* Statut courant */}
        <div
          className="rounded-lg border p-4"
          style={{
            backgroundColor: "rgba(56, 56, 67, 0.5)",
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
            className="sentinel-mono flex items-center gap-2 text-sm font-medium"
            style={{ color: "var(--stitch-primary)" }}
          >
            <RefreshCw size={16} className={state.status === "ORCHESTRATING" ? "animate-spin" : ""} />
            {state.status}
          </div>
        </div>

        {/* Classification de la menace */}
        <div
          className={`rounded-lg border p-4 ${
            isCritical ? "stitch-glow-critical" : ""
          }`}
          style={{
            backgroundColor: "rgba(147, 0, 10, 0.1)",
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
            style={{ color: "var(--stitch-error)" }}
          >
            {state.classification}
          </div>
          <div
            className="mt-1 text-xs"
            style={{ color: "var(--stitch-on-surface-variant)" }}
          >
            Confidence Score: {state.confidence}%
          </div>
        </div>

        {/* Barre de progression analyse */}
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
      className="sentinel-caps flex items-center justify-center gap-1 rounded border px-3 py-2 transition-colors hover:brightness-125"
      style={{
        backgroundColor: "var(--stitch-container-highest)",
        borderColor: "rgba(60, 73, 78, 0.5)",
        color: "var(--stitch-on-surface)",
      }}
    >
      {icon}
      {label}
    </button>
  );
}
