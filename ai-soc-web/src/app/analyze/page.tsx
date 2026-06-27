"use client";

import { useState } from "react";
import { usePredictAll } from "@/hooks/useApi";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { VerdictPill } from "@/components/ui/VerdictPill";
import { ResultCard } from "@/components/inference/ResultCard";
import { cn } from "@/lib/utils";
import type { ConsensusVerdict } from "@/types/api";
import { Crosshair, Play, LoaderCircle, Trash2, Sparkles, Radar } from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Radar as RechartsRadar,
} from "recharts";

const SAMPLES = [
  {
    label: "Phishing bancaire",
    text: "Urgent : votre compte a été suspendu. Vérifiez votre identité immédiatement via ce lien : http://banque-secure.xyz/login sinon votre compte sera définitivement bloqué.",
  },
  {
    label: "Email légitime",
    text: "Bonjour, veuillez trouver ci-joint le compte-rendu de la réunion d'hier. N'hésitez pas si vous avez des questions. Bonne journée, L'équipe projet.",
  },
  {
    label: "BEC / Spear phishing",
    text: "Bonjour, pourriez-vous traiter en urgence le virement de 45 000€ vers le nouveau fournisseur ? Je suis en réunion toute la journée. Merci de votre réactivité. Le DG.",
  },
];

export default function AnalyzePage() {
  const [prompt, setPrompt] = useState("");
  const mutation = usePredictAll();
  const data = mutation.data;

  return (
    <div>
      <DemoBanner demo={false} />

      <PageHeader
        icon={<Crosshair size={22} />}
        title="Threat Analysis"
        description="Analyse multi-modèles en temps réel avec consensus de vote."
      />

      <div className="grid gap-5 lg:grid-cols-5">
        {/* Saisie */}
        <div className="space-y-4 lg:col-span-3">
          <Card>
            <CardHeader
              title="Texte à analyser"
              subtitle="Email, message ou prompt suspect"
              icon={<Crosshair size={18} />}
            />
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={8}
              placeholder="Collez ici le contenu d'un email, un message ou un prompt à faire analyser par tous les modèles…"
              className="w-full resize-none rounded-xl border border-white/10 bg-black/30 p-3 font-mono text-sm text-[#f0f4ff] placeholder:text-tertiary focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />

            {/* Samples */}
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="self-center text-[11px] uppercase tracking-wider text-tertiary">
                <Sparkles size={12} className="mr-1 inline" />
                Exemples :
              </span>
              {SAMPLES.map((s) => (
                <button
                  key={s.label}
                  onClick={() => setPrompt(s.text)}
                  className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] text-secondary transition-colors hover:border-primary/30 hover:text-primary"
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Actions */}
            <div className="mt-4 flex items-center gap-2">
              <button
                onClick={() => mutation.mutate(prompt)}
                disabled={!prompt.trim() || mutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
              >
                {mutation.isPending ? (
                  <LoaderCircle size={16} className="animate-spin" />
                ) : (
                  <Play size={16} />
                )}
                {mutation.isPending ? "Analyse en cours…" : "Analyser (tous modèles)"}
              </button>
              <button
                onClick={() => {
                  setPrompt("");
                  mutation.reset();
                }}
                className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2.5 text-sm text-secondary transition-colors hover:bg-white/5"
              >
                <Trash2 size={15} />
                Effacer
              </button>
            </div>
          </Card>

          {/* Résultats par modèle masqués */}
        </div>

        {/* Panneau consensus */}
        <div className="lg:col-span-2">
          <div className="sticky top-20 space-y-4">
            {data ? (
              <ConsensusPanel
                verdict={data.consensus.verdict}
                blockVotes={data.consensus.block_votes}
                acceptVotes={data.consensus.accept_votes}
                totalVotes={data.consensus.total_votes}
                confidence={data.consensus.confidence_pct}
                // On n'envoie au radar que les résultats valides (pas les erreurs).
                results={data.results.flatMap((r) =>
                  "model_name" in r && "threat_score" in r && "verdict" in r
                    ? [r]
                    : []
                )}
              />
            ) : (
              <Card className="flex h-64 flex-col items-center justify-center text-center">
                <Radar size={40} className="mb-3 text-tertiary" />
                <p className="text-sm text-secondary">
                  Lancez une analyse pour visualiser le consensus multi-modèles
                </p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ConsensusPanel({
  verdict,
  blockVotes,
  acceptVotes,
  totalVotes,
  confidence,
  results,
}: {
  verdict: ConsensusVerdict;
  blockVotes: number;
  acceptVotes: number;
  totalVotes: number;
  confidence: number;
  results: { model_name: string; threat_score: number; verdict: string }[];
}) {
  const tone = verdict === "BLOCK" ? "block" : verdict === "ACCEPT" ? "accept" : "warn";

  const radarData = results.map((r) => ({
    model: r.model_name.split(" ")[0],
    score: Math.round(r.threat_score),
  }));

  return (
    <>
      {/* Bandeau verdict */}
      <Card
        className={cn(
          "animate-slide-in border-2",
          tone === "block" && "border-block/40 shadow-glow-block",
          tone === "accept" && "border-accept/40 shadow-glow-accept",
          tone === "warn" && "border-warn/40"
        )}
      >
        <div className="flex flex-col items-center py-3 text-center">
          <span className="text-4xl">
            {verdict === "BLOCK" ? "🚨" : verdict === "ACCEPT" ? "✅" : "⚠️"}
          </span>
          <p className="mt-2 text-[11px] uppercase tracking-[0.2em] text-secondary">
            Verdict consensuel
          </p>
          <VerdictPill verdict={verdict} />
          <p className="mt-3 text-xs text-secondary">
            {verdict === "BLOCK"
              ? "Menace détectée — majorité de modèles en alerte"
              : verdict === "ACCEPT"
              ? "Aucune menace — contenu considéré comme sûr"
              : "Résultat incertain — les modèles divergent"}
          </p>
        </div>
      </Card>

      <div className="grid grid-cols-3 gap-2">
        <StatCard label="Block" value={blockVotes} tone="block" />
        <StatCard label="Accept" value={acceptVotes} tone="accept" />
        <StatCard label="Confiance" value={`${confidence.toFixed(0)}%`} tone="primary" />
      </div>

      {/* Radar des scores masqué */}
      <p className="mt-4 text-center text-[11px] text-tertiary">
        Scoring calculé sur l'ensemble de la flotte de modèles IA de sécurité de manière consolidée.
      </p>
    </>
  );
}
