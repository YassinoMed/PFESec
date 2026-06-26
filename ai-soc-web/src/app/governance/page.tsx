"use client";

import { useModels } from "@/hooks/useApi";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { ModelBadge } from "@/components/ui/ModelBadge";
import { cn } from "@/lib/utils";
import { Scale, ShieldCheck, Clock, Target, CircleDot } from "lucide-react";

export default function GovernancePage() {
  const models = useModels();
  const modelList = models.data?.models ?? [];

  const ready = modelList.filter((m) => m.status === "READY").length;
  const loaded = modelList.filter((m) => m.loaded).length;
  const types = new Set(modelList.map((m) => m.type)).size;

  return (
    <div>
      <DemoBanner demo={models.demo} />

      <PageHeader
        icon={<Scale size={22} />}
        title="AI Governance"
        description="Inventaire et comparatif des modèles pour la gouvernance et l'audit IA."
      />

      {/* KPIs */}
      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Modèles audités" value={modelList.length} icon={<Scale size={16} />} tone="primary" />
        <StatCard label="Opérationnels" value={`${ready}/${modelList.length}`} icon={<ShieldCheck size={16} />} tone="accept" />
        <StatCard label="En production (VRAM)" value={loaded} icon={<CircleDot size={16} />} tone="info" />
        <StatCard label="Familles d'architectures" value={types} icon={<Target size={16} />} tone="warn" sub="BERT · LoRA · LLM" />
      </div>

      {/* Tableau comparatif */}
      <Card>
        <CardHeader
          title="Inventaire des modèles"
          subtitle="État, type et rôle de chaque modèle de la flotte"
          icon={<Scale size={18} />}
        />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-tertiary">
                <th className="px-3 py-2.5 font-medium">Modèle</th>
                <th className="px-3 py-2.5 font-medium">Architecture</th>
                <th className="px-3 py-2.5 font-medium">Tâche</th>
                <th className="px-3 py-2.5 font-medium">Statut</th>
                <th className="px-3 py-2.5 font-medium">Production</th>
                <th className="px-3 py-2.5 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {modelList.map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-white/[0.04] transition-colors hover:bg-white/[0.02]"
                >
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{m.icon}</span>
                      <div>
                        <div className="font-display font-semibold text-[#f0f4ff]">
                          {m.name}
                        </div>
                        <div className="font-mono text-[10px] text-tertiary">
                          {m.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <ModelBadge type={m.type} />
                  </td>
                  <td className="px-3 py-3">
                    <span className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[11px] text-secondary">
                      {m.task}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 text-xs font-medium",
                        m.status === "READY" ? "text-accept" : "text-warn"
                      )}
                    >
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          m.status === "READY" ? "bg-accept" : "bg-warn"
                        )}
                      />
                      {m.status}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 text-xs",
                        m.loaded ? "text-primary" : "text-tertiary"
                      )}
                    >
                      <CircleDot size={12} />
                      {m.loaded ? "Chargé" : "Inactif"}
                    </span>
                  </td>
                  <td className="max-w-xs px-3 py-3 text-xs text-secondary">
                    {m.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Cartes de synthèse par famille */}
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {(["bert", "lora", "llm"] as const).map((type) => {
          const items = modelList.filter((m) => m.type === type);
          if (items.length === 0) return null;
          return (
            <Card key={type}>
              <CardHeader
                title={`${type.toUpperCase()} · ${items.length}`}
                subtitle={type === "bert" ? "Classifieurs spécialisés" : type === "lora" ? "Adaptateurs LoRA" : "Modèles génératifs"}
                icon={<Target size={16} />}
              />
              <ul className="space-y-2">
                {items.map((m) => (
                  <li key={m.id} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-secondary">
                      <span>{m.icon}</span>
                      {m.name}
                    </span>
                    <span className={cn("h-1.5 w-1.5 rounded-full", m.loaded ? "bg-accept" : "bg-tertiary")} />
                  </li>
                ))}
              </ul>
            </Card>
          );
        })}
      </div>

      <p className="mt-5 flex items-center gap-2 text-xs text-tertiary">
        <Clock size={12} />
        Les métriques de performance détaillées (precision/recall/F1) sont
        disponibles dans le module Batch Evaluation après exécution d'une suite
        de tests.
      </p>
    </div>
  );
}
