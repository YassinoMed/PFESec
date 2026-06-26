"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, BackendUnreachable } from "@/lib/api";
import { useModels } from "@/hooks/useApi";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { VerdictPill } from "@/components/ui/VerdictPill";
import { ThreatBar } from "@/components/ui/ThreatBar";
import { ModelBadge } from "@/components/ui/ModelBadge";
import { cn } from "@/lib/utils";
import { FlaskConical, Play, LoaderCircle, Clock } from "lucide-react";
import { mockPredictAll } from "@/lib/mock";

export default function SandboxPage() {
  const models = useModels();
  const [selected, setSelected] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<null | (ReturnType<typeof mockPredictAll>["results"][number] & { error?: string })>(null);

  const modelList = models.data?.models ?? [];
  const current = selected || modelList[0]?.id || "";
  const currentModel = modelList.find((m) => m.id === current);

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        return await api.predict(current, prompt);
      } catch (e) {
        if (e instanceof BackendUnreachable) {
          // En mode démo, on pioche le résultat correspondant au modèle.
          const all = mockPredictAll(prompt);
          const r = all.results.find((x) => x.model_id === current);
          return r ?? all.results[0];
        }
        throw e;
      }
    },
    onSuccess: setResult,
  });

  const isClassif = result && "type" in result && result.type === "classification";
  const probs =
    isClassif && result && "probabilities" in result
      ? Object.entries(result.probabilities).sort((a, b) => b[1] - a[1])
      : [];

  return (
    <div>
      <DemoBanner demo={models.demo} />

      <PageHeader
        icon={<FlaskConical size={22} />}
        title="Single-Model Sandbox"
        description="Inférence isolée sur un modèle sélectionné, vue détaillée."
      />

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Saisie */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Configuration"
              subtitle="Choix du modèle et du texte"
              icon={<FlaskConical size={18} />}
            />

            {/* Sélecteur de modèle */}
            <label className="mb-1.5 block text-[11px] uppercase tracking-wider text-secondary">
              Modèle
            </label>
            <div className="mb-4 grid gap-2 sm:grid-cols-2">
              {modelList.map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    setSelected(m.id);
                    setResult(null);
                  }}
                  className={cn(
                    "flex items-center gap-2 rounded-lg border p-2.5 text-left transition-colors",
                    current === m.id
                      ? "border-primary/40 bg-primary/10"
                      : "border-white/[0.07] bg-white/[0.02] hover:border-white/15"
                  )}
                >
                  <span className="text-lg">{m.icon}</span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate text-xs font-semibold text-[#f0f4ff]">
                        {m.name}
                      </span>
                      <ModelBadge type={m.type} />
                    </div>
                    <p className="truncate text-[10px] text-tertiary">
                      {m.task}
                    </p>
                  </div>
                </button>
              ))}
            </div>

            <label className="mb-1.5 block text-[11px] uppercase tracking-wider text-secondary">
              Texte
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={7}
              placeholder="Saisissez le texte à analyser…"
              className="w-full resize-none rounded-xl border border-white/10 bg-black/30 p-3 font-mono text-sm text-[#f0f4ff] placeholder:text-tertiary focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />

            <button
              onClick={() => mutation.mutate()}
              disabled={!prompt.trim() || !current || mutation.isPending}
              className="mt-3 flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
            >
              {mutation.isPending ? (
                <LoaderCircle size={16} className="animate-spin" />
              ) : (
                <Play size={16} />
              )}
              Lancer l'inférence
            </button>
          </Card>
        </div>

        {/* Résultat */}
        <div>
          <Card className="min-h-[400px]">
            <CardHeader
              title="Résultat détaillé"
              subtitle={currentModel?.name ?? "—"}
              icon={<FlaskConical size={18} />}
            />

            {!result && !mutation.isPending && (
              <div className="flex h-64 flex-col items-center justify-center text-center">
                <span className="text-4xl opacity-30">{currentModel?.icon ?? "🤖"}</span>
                <p className="mt-3 text-sm text-tertiary">
                  En attente d'une inférence…
                </p>
              </div>
            )}

            {mutation.isPending && (
              <div className="flex h-64 flex-col items-center justify-center">
                <LoaderCircle size={32} className="animate-spin text-primary" />
                <p className="mt-3 text-sm text-secondary">Inférence en cours…</p>
              </div>
            )}

            {result && !("error" in result) && "type" in result && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{result.icon}</span>
                    <span className="font-display font-semibold text-[#f0f4ff]">
                      {result.model_name}
                    </span>
                  </div>
                  <VerdictPill verdict={result.verdict} />
                </div>

                <ThreatBar score={result.threat_score} />

                {isClassif ? (
                  <div>
                    <p className="mb-2 text-[11px] uppercase tracking-wider text-tertiary">
                      Confiance : <span className="text-primary">{((result as { confidence: number }).confidence * 100).toFixed(1)}%</span>
                    </p>
                    <div className="space-y-2">
                      {probs.map(([label, p]) => (
                        <div key={label}>
                          <div className="mb-1 flex justify-between text-xs">
                            <span className="text-secondary">{label}</span>
                            <span className="font-mono text-secondary">{(p * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-white/5">
                            <div
                              className={cn("h-full rounded-full", p > 0.5 ? "bg-primary" : "bg-white/20")}
                              style={{ width: `${p * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="mb-1.5 text-[11px] uppercase tracking-wider text-tertiary">
                      Réponse générée
                    </p>
                    <pre className="max-h-60 overflow-auto rounded-lg border border-white/5 bg-black/40 p-3 font-mono text-xs leading-relaxed text-info whitespace-pre-wrap">
                      {result.prediction}
                    </pre>
                  </div>
                )}

                <div className="flex items-center justify-between border-t border-white/5 pt-3 text-[11px] text-tertiary">
                  <span className="uppercase tracking-wider">
                    {isClassif ? "Classification" : "Génératif"}
                  </span>
                  <span className="flex items-center gap-1 font-mono">
                    <Clock size={11} /> {result.elapsed_s}s
                  </span>
                </div>
              </div>
            )}

            {result && "error" in result && (
              <div className="rounded-lg bg-block/10 p-3 font-mono text-sm text-block">
                {result.error}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
