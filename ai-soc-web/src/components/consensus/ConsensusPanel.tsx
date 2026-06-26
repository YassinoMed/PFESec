"use client";

import { useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import {
  Brain,
  LoaderCircle,
  Play,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  BarChart3,
  Clock,
  Layers,
  Trophy,
} from "lucide-react";

interface ModelVote {
  model_id: string;
  model_name: string;
  category: string;
  confidence: number;
  weight: number;
  weighted_score: number;
  inference_ms: number;
  error?: string;
}

interface ConsensusResult {
  query: string;
  global_score: number;
  confidence_level: string;
  consensus_reached: boolean;
  warning?: string;
  final_response: unknown;
  primary_model: ModelVote | null;
  total_models_executed: number;
  total_retained: number;
  total_rejected: number;
  total_execution_ms: number;
  config: Record<string, unknown>;
  ranking: ModelVote[];
  retained: ModelVote[];
  rejected: ModelVote[];
  contributions: Record<string, number>;
  timestamp: string;
}

const confColor = (level: string) => {
  switch (level) {
    case "High": return "text-accept";
    case "Medium": return "text-warn";
    default: return "text-block";
  }
};

const confBg = (level: string) => {
  switch (level) {
    case "High": return "bg-accept/10 border-accept/30";
    case "Medium": return "bg-warn/10 border-warn/30";
    default: return "bg-block/10 border-block/30";
  }
};

export default function ConsensusPanel() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ConsensusResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runConsensus = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const url = `${process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || "http://localhost:8080"}/api/v1/security/consensus`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, models: [] }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader
          title="Consensus IA"
          subtitle="Moteur de consensus multi-modèles avec score pondéré"
          icon={<Brain size={18} />}
          action={
            <div className="flex items-center gap-2">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={1}
                placeholder="Entrez une requête de test..."
                className="w-64 resize-none rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-xs text-[#f0f4ff] placeholder:text-tertiary focus:border-primary/50 focus:outline-none"
              />
              <button
                onClick={runConsensus}
                disabled={loading || !query.trim()}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-white shadow-glow transition-all hover:bg-primary/90 disabled:opacity-40"
              >
                {loading ? <LoaderCircle size={14} className="animate-spin" /> : <Play size={14} />}
                Exécuter
              </button>
            </div>
          }
        />
      </Card>

      {error && (
        <Card className="border-block/30">
          <p className="flex items-center gap-2 text-sm text-block">
            <XCircle size={16} /> {error}
          </p>
        </Card>
      )}

      {loading && (
        <div className="flex h-32 items-center justify-center">
          <LoaderCircle size={28} className="animate-spin text-primary" />
          <span className="ml-3 text-sm text-secondary">Calcul du consensus multi-modèles…</span>
        </div>
      )}

      {result && <ConsensusDisplay result={result} />}
    </div>
  );
}

function ConsensusDisplay({ result }: { result: ConsensusResult }) {
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className={cn("border-2 lg:col-span-2", confBg(result.confidence_level))}>
          <div className="flex flex-col items-center py-4 text-center">
            <span className={cn("text-4xl font-bold tabular-nums", confColor(result.confidence_level))}>
              {result.global_score.toFixed(1)}%
            </span>
            <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-secondary">Score global pondéré</p>

            <div className="mt-3 h-2 w-full max-w-xs overflow-hidden rounded-full bg-white/5">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-1000",
                  result.confidence_level === "High" ? "bg-accept" :
                  result.confidence_level === "Medium" ? "bg-warn" : "bg-block"
                )}
                style={{ width: `${result.global_score}%` }}
              />
            </div>

            <div className="mt-4 flex items-center gap-4 text-xs">
              <span className={cn("flex items-center gap-1 font-semibold", confColor(result.confidence_level))}>
                <TrendingUp size={14} /> {result.confidence_level}
              </span>
              <span className="flex items-center gap-1 text-secondary">
                <CheckCircle2 size={14} className="text-accept" />
                {result.consensus_reached ? "Consensus atteint" : "Pas de consensus"}
              </span>
            </div>

            {result.warning && (
              <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-warn/10 px-3 py-1.5 text-xs text-warn">
                <AlertTriangle size={13} /> {result.warning}
              </p>
            )}
          </div>
        </Card>

        <Card>
          <div className="space-y-2.5">
            <MiniStat label="Modèles exécutés" value={result.total_models_executed} icon={<Layers size={13} />} />
            <MiniStat label="Retenus" value={result.total_retained} icon={<CheckCircle2 size={13} />} color="text-accept" />
            <MiniStat label="Rejetés" value={result.total_rejected} icon={<XCircle size={13} />} color="text-block" />
            <MiniStat label="Temps total" value={`${result.total_execution_ms.toFixed(0)} ms`} icon={<Clock size={13} />} />
            {result.primary_model && (
              <MiniStat label="Modèle principal" value={result.primary_model.model_name} icon={<Trophy size={13} />} color="text-warn" />
            )}
          </div>
        </Card>
      </div>

      {result.ranking.length > 0 && (
        <Card>
          <CardHeader title="Classement des modèles" subtitle="Trié par score décroissant" icon={<BarChart3 size={18} />} />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/5 text-tertiary">
                  <th className="p-2 font-medium">#</th>
                  <th className="p-2 font-medium">Modèle</th>
                  <th className="p-2 font-medium">Catégorie</th>
                  <th className="p-2 font-medium text-right">Score</th>
                  <th className="p-2 font-medium text-right">Poids</th>
                  <th className="p-2 font-medium text-right">Score pondéré</th>
                  <th className="p-2 font-medium text-right">Contribution</th>
                  <th className="p-2 font-medium text-right">Temps</th>
                </tr>
              </thead>
              <tbody>
                {result.ranking.map((v, i) => {
                  const contrib = result.contributions[v.model_id] ?? 0;
                  return (
                    <tr key={v.model_id} className={cn("border-b border-white/[0.03] transition-colors hover:bg-white/[0.02]",
                      i === 0 && "bg-primary/[0.04]"
                    )}>
                      <td className="p-2 font-mono text-tertiary">{i + 1}</td>
                      <td className="p-2 font-medium text-[#f0f4ff]">{v.model_name}</td>
                      <td className="p-2 text-tertiary">{v.category.replace(/_/g, " ")}</td>
                      <td className="p-2 text-right font-mono tabular-nums">{v.confidence.toFixed(1)}%</td>
                      <td className="p-2 text-right font-mono tabular-nums">×{v.weight}</td>
                      <td className="p-2 text-right font-mono tabular-nums">{v.weighted_score.toFixed(1)}</td>
                      <td className="p-2 text-right font-mono tabular-nums">{contrib.toFixed(1)}%</td>
                      <td className="p-2 text-right font-mono tabular-nums text-tertiary">{v.inference_ms.toFixed(0)}ms</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {result.rejected.length > 0 && (
        <Card>
          <CardHeader title="Modèles rejetés" subtitle={`${result.rejected.length} modèles exclus`} icon={<XCircle size={18} />} />
          <div className="flex flex-wrap gap-2">
            {result.rejected.map((v) => (
              <span key={v.model_id} className="rounded-full bg-block/10 px-2.5 py-1 text-[10px] text-block">
                {v.model_name} ({v.error || `< ${result.config.medium_confidence_threshold}%`})
              </span>
            ))}
          </div>
        </Card>
      )}
    </>
  );
}

function MiniStat({ label, value, icon, color = "text-secondary" }: { label: string; value: number | string; icon: React.ReactNode; color?: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-white/[0.02] px-3 py-2">
      <span className="flex items-center gap-1.5 text-[11px] text-secondary">
        {icon} {label}
      </span>
      <span className={cn("font-mono text-xs font-semibold tabular-nums", color)}>{value}</span>
    </div>
  );
}
