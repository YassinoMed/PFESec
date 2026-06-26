"use client";

import { Card } from "@/components/ui/Card";
import { VerdictPill } from "@/components/ui/VerdictPill";
import { ThreatBar } from "@/components/ui/ThreatBar";
import { ModelBadge } from "@/components/ui/ModelBadge";
import type { PredictResponse } from "@/types/api";
import { cn } from "@/lib/utils";
import { Clock } from "lucide-react";

interface ResultCardProps {
  result: PredictResponse;
  index?: number;
}

/** Carte de résultat d'inférence pour un modèle. */
export function ResultCard({ result, index = 0 }: ResultCardProps) {
  // Variante d'erreur
  if ("error" in result) {
    return (
      <Card className="animate-fade-up border-block/30" style={{ animationDelay: `${index * 60}ms` }}>
        <div className="flex items-center justify-between">
          <span className="font-display text-sm font-semibold text-[#f0f4ff]">
            {result.model_id ?? "Modèle"}
          </span>
          <VerdictPill verdict="ERROR" />
        </div>
        <p className="mt-2 rounded-lg bg-block/10 p-2 font-mono text-xs text-block">
          {result.error}
        </p>
      </Card>
    );
  }

  const isClassif = result.type === "classification";
  const probs = isClassif
    ? Object.entries(result.probabilities).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <Card
      className="animate-fade-up"
      hover
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* En-tête : icône + nom + badge type */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden>
            {result.icon}
          </span>
          <span className="font-display text-sm font-semibold leading-tight text-[#f0f4ff]">
            {result.model_name}
          </span>
        </div>
        <ModelBadge type={result.model_type} />
      </div>

      {/* Verdict */}
      <div className="mb-3">
        <VerdictPill verdict={result.verdict} size="sm" />
      </div>

      {/* Threat score */}
      <ThreatBar score={result.threat_score} className="mb-3" />

      {/* Contenu selon le type */}
      {isClassif ? (
        <div className="space-y-1.5">
          <p className="mb-1 text-[11px] uppercase tracking-wider text-tertiary">
            Distribution des probabilités
          </p>
          {probs.map(([label, p]) => (
            <div key={label} className="flex items-center gap-2">
              <span className="w-28 shrink-0 truncate text-[11px] text-secondary">
                {label}
              </span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className={cn(
                    "h-full rounded-full",
                    p > 0.5 ? "bg-primary" : "bg-white/20"
                  )}
                  style={{ width: `${p * 100}%` }}
                />
              </div>
              <span className="w-10 shrink-0 text-right font-mono text-[11px] tabular-nums text-secondary">
                {(p * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <p className="mb-1 text-[11px] uppercase tracking-wider text-tertiary">
            Réponse générée
          </p>
          <pre className="max-h-32 overflow-auto rounded-lg border border-white/5 bg-black/40 p-2.5 font-mono text-[11px] leading-relaxed text-info whitespace-pre-wrap">
            {result.prediction}
          </pre>
        </div>
      )}

      {/* Footer : latence */}
      <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-tertiary">
        <span className="uppercase tracking-wider">
          {isClassif ? "Classification" : "Génératif"}
        </span>
        <span className="flex items-center gap-1 font-mono">
          <Clock size={11} /> {result.elapsed_s}s
        </span>
      </div>
    </Card>
  );
}
