"use client";

import { useState, useEffect } from "react";
import { useModels, useGpuStatus } from "@/hooks/useApi";
import { registryApi, FleetSummary } from "@/lib/registryApi";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { RadialGauge } from "@/components/ui/RadialGauge";
import { ModelBadge } from "@/components/ui/ModelBadge";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ShieldCheck,
  Boxes,
  Crosshair,
  Cpu,
  CircleDot,
  ArrowRight,
  Activity,
  Layers,
  Brain,
} from "lucide-react";
import Link from "next/link";

export default function CommandCenterPage() {
  const models = useModels();
  const gpu = useGpuStatus();
  const [fleetSummary, setFleetSummary] = useState<FleetSummary | null>(null);

  useEffect(() => {
    registryApi.getSummary().then(setFleetSummary).catch(() => {});
  }, []);

  const modelList = models.data?.models ?? [];
  const loaded = modelList.filter((m) => m.loaded).length;
  const phishing = modelList.filter((m) => m.task === "phishing").length;
  const soc = modelList.filter((m) => m.task === "soc").length;

  const gpuDevice = gpu.data?.available ? gpu.data.devices[0] : undefined;

  return (
    <div>
      <DemoBanner demo={models.demo || gpu.demo} />

      <PageHeader
        icon={<LayoutDashboard size={22} />}
        title="SOC Command Center"
        description="Vue temps réel de l'orchestration multi-modèles et de l'infrastructure GPU."
      />

      {/* KPIs */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-3">
        <StatCard
          label="Détection phishing"
          value={phishing}
          icon={<Crosshair size={16} />}
          tone="info"
          sub="modèles dédiés"
        />
        <StatCard
          label="Analyse SOC"
          value={soc}
          icon={<Activity size={16} />}
          tone="accept"
          sub="règles & alertes"
        />
        <StatCard
          label="Utilisation GPU"
          value={gpuDevice ? `${gpuDevice.utilization_pct.toFixed(0)}%` : "—"}
          icon={<Cpu size={16} />}
          tone={gpuDevice && gpuDevice.utilization_pct > 85 ? "warn" : "neutral"}
          sub={gpuDevice?.name ?? "Aucun GPU"}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* Colonne gauche */}
        <div className="space-y-4 lg:col-span-2">
          {/* Accès rapide aux modules */}
          <div className="grid gap-3 sm:grid-cols-2">
            <QuickLink
              href="/analyze"
              icon={<Crosshair size={18} />}
              title="Threat Analysis"
              desc="Analyse multi-modèles avec consensus"
            />
            <QuickLink
              href="/batch"
              icon={<Boxes size={18} />}
              title="Batch Evaluation"
              desc="Tests & métriques (precision, recall, F1)"
            />
          </div>
        </div>

        {/* Colonne droite : GPU + santé système */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Observabilité GPU"
              subtitle={gpuDevice?.name ?? "Aucun GPU détecté"}
              icon={<Cpu size={18} />}
            />
            {gpuDevice ? (
              <div className="flex flex-col items-center gap-4 py-2">
                <RadialGauge
                  value={gpuDevice.utilization_pct}
                  label="Utilisation"
                  sublabel="compute"
                  tone={
                    gpuDevice.utilization_pct > 85
                      ? "warn"
                      : "primary"
                  }
                  size={140}
                />
                <div className="w-full space-y-2">
                  <GpuLine
                    label="VRAM allouée"
                    value={`${gpuDevice.allocated_gb} / ${gpuDevice.total_gb} Go`}
                    pct={(gpuDevice.allocated_gb / gpuDevice.total_gb) * 100}
                  />
                  <GpuLine
                    label="VRAM réservée"
                    value={`${gpuDevice.reserved_gb} Go`}
                    pct={(gpuDevice.reserved_gb / gpuDevice.total_gb) * 100}
                  />
                  <GpuLine
                    label="VRAM libre"
                    value={`${gpuDevice.free_gb} Go`}
                    pct={(gpuDevice.free_gb / gpuDevice.total_gb) * 100}
                    tone="accept"
                  />
                </div>
              </div>
            ) : (
              <p className="py-6 text-center text-sm text-tertiary">
                GPU non disponible
              </p>
            )}
          </Card>

          <Card>
            <CardHeader
              title="Santé système"
              icon={<ShieldCheck size={18} />}
            />
            <div className="space-y-2.5">
              <HealthRow label="Backend inference" ok={!models.demo} />
              <HealthRow label="Modèles chargés" ok={loaded > 0} value={`${loaded}`} />
              <HealthRow
                label="CUDA"
                ok={gpu.data?.available ? !!gpu.data.cuda_version : false}
                value={gpu.data?.available ? gpu.data.cuda_version ?? "—" : "—"}
              />
              <HealthRow label="Télémétrie live" ok={!gpu.demo} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function QuickLink({
  href,
  icon,
  title,
  desc,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <Link href={href} className="group">
      <Card hover className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-primary/25 bg-primary/10 text-primary">
          {icon}
        </div>
        <div className="flex-1">
          <h4 className="font-display text-sm font-semibold text-[#f0f4ff]">
            {title}
          </h4>
          <p className="text-[11px] text-secondary">{desc}</p>
        </div>
        <ArrowRight
          size={16}
          className="text-tertiary transition-transform group-hover:translate-x-1 group-hover:text-primary"
        />
      </Card>
    </Link>
  );
}

function GpuLine({
  label,
  value,
  pct,
  tone = "primary",
}: {
  label: string;
  value: string;
  pct: number;
  tone?: "primary" | "accept";
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-[11px]">
        <span className="text-secondary">{label}</span>
        <span className="font-mono tabular-nums text-secondary">{value}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
        <div
          className={cn(
            "h-full rounded-full",
            tone === "accept" ? "bg-accept" : "bg-primary"
          )}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
    </div>
  );
}

function HealthRow({
  label,
  ok,
  value,
}: {
  label: string;
  ok: boolean;
  value?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-secondary">{label}</span>
      <span className="flex items-center gap-1.5">
        {value && <span className="font-mono text-xs text-secondary">{value}</span>}
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            ok ? "bg-accept" : "bg-tertiary"
          )}
          style={ok ? { animation: "pulse 2.5s infinite", boxShadow: "0 0 8px hsl(142 72% 46%)" } : undefined}
        />
      </span>
    </div>
  );
}
