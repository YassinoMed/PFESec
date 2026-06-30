/**
 * hooks/useCouncilWebSocket.ts — Real-time WebSocket hook for the Council V2 dashboard.
 *
 * Connects to the backend discussion journal WebSocket (port 8090)
 * and dispatches events into typed state buckets.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  CoordinatorPhase,
  CouncilEvent,
  CouncilEventType,
  ConflictItem,
  DiscussionMessage,
  EvidenceItem,
  MasterState,
  TimelineEntry,
} from "@/types/council";
import { resolveAgent, MASTERS } from "@/lib/councilApi";

let msgIdCounter = 0;
function nextId() {
  return `evt-${++msgIdCounter}-${Date.now()}`;
}

function eventToRole(type: CouncilEventType): DiscussionMessage["role"] {
  switch (type) {
    case "coordinator": return "coordinator";
    case "master_activation":
    case "master_planning":
    case "master_completed":
    case "discussion": return "master";
    case "expert_query":
    case "expert_response": return "expert";
    case "consensus":
    case "consensus_final":
    case "report": return "engine";
    default: return "engine";
  }
}

const initMasters = (): Record<string, MasterState> => {
  const m: Record<string, MasterState> = {};
  for (const def of MASTERS) {
    m[def.id] = {
      id: def.id,
      name: def.name,
      emoji: def.emoji,
      color: def.color,
      phase: "idle",
      confidence: 0,
      score: 0,
      verdict: "",
      elapsed_ms: 0,
      experts_active: 0,
      experts_total: 0,
      models_used: [],
      evidence_count: 0,
      progress: 0,
    };
  }
  return m;
};

export interface CouncilWsState {
  isConnected: boolean;
  coordinatorPhase: CoordinatorPhase;
  masterStates: Record<string, MasterState>;
  discussions: DiscussionMessage[];
  evidences: EvidenceItem[];
  conflicts: ConflictItem[];
  timeline: TimelineEntry[];
  eventCount: number;
}

export function useCouncilWebSocket(wsUrl: string, active: boolean) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [coordinatorPhase, setCoordinatorPhase] = useState<CoordinatorPhase>("idle");
  const [masterStates, setMasterStates] = useState<Record<string, MasterState>>(initMasters);
  const [discussions, setDiscussions] = useState<DiscussionMessage[]>([]);
  const [evidences, setEvidences] = useState<EvidenceItem[]>([]);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [eventCount, setEventCount] = useState(0);
  const [events, setEvents] = useState<CouncilEvent[]>([]);

  const reset = useCallback(() => {
    setCoordinatorPhase("idle");
    setMasterStates(initMasters());
    setDiscussions([]);
    setEvidences([]);
    setConflicts([]);
    setTimeline([]);
    setEventCount(0);
    setEvents([]);
    msgIdCounter = 0;
  }, []);

  const handleEvent = useCallback((evt: CouncilEvent) => {
    setEventCount(c => c + 1);
    setEvents(prev => [...prev, evt]);
    const agent = resolveAgent(evt.source);
    const targetAgent = evt.target ? resolveAgent(evt.target) : null;

    // ── Timeline entry for every event ──
    setTimeline(prev => [
      ...prev,
      {
        id: nextId(),
        timestamp: evt.timestamp,
        agent: agent.name,
        agentEmoji: agent.emoji,
        action: evt.message,
        duration_ms: evt.elapsed_ms,
        phase: evt.type,
        eventType: evt.type,
      },
    ]);

    // ── Discussion message ──
    setDiscussions(prev => {
      // Deduplicate exact content
      if (prev.length > 0 && prev[prev.length - 1].content === evt.message) return prev;
      return [
        ...prev,
        {
          id: nextId(),
          speaker: agent.name,
          speakerEmoji: agent.emoji,
          role: eventToRole(evt.type),
          target: targetAgent?.name,
          content: evt.message,
          timestamp: evt.timestamp,
          eventType: evt.type,
          elapsed_ms: evt.elapsed_ms,
        },
      ];
    });

    // ── Coordinator phase ──
    if (evt.type === "coordinator") {
      setCoordinatorPhase("planning");
    }

    // ── Master states ──
    if (evt.type === "master_activation") {
      const masterId = evt.source.toLowerCase().trim();
      setCoordinatorPhase("dispatching");
      setMasterStates(prev => {
        const m = prev[masterId];
        if (!m) return prev;
        return { ...prev, [masterId]: { ...m, phase: "activated", progress: 10 } };
      });
    }

    if (evt.type === "expert_query") {
      const masterId = evt.source.toLowerCase().trim();
      setMasterStates(prev => {
        const m = prev[masterId];
        if (!m) return prev;
        return {
          ...prev,
          [masterId]: {
            ...m,
            phase: "querying_experts",
            experts_active: m.experts_active + 1,
            experts_total: m.experts_total + 1,
            progress: Math.min(m.progress + 8, 60),
          },
        };
      });
    }

    if (evt.type === "expert_response") {
      // source is the expert, target is the master
      const masterId = (evt.target || "").toLowerCase().trim();
      setMasterStates(prev => {
        const m = prev[masterId];
        if (!m) return prev;
        return {
          ...prev,
          [masterId]: {
            ...m,
            phase: "analyzing",
            experts_active: Math.max(0, m.experts_active - 1),
            evidence_count: m.evidence_count + 1,
            progress: Math.min(m.progress + 5, 75),
          },
        };
      });

      // ── Evidence item ──
      setEvidences(prev => [
        ...prev,
        {
          id: nextId(),
          source: agent.name,
          type: "expert",
          content: evt.message,
          confidence: 0,
          timestamp: evt.timestamp,
        },
      ]);
    }

    if (evt.type === "discussion") {
      setCoordinatorPhase("waiting");
      const masterId = evt.source.toLowerCase().trim();
      setMasterStates(prev => {
        const m = prev[masterId];
        if (!m) return prev;
        return { ...prev, [masterId]: { ...m, phase: "debating", progress: Math.min(m.progress + 3, 85) } };
      });
    }

    if (evt.type === "master_completed") {
      const masterId = evt.source.toLowerCase().trim();
      const scoreMatch = evt.message.match(/(\d+(?:\.\d+)?)%/);
      const score = scoreMatch ? parseFloat(scoreMatch[1]) : 0;
      setMasterStates(prev => {
        const m = prev[masterId];
        if (!m) return prev;
        return { ...prev, [masterId]: { ...m, phase: "completed", score, confidence: score, progress: 100, elapsed_ms: evt.elapsed_ms, verdict: evt.message } };
      });
    }

    // ── Contradictions ──
    if (evt.type === "contradiction") {
      setConflicts(prev => [
        ...prev,
        {
          id: nextId(),
          left: evt.source,
          right: evt.target || "",
          leftScore: 0,
          rightScore: 0,
          detail: evt.message,
          status: "detected",
          timestamp: evt.timestamp,
        },
      ]);
    }

    if (evt.type === "contradiction_resolved") {
      setConflicts(prev =>
        prev.map(c =>
          c.left === evt.source && c.right === (evt.target || "")
            ? { ...c, status: "resolved" as const, resolution: evt.message }
            : c
        )
      );
    }

    // ── Consensus ──
    if (evt.type === "consensus") {
      setCoordinatorPhase("consensus");
    }
    if (evt.type === "consensus_final") {
      setCoordinatorPhase("final_decision");
    }

    // ── Report ──
    if (evt.type === "report") {
      setCoordinatorPhase("final_decision");
    }
  }, []);

  // ── WebSocket connection lifecycle ──
  useEffect(() => {
    if (!active) return;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => ws.close();

    ws.onmessage = (event) => {
      try {
        const entry = JSON.parse(event.data) as CouncilEvent;
        handleEvent(entry);
      } catch {
        // ignore malformed
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
      setIsConnected(false);
    };
  }, [wsUrl, active, handleEvent]);

  // ── Wait-for-open utility ──
  const waitForOpen = useCallback((): Promise<void> => {
    return new Promise((resolve) => {
      const ws = wsRef.current;
      if (!ws) { resolve(); return; }
      if (ws.readyState === WebSocket.OPEN) { resolve(); return; }
      ws.addEventListener("open", () => resolve(), { once: true });
      ws.addEventListener("error", () => resolve(), { once: true });
    });
  }, []);

  return {
    isConnected,
    coordinatorPhase,
    masterStates,
    discussions,
    evidences,
    conflicts,
    timeline,
    eventCount,
    events,
    reset,
    waitForOpen,
  };
}
