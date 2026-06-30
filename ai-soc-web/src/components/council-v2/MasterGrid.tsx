"use client";

import type { MasterState } from "@/types/council";
import { MasterCard } from "./MasterCard";
import { MASTERS } from "@/lib/councilApi";

interface MasterGridProps {
  masterStates: Record<string, MasterState>;
  onMasterClick?: (masterId: string) => void;
}

export function MasterGrid({ masterStates, onMasterClick }: MasterGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {MASTERS.map(def => {
        const state = masterStates[def.id];
        if (!state) return null;
        return (
          <MasterCard
            key={def.id}
            master={state}
            onClick={() => onMasterClick?.(def.id)}
          />
        );
      })}
    </div>
  );
}
