"use client";

import { Shield, BellRing, Settings, Power } from "lucide-react";

interface SentinelHeaderProps {
  session: string;
  risk: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  consensus: number;
  agents: number;
}

const riskColor: Record<SentinelHeaderProps["risk"], string> = {
  CRITICAL: "var(--stitch-error)",
  HIGH: "var(--stitch-warning)",
  MEDIUM: "var(--stitch-tertiary)",
  LOW: "var(--stitch-success)",
};

export function SentinelHeader({
  session,
  risk,
  consensus,
  agents,
}: SentinelHeaderProps) {
  return (
    <header
      className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b px-5"
      style={{
        backgroundColor: "rgba(26, 27, 36, 0.8)",
        backdropFilter: "blur(12px)",
        borderColor: "rgba(0, 209, 255, 0.2)",
        boxShadow: "0 0 15px rgba(0,209,255,0.15)",
      }}
    >
      {/* Brand + indicateurs globaux */}
      <div className="flex items-center gap-6">
        <h1
          className="sentinel-caps text-lg"
          style={{ color: "var(--stitch-primary)", letterSpacing: "-0.01em" }}
        >
          ◈ SENTINEL COMMAND
        </h1>

        <div className="hidden h-8 items-center gap-4 border-l pl-6 md:flex"
          style={{ borderColor: "rgba(60, 73, 78, 0.4)" }}
        >
          <Indicator label="Session" value={session} mono />
          <Indicator
            label="Risk"
            value={risk}
            mono
            valueColor={riskColor[risk]}
            chip
          />
          <Indicator label="Consensus" value={`${consensus}%`} mono valueColor="var(--stitch-primary)" />
          <Indicator
            label="Agents"
            value={`${agents} ACTIVE`}
            mono
            valueColor="var(--stitch-tertiary)"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3" style={{ color: "var(--stitch-primary)" }}>
          <Shield size={18} className="cursor-pointer transition-colors hover:opacity-70" />
          <BellRing size={18} className="cursor-pointer transition-colors hover:opacity-70" />
          <Settings size={18} className="cursor-pointer transition-colors hover:opacity-70" />
        </div>
        <button
          className="sentinel-caps flex items-center gap-2 rounded px-4 py-2 transition-all hover:brightness-110"
          style={{
            color: "#690005",
            backgroundColor: "rgba(255, 180, 171, 0.9)",
            boxShadow: "0 0 10px rgba(255,180,171,0.2)",
          }}
        >
          <Power size={14} />
          TERMINATE SESSION
        </button>
      </div>
    </header>
  );
}

function Indicator({
  label,
  value,
  mono,
  chip,
  valueColor,
}: {
  label: string;
  value: string;
  mono?: boolean;
  chip?: boolean;
  valueColor?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="sentinel-caps"
        style={{ color: "var(--stitch-on-surface-variant)" }}
      >
        {label}
      </span>
      {chip ? (
        <span
          className="sentinel-caps rounded px-2 py-1"
          style={{
            color: valueColor,
            backgroundColor: "rgba(147, 0, 10, 0.2)",
          }}
        >
          {value}
        </span>
      ) : (
        <span
          className={mono ? "sentinel-mono text-sm font-medium" : "text-sm font-semibold"}
          style={{ color: valueColor ?? "var(--stitch-on-surface)" }}
        >
          {value}
        </span>
      )}
    </div>
  );
}
