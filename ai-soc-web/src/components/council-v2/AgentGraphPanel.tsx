"use client";

import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { MasterState } from "@/types/council";
import { MASTERS, resolveAgent } from "@/lib/councilApi";

interface AgentGraphPanelProps {
  masterStates: Record<string, MasterState>;
  coordinatorPhase: string;
}

export function AgentGraphPanel({ masterStates, coordinatorPhase }: AgentGraphPanelProps) {
  const nodes = useMemo<Node[]>(() => {
    const isPlan = coordinatorPhase !== "idle";
    const isDone = coordinatorPhase === "final_decision";

    const list: Node[] = [
      // Coordinator node
      {
        id: "coord",
        position: { x: 350, y: 20 },
        data: { label: "🧠 Global Coordinator" },
        style: {
          background: isPlan ? "rgba(167, 139, 250, 0.15)" : "rgba(255, 255, 255, 0.02)",
          borderColor: isPlan ? "#a78bfa" : "rgba(255, 255, 255, 0.1)",
          color: "#fff",
          fontSize: "11px",
          fontWeight: "bold",
          borderRadius: "8px",
          borderWidth: "1px",
          boxShadow: isPlan ? "0 0 15px rgba(167, 139, 250, 0.3)" : "none",
          width: 160,
        },
      },
    ];

    // Master nodes
    MASTERS.forEach((m, idx) => {
      const active = masterStates[m.id]?.phase !== "idle";
      const done = masterStates[m.id]?.phase === "completed";
      const xPos = 50 + idx * 200;

      list.push({
        id: m.id,
        position: { x: xPos, y: 120 },
        data: { label: `${m.emoji} ${m.name}` },
        style: {
          background: active ? `${m.color}25` : "rgba(255, 255, 255, 0.02)",
          borderColor: active ? m.color : "rgba(255, 255, 255, 0.1)",
          color: "#fff",
          fontSize: "11px",
          fontWeight: "semibold",
          borderRadius: "8px",
          borderWidth: "1px",
          boxShadow: active ? `0 0 15px ${m.color}40` : "none",
          width: 140,
        },
      });
    });

    // Experts layer
    const experts = [
      { id: "threat_intel", name: "📡 Threat Intel", parent: "threat_master", x: 30 },
      { id: "email_expert", name: "📧 Email Expert", parent: "threat_master", x: 130 },
      { id: "soc_analyst", name: "💻 SOC Analyst", parent: "soc_master", x: 230 },
      { id: "mitre_expert", name: "🗺️ MITRE Expert", parent: "soc_master", x: 330 },
      { id: "rag_knowledge", name: "📚 RAG Expert", parent: "rag_master", x: 450 },
      { id: "governance_exp", name: "⚖️ Governance Exp", parent: "governance_master", x: 650 },
    ];

    experts.forEach(exp => {
      const parentActive = masterStates[exp.parent]?.phase !== "idle";
      list.push({
        id: exp.id,
        position: { x: exp.x, y: 220 },
        data: { label: exp.name },
        style: {
          background: parentActive ? "rgba(56, 189, 248, 0.1)" : "rgba(255, 255, 255, 0.01)",
          borderColor: parentActive ? "#38bdf8" : "rgba(255, 255, 255, 0.05)",
          color: "#cbd5e1",
          fontSize: "10px",
          borderRadius: "6px",
          borderWidth: "1px",
          width: 100,
        },
      });
    });

    // Final Decision node
    list.push({
      id: "decision",
      position: { x: 350, y: 320 },
      data: { label: "🏁 Weighted Decision" },
      style: {
        background: isDone ? "rgba(34, 197, 94, 0.15)" : "rgba(255, 255, 255, 0.02)",
        borderColor: isDone ? "#22c55e" : "rgba(255, 255, 255, 0.1)",
        color: "#fff",
        fontSize: "11px",
        fontWeight: "bold",
        borderRadius: "8px",
        borderWidth: "1px",
        boxShadow: isDone ? "0 0 15px rgba(34, 197, 94, 0.3)" : "none",
        width: 160,
      },
    });

    return list;
  }, [masterStates, coordinatorPhase]);

  const edges = useMemo<Edge[]>(() => {
    const list: Edge[] = [];
    const isPlan = coordinatorPhase !== "idle";
    const isDone = coordinatorPhase === "final_decision";

    // Coordinator -> Masters
    MASTERS.forEach(m => {
      const active = masterStates[m.id]?.phase !== "idle";
      list.push({
        id: `coord-${m.id}`,
        source: "coord",
        target: m.id,
        animated: active,
        style: { stroke: active ? m.color : "rgba(255, 255, 255, 0.1)", strokeWidth: active ? 2 : 1 },
      });
    });

    // Masters -> Experts mapping
    const experts = [
      { id: "threat_intel", parent: "threat_master" },
      { id: "email_expert", parent: "threat_master" },
      { id: "soc_analyst", parent: "soc_master" },
      { id: "mitre_expert", parent: "soc_master" },
      { id: "rag_knowledge", parent: "rag_master" },
      { id: "governance_exp", parent: "governance_master" },
    ];

    experts.forEach(exp => {
      const parentActive = masterStates[exp.parent]?.phase !== "idle";
      list.push({
        id: `${exp.parent}-${exp.id}`,
        source: exp.parent,
        target: exp.id,
        animated: parentActive,
        style: { stroke: parentActive ? "#38bdf8" : "rgba(255, 255, 255, 0.1)", strokeWidth: parentActive ? 1.5 : 1 },
      });
    });

    // Experts -> Decision mapping
    experts.forEach(exp => {
      list.push({
        id: `${exp.id}-decision`,
        source: exp.id,
        target: "decision",
        animated: isDone,
        style: { stroke: isDone ? "#22c55e" : "rgba(255, 255, 255, 0.1)", strokeWidth: isDone ? 1.5 : 1 },
      });
    });

    return list;
  }, [masterStates, coordinatorPhase]);

  return (
    <div className="glass rounded-xl p-4 h-[440px] flex flex-col">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <span>🕸️</span> Live Agent Decision Graph
      </h3>
      <div className="flex-1 bg-[#050810]/40 rounded-lg overflow-hidden border border-white/[0.04]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          attributionPosition="bottom-right"
          minZoom={0.5}
          maxZoom={1.5}
        >
          <Background color="#ffffff" gap={16} size={1} style={{ opacity: 0.03 }} />
          <Controls className="bg-[#090d1a]/80 border border-white/[0.1] text-white" />
        </ReactFlow>
      </div>
    </div>
  );
}
