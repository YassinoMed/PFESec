"use client";

import { useModels, useGpuStatus } from "@/hooks/useApi";
import { cn } from "@/lib/utils";
import { Activity, Cpu, AlertTriangle, Wifi, WifiOff } from "lucide-react";

export function Topbar() {
  const models = useModels();
  const gpu = useGpuStatus();

  // En mode démo, l'état backend est "simulé vert" pour ne pas effrayer,
  // mais on garde le bandeau d'info (plus bas dans les pages).
  const demo = models.demo || gpu.demo;
  const loadedCount = gpu.data && gpu.data.available
    ? gpu.data.loaded_models.length
    : models.data?.models.filter((m) => m.loaded).length ?? 0;

  const gpuPct = gpu.data && gpu.data.available
    ? gpu.data.devices[0]?.utilization_pct
    : undefined;

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-white/[0.06] bg-base-900/70 px-6 py-3 backdrop-blur-xl lg:px-8">
      {/* Statut connexion backend */}
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "flex h-2 w-2 rounded-full",
            demo ? "bg-warn" : "bg-accept"
          )}
          style={{ animation: "pulse 2.5s infinite" }}
        />
        <span className="text-xs font-medium text-secondary">
          {demo ? "Mode démo" : "Backend connecté"}
        </span>
        {demo ? (
          <WifiOff size={13} className="text-warn" />
        ) : (
          <Wifi size={13} className="text-accept" />
        )}
      </div>

      {/* Indicateurs compacts */}
      <div className="flex items-center gap-2">
        <Pill icon={<Activity size={13} />} label={`${loadedCount} modèles en VRAM`} />
        {gpuPct !== undefined && (
          <Pill
            icon={<Cpu size={13} />}
            label={`GPU ${gpuPct.toFixed(0)}%`}
            tone={gpuPct > 85 ? "warn" : "primary"}
          />
        )}
        {demo && (
          <Pill
            icon={<AlertTriangle size={13} />}
            label="Données simulées"
            tone="warn"
          />
        )}
      </div>
    </header>
  );
}

function Pill({
  icon,
  label,
  tone = "neutral",
}: {
  icon: React.ReactNode;
  label: string;
  tone?: "neutral" | "primary" | "warn";
}) {
  return (
    <span
      className={cn(
        "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium sm:inline-flex",
        tone === "primary" && "border-primary/30 bg-primary/5 text-primary",
        tone === "warn" && "border-warn/30 bg-warn/5 text-warn",
        tone === "neutral" && "border-white/10 bg-white/[0.03] text-secondary"
      )}
    >
      {icon}
      {label}
    </span>
  );
}
