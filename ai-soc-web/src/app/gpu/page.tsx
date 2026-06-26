"use client";

import { useEffect, useRef, useState } from "react";
import { useGpuStatus } from "@/hooks/useApi";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { RadialGauge } from "@/components/ui/RadialGauge";
import { Cpu, MemoryStick, Zap, Thermometer } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface Sample {
  t: string;
  util: number;
  vram: number;
}

const MAX_SAMPLES = 30;

export default function GpuPage() {
  const gpu = useGpuStatus();
  const [history, setHistory] = useState<Sample[]>([]);
  const seed = useRef(63); // base pour le mode démo

  const device = gpu.data?.available ? gpu.data.devices[0] : undefined;

  // Accumule l'historique à chaque polling (time-series live).
  useEffect(() => {
    if (!device) return;
    const now = new Date();
    setHistory((h) => {
      // En mode démo on ajoute une légère dérive pour un graphe vivant.
      const util = gpu.demo
        ? Math.max(
            10,
            Math.min(95, seed.current + (Math.random() * 16 - 8))
          )
        : device.utilization_pct;
      if (gpu.demo) seed.current = util;
      const vram = gpu.demo
        ? 60 + Math.random() * 12
        : (device.allocated_gb / device.total_gb) * 100;
      return [
        ...h.slice(-MAX_SAMPLES + 1),
        {
          t: now.toLocaleTimeString("fr-FR", { hour12: false }),
          util: Math.round(util * 10) / 10,
          vram: Math.round(vram * 10) / 10,
        },
      ];
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gpu.data]);

  return (
    <div>
      <DemoBanner demo={gpu.demo} />

      <PageHeader
        icon={<Cpu size={22} />}
        title="GPU Observatory"
        description="Télémétrie matérielle en continu : compute, VRAM et charge historique."
      />

      {!device ? (
        <Card className="flex h-64 flex-col items-center justify-center text-center">
          <Cpu size={40} className="mb-3 text-tertiary" />
          <p className="text-sm text-secondary">
            Aucun GPU CUDA disponible sur le backend.
          </p>
        </Card>
      ) : (
        <>
          {/* KPIs */}
          <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard
              label="Compute"
              value={`${device.utilization_pct.toFixed(1)}%`}
              icon={<Zap size={16} />}
              tone={device.utilization_pct > 85 ? "warn" : "primary"}
            />
            <StatCard
              label="VRAM allouée"
              value={`${device.allocated_gb.toFixed(2)} Go`}
              icon={<MemoryStick size={16} />}
              tone="info"
              sub={`/${device.total_gb.toFixed(1)} Go`}
            />
            <StatCard
              label="VRAM libre"
              value={`${device.free_gb.toFixed(2)} Go`}
              icon={<MemoryStick size={16} />}
              tone="accept"
            />
            <StatCard
              label="Modèles chargés"
              value={gpu.data?.available ? gpu.data.loaded_models.length : 0}
              icon={<Cpu size={16} />}
              tone="neutral"
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {/* Gauges */}
            <Card className="lg:col-span-1">
              <CardHeader title="Instantané" subtitle={device.name} icon={<Cpu size={18} />} />
              <div className="flex flex-col items-center gap-6 py-4">
                <RadialGauge
                  value={device.utilization_pct}
                  label="Compute GPU"
                  sublabel="SM activity"
                  tone={device.utilization_pct > 85 ? "warn" : "primary"}
                  size={150}
                />
                <RadialGauge
                  value={(device.reserved_gb / device.total_gb) * 100}
                  label="VRAM réservée"
                  sublabel="PyTorch cache"
                  tone="accept"
                  size={130}
                />
              </div>
            </Card>

            {/* Time-series */}
            <Card className="lg:col-span-2">
              <CardHeader
                title="Charge historique"
                subtitle={`${history.length} échantillons · polling 5s`}
                icon={<Thermometer size={18} />}
              />
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={history} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                  <defs>
                    <linearGradient id="utilGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(220, 95%, 62%)" stopOpacity={0.6} />
                      <stop offset="100%" stopColor="hsl(220, 95%, 62%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="vramGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(142, 72%, 46%)" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="hsl(142, 72%, 46%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="t" tick={{ fill: "#94a3b8", fontSize: 10 }} minTickGap={40} />
                  <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 10 }} unit="%" />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1424",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="util"
                    name="Compute %"
                    stroke="hsl(220, 95%, 62%)"
                    strokeWidth={2}
                    fill="url(#utilGrad)"
                  />
                  <Area
                    type="monotone"
                    dataKey="vram"
                    name="VRAM %"
                    stroke="hsl(142, 72%, 46%)"
                    strokeWidth={2}
                    fill="url(#vramGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>

              <div className="mt-4 flex flex-wrap gap-2">
                {gpu.data?.available &&
                  gpu.data.loaded_models.map((m) => (
                    <span
                      key={m}
                      className="rounded-full border border-primary/30 bg-primary/5 px-3 py-1 font-mono text-[11px] text-primary"
                    >
                      {m}
                    </span>
                  ))}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
