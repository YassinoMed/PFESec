"use client";

import React, { useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { Shield, ShieldAlert, CheckSquare, Clock } from "lucide-react";

interface ResponseAction {
  phase: string;
  priority: number;
  action: string;
  description: string;
  responsible: string;
  estimated_time: string;
  automated: boolean;
}

interface ResponsePlanProps {
  plan: {
    incident_type: string;
    containment: ResponseAction[];
    eradication: ResponseAction[];
    recovery: ResponseAction[];
    prevention: ResponseAction[];
    monitoring: string[];
    escalation_required: boolean;
    estimated_resolution_time: string;
  };
}

type TabType = "containment" | "eradication" | "recovery" | "prevention" | "monitoring";

export default function ResponsePlanCards({ plan }: ResponsePlanProps) {
  const [activeTab, setActiveTab] = useState<TabType>("containment");
  const { incident_type, containment, eradication, recovery, prevention, monitoring, escalation_required, estimated_resolution_time } = plan;

  const tabs: Array<{ id: TabType; label: string; count?: number }> = [
    { id: "containment", label: "Confinement", count: containment.length },
    { id: "eradication", label: "Éradication", count: eradication.length },
    { id: "recovery", label: "Récupération", count: recovery.length },
    { id: "prevention", label: "Prévention", count: prevention.length },
    { id: "monitoring", label: "Surveillance", count: monitoring.length },
  ];

  // Helper to get active list
  const getActiveActions = (): ResponseAction[] => {
    if (activeTab === "containment") return containment;
    if (activeTab === "eradication") return eradication;
    if (activeTab === "recovery") return recovery;
    if (activeTab === "prevention") return prevention;
    return [];
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader
        title="Plan de Réponse Incident (IR Playbook)"
        subtitle={`Procédure opérationnelle pour incident: ${incident_type}`}
        icon={<CheckSquare size={18} className="text-accept" />}
      />

      <div className="space-y-4 p-4 flex-1">
        {/* Playbook Header Details */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-white/[0.02] p-3 text-xs border border-white/5">
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-secondary" />
            <span className="text-secondary">Temps de résolution:</span>
            <span className="font-semibold text-[#f0f4ff]">{estimated_resolution_time}</span>
          </div>
          {escalation_required && (
            <div className="flex items-center gap-1.5 rounded bg-block/15 px-2 py-0.5 border border-block/20 text-block text-[10px] font-bold uppercase tracking-wide">
              <ShieldAlert size={12} />
              Escalade Requise
            </div>
          )}
        </div>

        {/* Tab switcher */}
        <div className="flex flex-wrap gap-1 border-b border-white/5 pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-200",
                activeTab === tab.id
                  ? "bg-primary text-white shadow-glow"
                  : "text-secondary hover:bg-white/[0.02] hover:text-[#f0f4ff]"
              )}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1.5 rounded-full bg-black/40 px-1.5 py-0.2 text-[10px] font-mono">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Active list display */}
        <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
          {activeTab === "monitoring" ? (
            <div className="space-y-2">
              {monitoring.map((mon, index) => (
                <div key={index} className="flex gap-2.5 rounded-lg bg-white/[0.01] border border-white/5 p-3 text-xs">
                  <span className="text-primary mt-0.5 font-bold font-mono">#{index + 1}</span>
                  <p className="text-secondary leading-relaxed">{mon}</p>
                </div>
              ))}
              {monitoring.length === 0 && (
                <p className="text-xs text-secondary text-center py-4">Aucune action de surveillance identifiée.</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {getActiveActions().map((act, index) => (
                <div key={index} className="rounded-lg bg-white/[0.01] border border-white/5 p-3.5 space-y-2 relative">
                  {/* Card header */}
                  <div className="flex items-start justify-between gap-3 text-xs">
                    <span className="font-semibold text-[#f0f4ff]">
                      {index + 1}. {act.action}
                    </span>
                    {act.automated && (
                      <span className="rounded bg-accept/15 border border-accept/20 px-1.5 py-0.5 text-[9px] font-bold text-accept uppercase tracking-wider">
                        Auto
                      </span>
                    )}
                  </div>

                  {/* Card Description */}
                  <p className="text-xs text-secondary leading-relaxed">
                    {act.description}
                  </p>

                  {/* Card Footer tags */}
                  <div className="flex flex-wrap items-center gap-4 text-[10px] text-tertiary pt-1">
                    <div>
                      <span className="text-tertiary mr-1">Acteur:</span>
                      <span className="font-medium text-secondary">{act.responsible}</span>
                    </div>
                    <div>
                      <span className="text-tertiary mr-1">Temps:</span>
                      <span className="font-medium text-secondary">{act.estimated_time}</span>
                    </div>
                  </div>
                </div>
              ))}
              {getActiveActions().length === 0 && (
                <p className="text-xs text-secondary text-center py-4">Aucune action recommandée pour cette phase.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
