"use client";

import React from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { AlertCircle } from "lucide-react";

interface RiskAssessmentProps {
  assessment: {
    severity: string;
    severity_score: number;
    probability: number;
    impact: string;
    impact_score: number;
    criticality: string;
    risk_score: number;
    cvss_vector?: string;
  };
}

export default function RiskMatrix({ assessment }: RiskAssessmentProps) {
  const { severity, severity_score, probability, impact, impact_score, criticality, risk_score, cvss_vector } = assessment;

  // Map scores to grid indices (0 to 4) for the 5x5 matrix
  // Probability: 0-100% -> 5 classes (0-20, 20-40, 40-60, 60-80, 80-100)
  // Impact: 0-10 -> 5 classes (0-2, 2-4, 4-6, 6-8, 8-10)
  const probIdx = Math.min(Math.floor(probability / 20), 4);
  const impIdx = Math.min(Math.floor(impact_score / 2), 4);

  // Grid coordinates: y (impact) decreases from top (4) to bottom (0), x (probability) increases from left (0) to right (4)
  const gridCells = [];
  for (let r = 4; r >= 0; r--) {
    for (let c = 0; c < 5; c++) {
      const isTarget = r === impIdx && c === probIdx;

      // Determine cell danger tone based on position
      let cellTone = "bg-white/[0.02]";
      if (r + c >= 6) {
        cellTone = "bg-block/15 hover:bg-block/25"; // Critical / High zone
      } else if (r + c >= 4) {
        cellTone = "bg-warn/15 hover:bg-warn/25";   // Medium zone
      } else if (r + c >= 2) {
        cellTone = "bg-accept/10 hover:bg-accept/20"; // Low zone
      }

      gridCells.push(
        <div
          key={`cell-${r}-${c}`}
          className={cn(
            "relative flex h-8 w-8 items-center justify-center rounded border border-white/5 transition-all duration-300",
            cellTone,
            isTarget && "ring-2 ring-block ring-offset-2 ring-offset-black scale-110 z-10 shadow-[0_0_12px_rgba(239,68,68,0.6)]"
          )}
        >
          {isTarget && (
            <span className="absolute animate-ping h-2.5 w-2.5 rounded-full bg-block opacity-75" />
          )}
          {isTarget && (
            <div className="h-2 w-2 rounded-full bg-block" />
          )}
        </div>
      );
    }
  }

  return (
    <Card className="flex flex-col h-full">
      <CardHeader
        title="Évaluation des Risques"
        subtitle="Matrice de sévérité composite (Impact × Probabilité)"
        icon={<AlertCircle size={18} />}
      />

      <div className="space-y-4 p-4 flex-1">
        {/* Core numbers display */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-white/[0.02] border border-white/5 p-2">
            <span className="text-[10px] text-secondary uppercase block">Risque</span>
            <span className="text-lg font-bold font-mono text-[#f0f4ff]">{risk_score.toFixed(1)}</span>
          </div>
          <div className="rounded-lg bg-white/[0.02] border border-white/5 p-2">
            <span className="text-[10px] text-secondary uppercase block">Probabilité</span>
            <span className="text-lg font-bold font-mono text-[#f0f4ff]">{probability.toFixed(0)}%</span>
          </div>
          <div className="rounded-lg bg-white/[0.02] border border-white/5 p-2">
            <span className="text-[10px] text-secondary uppercase block">Impact</span>
            <span className="text-lg font-bold font-mono text-[#f0f4ff]">{impact_score.toFixed(1)}/10</span>
          </div>
        </div>

        {/* Matrix Visualization */}
        <div className="flex items-center justify-center gap-6 py-2">
          {/* Y Axis Label (Impact) */}
          <div className="flex h-[180px] flex-col justify-between text-[10px] text-secondary text-right pr-1">
            <span>Très Élevé</span>
            <span>Élevé</span>
            <span>Moyen</span>
            <span>Faible</span>
            <span>Très Faible</span>
          </div>

          <div className="flex flex-col gap-1.5">
            {/* 5x5 Grid */}
            <div className="grid grid-cols-5 gap-1.5 p-1 bg-white/[0.01] border border-white/5 rounded-lg">
              {gridCells}
            </div>

            {/* X Axis Label (Probability) */}
            <div className="flex justify-between text-[10px] text-secondary px-1">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Level and vector details */}
        <div className="space-y-2 border-t border-white/5 pt-3 text-xs leading-relaxed">
          <div className="flex justify-between">
            <span className="text-secondary">Classe de Risque:</span>
            <span
              className={cn(
                "font-bold uppercase",
                severity === "CRITICAL"
                  ? "text-block animate-pulse"
                  : severity === "HIGH"
                  ? "text-block"
                  : severity === "MEDIUM"
                  ? "text-warn"
                  : "text-accept"
              )}
            >
              {severity} ({severity_score.toFixed(1)}/10)
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-secondary">SLA / Criticité:</span>
            <span className="text-[#f0f4ff] font-medium">{criticality}</span>
          </div>
          {cvss_vector && (
            <div className="mt-2 rounded bg-white/[0.02] border border-white/5 px-2 py-1.5 text-[10px] font-mono text-tertiary select-all">
              {cvss_vector}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
