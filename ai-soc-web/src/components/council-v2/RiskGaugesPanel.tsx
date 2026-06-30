"use client";

import React from "react";
import type { RiskGauges } from "@/types/council";
import { AnimatedGauge } from "./ui/AnimatedGauge";

interface RiskGaugesPanelProps {
  riskData: RiskGauges | null;
}

export function RiskGaugesPanel({ riskData }: RiskGaugesPanelProps) {
  // Default fallbacks for a nice visual state before/during run
  const risk = riskData?.risk_score ?? 0;
  const impact = riskData?.impact ?? 0;
  const likelihood = riskData?.likelihood ?? 0;
  const priority = riskData?.priority ?? 0;
  const business = riskData?.business_impact ?? 0;
  const cvss = riskData?.cvss ?? 0; // scaled out of 10 in data, we show CVSS out of 10

  const getSeverityColor = (val: number, max = 100) => {
    const pct = val / max;
    if (pct >= 0.75) return "#f87171"; // Red
    if (pct >= 0.45) return "#fbbf24"; // Amber
    return "#34d399"; // Green
  };

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-4 flex items-center gap-1.5">
        <span>📊</span> Risk & Criticality Assessment
      </h3>

      <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
        {/* Risk Score */}
        <div className="flex flex-col items-center">
          <AnimatedGauge
            value={risk}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(risk)}
            label="Risk"
          />
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Risk Score</span>
        </div>

        {/* Impact */}
        <div className="flex flex-col items-center">
          <AnimatedGauge
            value={impact}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(impact)}
            label="Impact"
          />
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Tech Impact</span>
        </div>

        {/* Likelihood */}
        <div className="flex flex-col items-center">
          <AnimatedGauge
            value={likelihood}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(likelihood)}
            label="L'hood"
          />
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Likelihood</span>
        </div>

        {/* Priority */}
        <div className="flex flex-col items-center">
          <AnimatedGauge
            value={priority}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(priority)}
            label="Prio"
          />
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Priority</span>
        </div>

        {/* Business Impact */}
        <div className="flex flex-col items-center">
          <AnimatedGauge
            value={business}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(business)}
            label="Biz"
          />
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Biz Impact</span>
        </div>

        {/* CVSS */}
        <div className="flex flex-col items-center relative">
          {/* CVSS is out of 10, so multiply by 10 for percentage render */}
          <AnimatedGauge
            value={cvss * 10}
            size={75}
            strokeWidth={5}
            color={getSeverityColor(cvss, 10)}
            label="CVSS"
          />
          <div className="absolute top-[22px] left-0 right-0 text-center pointer-events-none">
            <span className="text-xs font-bold text-white block mt-1.5 tabular-nums">
              {cvss > 0 ? cvss.toFixed(1) : "—"}
            </span>
          </div>
          <span className="text-[10px] text-white/40 mt-1 uppercase text-center font-medium">Base CVSS</span>
        </div>
      </div>
    </div>
  );
}
