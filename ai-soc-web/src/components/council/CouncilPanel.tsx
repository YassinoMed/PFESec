"use client";

import { useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock,
  GitCompareArrows,
  LoaderCircle,
  MessageSquare,
  Play,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";

interface ExpertAnalysis {
  expert_id: string;
  expert_name: string;
  category: string;
  status: string;
  response: unknown;
  conclusion: string;
  confidence: number;
  evidence: string[];
  limitations: string[];
  inference_ms: number;
  error?: string;
}

interface CouncilMessage {
  speaker: string;
  target?: string;
  phase: string;
  content: string;
  timestamp: string;
}

interface CouncilResult {
  classification: string;
  selected_models: string[];
  experts: ExpertAnalysis[];
  conversation: CouncilMessage[];
  contradictions: Array<Record<string, unknown>>;
  cross_validations: Array<{ reviewer: string; reviewed: string; status: string; notes: string }>;
  fact_check: { references: Array<{ source: string; text: string; score: number }>; hypotheses: string[]; unconfirmed: string[] };
  consensus: { global_score: number; confidence_level: string; total_retained: number; total_models_executed: number };
  reflection: { passed: boolean; issues: string[]; action: string };
  final_response: {
    conclusion: string;
    answer: string;
    global_confidence: number;
    confidence_level: string;
    participants: string[];
    primary_model?: string;
    main_evidence: string[];
    references_rag: Array<{ source: string; text: string; score: number }>;
    decision_reasons: string[];
    divergences: Array<Record<string, unknown>>;
  };
  timeline: Array<{ name: string; status: string; elapsed_ms: number; data: Record<string, unknown> }>;
  metrics: { total_execution_ms: number; experts_completed: number; experts_failed: number };
}

const ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || "http://localhost:8080";

export default function CouncilPanel() {
  const [query, setQuery] = useState("Analyse ce mail: URGENT, cliquez ici pour verifier votre mot de passe.");
  const [result, setResult] = useState<CouncilResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runCouncil = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${ORCHESTRATOR_URL}/api/v1/security/council`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
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
          title="Session Council"
          subtitle="Master AI, experts spécialisés, discussion, validation croisée et consensus argumenté"
          icon={<Brain size={18} />}
          action={
            <button
              onClick={runCouncil}
              disabled={loading || !query.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-white shadow-glow transition hover:bg-primary/90 disabled:opacity-40"
            >
              {loading ? <LoaderCircle size={14} className="animate-spin" /> : <Play size={14} />}
              Lancer
            </button>
          }
        />
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={4}
          className="w-full resize-none rounded-lg border border-white/10 bg-black/30 px-3 py-3 font-mono text-xs leading-5 text-[#f0f4ff] placeholder:text-tertiary focus:border-primary/50 focus:outline-none"
        />
      </Card>

      {error && (
        <Card className="border-block/30">
          <p className="flex items-center gap-2 text-sm text-block"><XCircle size={16} /> {error}</p>
        </Card>
      )}

      {loading && (
        <div className="flex h-40 items-center justify-center">
          <LoaderCircle size={30} className="animate-spin text-primary" />
          <span className="ml-3 text-sm text-secondary">Le Master AI consulte le conseil...</span>
        </div>
      )}

      {result && <CouncilDisplay result={result} />}
    </div>
  );
}

function CouncilDisplay({ result }: { result: CouncilResult }) {
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-4">
        <ScoreCard result={result} />
        <MiniCard label="Experts terminés" value={`${result.metrics.experts_completed}/${result.experts.length}`} icon={<ShieldCheck size={14} />} />
        <MiniCard label="Contradictions" value={result.contradictions.length} icon={<AlertTriangle size={14} />} tone={result.contradictions.length ? "warn" : "accept"} />
        <MiniCard label="Temps total" value={`${result.metrics.total_execution_ms.toFixed(0)} ms`} icon={<Clock size={14} />} />
      </div>

      <Card>
        <CardHeader title="Réponse finale du Master AI" subtitle={result.final_response.primary_model ? `Modèle principal: ${result.final_response.primary_model}` : undefined} icon={<Sparkles size={18} />} />
        <p className="rounded-lg border border-white/5 bg-black/20 p-4 text-sm leading-6 text-[#f0f4ff]">
          {result.final_response.answer}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {result.final_response.decision_reasons.map((reason) => (
            <span key={reason} className="rounded-lg bg-primary/10 px-2.5 py-1 text-[11px] text-primary">{reason}</span>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Timeline items={result.timeline} />
        <Conversation messages={result.conversation} />
      </div>

      <ExpertsTable experts={result.experts} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Validations croisées" subtitle={`${result.cross_validations.length} vérifications`} icon={<GitCompareArrows size={18} />} />
          <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
            {result.cross_validations.slice(0, 12).map((v, i) => (
              <div key={`${v.reviewer}-${v.reviewed}-${i}`} className="rounded-lg bg-white/[0.02] px-3 py-2 text-xs">
                <span className={cn("font-semibold", v.status === "confirmed" ? "text-accept" : v.status === "challenged" ? "text-warn" : "text-secondary")}>{v.status}</span>
                <p className="mt-1 text-secondary">{v.notes}</p>
              </div>
            ))}
            {result.cross_validations.length === 0 && <p className="text-sm text-secondary">Aucune validation croisée exécutée.</p>}
          </div>
        </Card>

        <Card>
          <CardHeader title="Fact checking RAG" subtitle={`${result.fact_check.references.length} références locales`} icon={<CheckCircle2 size={18} />} />
          <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
            {result.fact_check.references.map((ref) => (
              <div key={`${ref.source}-${ref.text}`} className="rounded-lg bg-white/[0.02] px-3 py-2 text-xs">
                <span className="font-mono text-primary">{ref.source}</span>
                <p className="mt-1 text-secondary">{ref.text}</p>
              </div>
            ))}
            {result.fact_check.references.length === 0 && <p className="text-sm text-secondary">Aucune référence locale confirmée.</p>}
          </div>
        </Card>
      </div>
    </>
  );
}

function ScoreCard({ result }: { result: CouncilResult }) {
  const score = result.consensus.global_score || 0;
  const tone = result.consensus.confidence_level === "High" ? "accept" : result.consensus.confidence_level === "Medium" ? "warn" : "block";
  return (
    <Card className="lg:col-span-1">
      <div className="space-y-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-secondary">Consensus</p>
          <p className={cn("mt-1 text-3xl font-bold tabular-nums", tone === "accept" ? "text-accept" : tone === "warn" ? "text-warn" : "text-block")}>{score.toFixed(1)}%</p>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white/5">
          <div className={cn("h-full rounded-full transition-all duration-1000", tone === "accept" ? "bg-accept" : tone === "warn" ? "bg-warn" : "bg-block")} style={{ width: `${Math.min(100, score)}%` }} />
        </div>
        <p className="text-xs text-secondary">{result.final_response.conclusion} · {result.consensus.confidence_level}</p>
      </div>
    </Card>
  );
}

function Timeline({ items }: { items: CouncilResult["timeline"] }) {
  return (
    <Card>
      <CardHeader title="Timeline de décision" subtitle="Étapes du Master AI" icon={<Clock size={18} />} />
      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={item.name} className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2">
            <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold", item.status === "completed" ? "bg-accept/15 text-accept" : "bg-warn/15 text-warn")}>{index + 1}</span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium capitalize text-[#f0f4ff]">{item.name.replace(/_/g, " ")}</p>
              <p className="text-[11px] text-secondary">{item.status} · {item.elapsed_ms.toFixed(0)} ms</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Conversation({ messages }: { messages: CouncilMessage[] }) {
  return (
    <Card>
      <CardHeader title="Dialogue Master / Experts" subtitle={`${messages.length} messages`} icon={<MessageSquare size={18} />} />
      <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
        {messages.map((message, index) => (
          <div key={`${message.timestamp}-${index}`} className={cn("rounded-lg border px-3 py-2 text-xs", message.speaker === "Master AI" ? "border-primary/20 bg-primary/10" : "border-white/5 bg-white/[0.02]")}>
            <div className="mb-1 flex items-center justify-between gap-3">
              <span className="font-semibold text-[#f0f4ff]">{message.speaker}</span>
              <span className="rounded bg-black/20 px-1.5 py-0.5 font-mono text-[10px] text-tertiary">{message.phase}</span>
            </div>
            <p className="leading-5 text-secondary">{message.content}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ExpertsTable({ experts }: { experts: ExpertAnalysis[] }) {
  return (
    <Card>
      <CardHeader title="Experts IA" subtitle="États, scores et preuves utilisées" icon={<ShieldCheck size={18} />} />
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/5 text-tertiary">
              <th className="p-2 font-medium">Expert</th>
              <th className="p-2 font-medium">État</th>
              <th className="p-2 font-medium">Conclusion</th>
              <th className="p-2 font-medium text-right">Confiance</th>
              <th className="p-2 font-medium text-right">Temps</th>
              <th className="p-2 font-medium">Preuves</th>
            </tr>
          </thead>
          <tbody>
            {experts.map((expert) => (
              <tr key={expert.expert_id} className="border-b border-white/[0.03]">
                <td className="p-2 font-medium text-[#f0f4ff]">{expert.expert_name}</td>
                <td className="p-2"><StatusPill status={expert.status} /></td>
                <td className="p-2 font-mono">{expert.conclusion}</td>
                <td className="p-2 text-right font-mono tabular-nums">{expert.confidence.toFixed(1)}%</td>
                <td className="p-2 text-right font-mono tabular-nums text-tertiary">{expert.inference_ms.toFixed(0)} ms</td>
                <td className="p-2 text-secondary">{expert.evidence.slice(0, 3).join(", ") || expert.error || "Aucune"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function StatusPill({ status }: { status: string }) {
  const ok = status === "completed";
  const fail = status === "error" || status === "timeout";
  return (
    <span className={cn("rounded-full px-2 py-1 text-[10px] font-semibold", ok ? "bg-accept/10 text-accept" : fail ? "bg-block/10 text-block" : "bg-warn/10 text-warn")}>
      {status}
    </span>
  );
}

function MiniCard({ label, value, icon, tone = "primary" }: { label: string; value: number | string; icon: React.ReactNode; tone?: "primary" | "warn" | "accept" }) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] text-secondary">{label}</p>
          <p className={cn("mt-1 font-mono text-lg font-semibold", tone === "warn" ? "text-warn" : tone === "accept" ? "text-accept" : "text-[#f0f4ff]")}>{value}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-primary">{icon}</div>
      </div>
    </Card>
  );
}
