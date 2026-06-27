"use client";

import React from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { Shield, ShieldAlert, Sparkles } from "lucide-react";

interface AttackPhase {
  phase_id: string;
  phase_name: string;
  techniques: string[];
  evidence: string[];
  confidence: number;
}

interface AttackTimelineProps {
  timeline: {
    attack_vector: string;
    entry_point: string;
    phases: AttackPhase[];
    iocs_extracted: Array<{ type: string; value: string; confidence: number }>;
    estimated_impact: string;
  };
}

export default function AttackTimeline({ timeline }: AttackTimelineProps) {
  const { attack_vector, entry_point, phases, iocs_extracted, estimated_impact } = timeline;

  return (
    <Card className="flex flex-col h-full">
      <CardHeader
        title="Reconstruction de l'Attaque"
        subtitle="Chronologie des tactiques de l'adversaire mappées sur MITRE ATT&CK"
        icon={<ShieldAlert size={18} className="text-block" />}
      />

      <div className="space-y-4 p-4 flex-1">
        {/* Core attack details header */}
        <div className="grid grid-cols-2 gap-4 rounded-lg bg-white/[0.02] p-3 text-xs border border-white/5">
          <div>
            <span className="text-secondary block">Vecteur principal</span>
            <span className="font-semibold text-[#f0f4ff]">{attack_vector}</span>
          </div>
          <div>
            <span className="text-secondary block">Point d'entrée identifié</span>
            <span className="font-semibold text-[#f0f4ff] truncate block" title={entry_point}>
              {entry_point}
            </span>
          </div>
        </div>

        {/* Phase List */}
        <div className="relative border-l border-white/10 ml-3 pl-6 space-y-6 py-2">
          {phases.map((phase, idx) => {
            const isCritical = phase.confidence > 0.7;
            return (
              <div key={phase.phase_id} className="relative">
                {/* Timeline node marker */}
                <div
                  className={cn(
                    "absolute -left-[31px] top-1 flex h-4 w-4 items-center justify-center rounded-full border bg-black transition-all",
                    isCritical ? "border-block shadow-[0_0_8px_rgba(239,68,68,0.4)]" : "border-primary"
                  )}
                >
                  <div className={cn("h-1.5 w-1.5 rounded-full", isCritical ? "bg-block" : "bg-primary")} />
                </div>

                {/* Phase Info */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold text-[#f0f4ff]">
                      {phase.phase_id} — {phase.phase_name}
                    </span>
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[9px] font-semibold font-mono",
                        isCritical ? "bg-block/10 text-block" : "bg-primary/10 text-primary"
                      )}
                    >
                      Confiance: {(phase.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* Techniques list */}
                  {phase.techniques && phase.techniques.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {phase.techniques.map((tech) => (
                        <span key={tech} className="rounded bg-white/[0.04] border border-white/5 px-2 py-0.5 text-[10px] text-secondary font-mono">
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Evidence list */}
                  {phase.evidence && phase.evidence.length > 0 && (
                    <p className="text-[11px] text-tertiary leading-relaxed mt-1">
                      Preuves: {phase.evidence.join("; ")}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {phases.length === 0 && (
            <div className="text-center py-6 text-xs text-secondary">
              Aucune phase suspecte identifiée pour cette requête.
            </div>
          )}
        </div>

        {/* IOC List Section if present */}
        {iocs_extracted && iocs_extracted.length > 0 && (
          <div className="mt-4 pt-3 border-t border-white/5 space-y-2">
            <span className="text-xs font-semibold text-[#f0f4ff] block">Indicateurs de compromission (IOC)</span>
            <div className="max-h-24 overflow-y-auto space-y-1.5 pr-1">
              {iocs_extracted.map((ioc, index) => (
                <div key={`${ioc.value}-${index}`} className="flex items-center justify-between rounded bg-white/[0.02] border border-white/5 px-2.5 py-1 text-xs">
                  <span className="font-mono text-secondary truncate max-w-[220px]" title={ioc.value}>
                    {ioc.value}
                  </span>
                  <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] text-primary uppercase tracking-wide">
                    {ioc.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reconstructed impact summary */}
        <div className="mt-4 pt-3 border-t border-white/5">
          <div className="flex items-center gap-2 rounded bg-block/5 border border-block/10 px-3 py-2 text-xs">
            <Shield className="text-block shrink-0" size={14} />
            <span className="text-secondary leading-relaxed">
              <strong className="text-block">Impact Estimé:</strong> {estimated_impact}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
