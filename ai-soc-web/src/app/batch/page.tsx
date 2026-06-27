"use client";

import { useState } from "react";
import { useTestScripts, useModels } from "@/hooks/useApi";
import { api, BackendUnreachable } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { computeMetrics, categoryFromId, pct } from "@/lib/metrics";
import { PageHeader, DemoBanner } from "@/components/layout/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { RadialGauge } from "@/components/ui/RadialGauge";
import { cn } from "@/lib/utils";
import type { RunTestsResponse, TestReport } from "@/types/api";
import { Boxes, Play, LoaderCircle, Terminal, CircleCheck, XCircle, AlertCircle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";

export default function BatchPage() {
  const scripts = useTestScripts();
  const models = useModels();
  const [selectedScript, setSelectedScript] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  const scriptList = scripts.data?.scripts ?? [];
  const modelList = models.data?.models ?? [];
  const script = selectedScript || scriptList[0]?.name || "";
  const model = selectedModel || modelList[0]?.id || "";

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        return await api.runTests(model, script);
      } catch (e) {
        if (e instanceof BackendUnreachable) {
          // Mode démo : rapport simulé cohérent.
          return mockRunTests(model, script) as RunTestsResponse;
        }
        throw e;
      }
    },
  });

  const report =
    mutation.data && mutation.data.report && "test_results" in mutation.data.report
      ? (mutation.data.report as TestReport)
      : null;
  const metrics = report ? computeMetrics(report) : null;

  return (
    <div>
      <DemoBanner demo={scripts.demo} />

      <PageHeader
        icon={<Boxes size={22} />}
        title="Batch Evaluation"
        description="Suite de tests automatisés avec métriques avancées (precision, recall, F1, confusion matrix)."
      />

      <div className="grid gap-5 lg:grid-cols-4">
        {/* Configuration */}
        <Card className="lg:col-span-1">
          <CardHeader title="Configuration" icon={<Terminal size={18} />} />

          <label className="mb-1.5 block text-[11px] uppercase tracking-wider text-secondary">
            Script de test
          </label>
          <select
            value={script}
            onChange={(e) => setSelectedScript(e.target.value)}
            className="mb-4 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-[#f0f4ff] focus:border-primary/50 focus:outline-none"
          >
            {scriptList.map((s) => (
              <option key={s.name} value={s.name} className="bg-base-800">
                {s.name}
              </option>
            ))}
          </select>

          {/* Modèle masqué pour l'utilisateur, exécuté par défaut */}

          <button
            onClick={() => mutation.mutate()}
            disabled={!script || !model || mutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-glow transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            {mutation.isPending ? (
              <LoaderCircle size={16} className="animate-spin" />
            ) : (
              <Play size={16} />
            )}
            {mutation.isPending ? "Exécution…" : "Lancer les tests"}
          </button>

          <p className="mt-3 text-[10px] leading-relaxed text-tertiary">
            ⚠️ L'exécution réelle peut durer jusqu'à 5 min (les modèles génératifs
            sont séquentiels). En mode démo, un rapport simulé est renvoyé.
          </p>
        </Card>

        {/* Résultats */}
        <div className="space-y-4 lg:col-span-3">
          {!report && !mutation.isPending && (
            <Card className="flex h-64 flex-col items-center justify-center text-center">
              <Boxes size={40} className="mb-3 text-tertiary" />
              <p className="text-sm text-secondary">
                Sélectionnez un script et un modèle, puis lancez l'évaluation.
              </p>
            </Card>
          )}

          {mutation.isPending && (
            <Card className="flex h-64 flex-col items-center justify-center">
              <LoaderCircle size={32} className="animate-spin text-primary" />
              <p className="mt-3 text-sm text-secondary">Exécution des tests…</p>
            </Card>
          )}

          {report && metrics && (
            <BatchResults report={report} metrics={metrics} />
          )}
        </div>
      </div>
    </div>
  );
}

function BatchResults({
  report,
  metrics,
}: {
  report: TestReport;
  metrics: NonNullable<ReturnType<typeof computeMetrics>>;
}) {
  return (
    <>
      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Accuracy"
          value={pct(report.accuracy)}
          tone="primary"
          sub={`${metrics.evaluated} cas évalués`}
        />
        <StatCard label="Precision" value={pct(metrics.precision)} tone="info" />
        <StatCard label="Recall" value={pct(metrics.recall)} tone="accept" />
        <StatCard label="F1-Score" value={pct(metrics.f1)} tone="warn" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Gauges */}
        <Card>
          <CardHeader title="Synthèse" subtitle="Rapport d'évaluation global" icon={<Boxes size={18} />} />
          <div className="flex items-center justify-around">
            <RadialGauge value={report.accuracy * 100} label="Accuracy" sublabel="global" tone="primary" size={110} />
            <RadialGauge value={metrics.f1 * 100} label="F1" sublabel="harmonique" tone="warn" size={110} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <MiniStat label="Pass" value={report.passed} tone="accept" icon={<CircleCheck size={13} />} />
            <MiniStat label="Fail" value={report.failed} tone="block" icon={<XCircle size={13} />} />
            <MiniStat label="Err" value={report.errors} tone="warn" icon={<AlertCircle size={13} />} />
          </div>
        </Card>

        {/* Confusion matrix (2x2 phishing/safe) */}
        <Card>
          <CardHeader title="Matrice de confusion" subtitle="Phishing / Safe" icon={<Terminal size={18} />} />
          <ConfusionMatrix metrics={metrics} />
        </Card>
      </div>

      {/* Précision par catégorie */}
      {metrics.perCategory.length > 0 && (
        <Card>
          <CardHeader title="Performance par catégorie" icon={<Boxes size={18} />} />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={metrics.perCategory} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="category" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#0f1424",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, "Accuracy"]}
              />
              <Bar dataKey={(d) => d.accuracy * 100} name="Accuracy" radius={[4, 4, 0, 0]}>
                {metrics.perCategory.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={
                      entry.accuracy > 0.8
                        ? "hsl(142, 72%, 46%)"
                        : entry.accuracy > 0.5
                        ? "hsl(38, 92%, 55%)"
                        : "hsl(0, 82%, 58%)"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Log des résultats */}
      <Card>
        <CardHeader title="Journal des tests" subtitle={`${report.test_results.length} cas`} icon={<Terminal size={18} />} />
        <div className="max-h-80 overflow-auto rounded-lg border border-white/5 bg-black/40 p-3 font-mono text-[11px]">
          {report.test_results.map((t, i) => (
            <div key={i} className="flex items-start gap-2 border-b border-white/[0.03] py-1.5 last:border-0">
              <StatusTag status={t.status} />
              <span className="shrink-0 text-tertiary">[{categoryFromId(t.id)}]</span>
              <span className="shrink-0 text-secondary">{t.id}</span>
              <span className="min-w-0 flex-1 truncate text-[#cbd5e1]">{t.title}</span>
              {t.expected && (
                <span className="shrink-0 text-tertiary">→ {t.expected}</span>
              )}
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}

function MiniStat({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: number;
  tone: "accept" | "block" | "warn";
  icon: React.ReactNode;
}) {
  const color = { accept: "text-accept", block: "text-block", warn: "text-warn" }[tone];
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] py-2">
      <div className={cn("flex items-center justify-center gap-1 font-display text-lg font-bold", color)}>
        {icon}
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-tertiary">{label}</div>
    </div>
  );
}

function StatusTag({ status }: { status: string }) {
  const map: Record<string, string> = {
    PASS: "text-accept",
    FAIL: "text-block",
    ERROR: "text-block",
    GENERATED: "text-info",
    INFO: "text-secondary",
    unknown: "text-tertiary",
  };
  return (
    <span className={cn("w-20 shrink-0 font-semibold", map[status] ?? "text-tertiary")}>
      [{status}]
    </span>
  );
}

function ConfusionMatrix({
  metrics,
}: {
  metrics: NonNullable<ReturnType<typeof computeMetrics>>;
}) {
  // On reconstruit une matrice 2x2 à partir des cellules (phishing/safe).
  const cell = (exp: string, pred: string) =>
    metrics.confusion.find(
      (c) => c.expected === exp && c.predicted === pred
    )?.count ?? 0;

  const rows = ["Phishing Email", "Safe Email"];
  const cols = ["Phishing Email", "Safe Email"];
  const short = (s: string) => (s.includes("Phish") ? "Phish" : "Safe");

  // Si pas de données évaluables (modèle génératif), on l'indique.
  if (metrics.evaluated === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-center text-sm text-tertiary">
        Aucune donnée évaluable pour ce modèle (résultats génératifs, pas de
        pass/fail).
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-white/10">
      <table className="w-full text-center text-xs">
        <thead>
          <tr>
            <th className="bg-white/[0.03] p-2 text-tertiary">
              Attendu \ Prédit
            </th>
            {cols.map((c) => (
              <th key={c} className="bg-white/[0.03] p-2 font-display text-secondary">
                {short(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td className="bg-white/[0.03] p-2 font-display text-secondary">
                {short(r)}
              </td>
              {cols.map((c) => {
                const count = cell(r, c);
                const ok = short(r) === short(c);
                return (
                  <td
                    key={c}
                    className={cn(
                      "p-3 font-display text-lg font-bold tabular-nums",
                      ok ? "bg-accept/10 text-accept" : "bg-block/10 text-block"
                    )}
                  >
                    {count}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ───── Mock d'un rapport de test pour le mode démo ───── */
function mockRunTests(model: string, script: string): RunTestsResponse {
  const cases = Array.from({ length: 12 }, (_, i) => {
    const isPhish = i % 2 === 0;
    const correct = Math.random() > 0.18;
    return {
      id: `TEST-${isPhish ? "PHISH" : "SAFE"}-${String(i + 1).padStart(3, "0")}`,
      title: isPhish ? "Tentative de phishing détectée" : "Email légitime",
      status: (correct ? "PASS" : "FAIL") as "PASS" | "FAIL",
      expected: isPhish ? "Phishing Email" : "Safe Email",
      prediction: {
        predicted_label: correct
          ? isPhish
            ? "Phishing Email"
            : "Safe Email"
          : isPhish
          ? "Safe Email"
          : "Phishing Email",
        confidence: 0.7 + Math.random() * 0.29,
        all_probabilities: {
          "Phishing Email": isPhish ? 0.85 : 0.15,
          "Safe Email": isPhish ? 0.15 : 0.85,
        },
      },
    };
  });
  const passed = cases.filter((c) => c.status === "PASS").length;
  const failed = cases.length - passed;
  return {
    success: true,
    stdout: `[mock] ${model} × ${script} → ${passed}/${cases.length}`,
    stderr: "",
    report: {
      model,
      timestamp: new Date().toISOString(),
      total_tests: cases.length,
      passed,
      failed,
      errors: 0,
      accuracy: passed / cases.length,
      test_results: cases,
    },
  };
}
