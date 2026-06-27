"use client";

import {
  BrainCircuit,
  Radio,
  LineChart,
  Network,
  ScrollText,
  Cpu,
  LifeBuoy,
  Plus,
  Bot,
} from "lucide-react";

export type SentinelView =
  | "orchestrator"
  | "stream"
  | "intelligence"
  | "network"
  | "journals";

interface SentinelSidebarProps {
  active: SentinelView;
  onSelect: (view: SentinelView) => void;
}

const NAV: { id: SentinelView; label: string; icon: typeof BrainCircuit }[] = [
  { id: "orchestrator", label: "Orchestrator", icon: BrainCircuit },
  { id: "stream", label: "Live Stream", icon: Radio },
  { id: "intelligence", label: "Intelligence", icon: LineChart },
  { id: "network", label: "Network", icon: Network },
  { id: "journals", label: "Journals", icon: ScrollText },
];

export function SentinelSidebar({ active, onSelect }: SentinelSidebarProps) {
  return (
    <nav
      className="fixed bottom-0 left-0 top-16 z-40 hidden w-64 flex-col border-r py-4 lg:flex"
      style={{
        backgroundColor: "rgba(18, 19, 28, 0.95)",
        backdropFilter: "blur(16px)",
        borderColor: "rgba(60, 73, 78, 0.3)",
      }}
    >
      {/* Profil opérateur */}
      <div className="mb-8 px-5">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-full border"
            style={{
              backgroundColor: "var(--stitch-surface-bright)",
              borderColor: "rgba(0, 209, 255, 0.3)",
              color: "var(--stitch-primary)",
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <div
              className="text-base font-semibold"
              style={{ color: "var(--stitch-on-surface)" }}
            >
              OP-721
            </div>
            <div
              className="sentinel-caps"
              style={{ color: "var(--stitch-on-surface-variant)" }}
            >
              Level 5 Clearance
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex flex-1 flex-col gap-2 px-3">
        {NAV.map(({ id, label, icon: Icon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className="flex items-center gap-3 rounded-lg px-4 py-3 transition-all"
              style={{
                backgroundColor: isActive
                  ? "rgba(87, 27, 193, 0.2)"
                  : "transparent",
                color: isActive
                  ? "var(--stitch-primary)"
                  : "var(--stitch-on-surface-variant)",
                borderRight: isActive
                  ? "4px solid var(--stitch-primary)"
                  : "4px solid transparent",
              }}
            >
              <Icon size={18} />
              <span className="sentinel-caps">{label}</span>
            </button>
          );
        })}
      </div>

      {/* New mission */}
      <div className="mt-auto px-5">
        <button
          className="stitch-glow-active flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 transition-all hover:brightness-110"
          style={{
            color: "var(--stitch-on-primary-container, #00566a)",
            backgroundColor: "var(--stitch-primary-container)",
          }}
        >
          <Plus size={16} />
          <span className="sentinel-caps">New Mission</span>
        </button>
      </div>

      {/* Footer */}
      <div className="mt-4 flex flex-col gap-2 border-t px-3 pt-4"
        style={{ borderColor: "rgba(60, 73, 78, 0.3)" }}
      >
        <SideFooterItem icon={Cpu} label="System Health" />
        <SideFooterItem icon={LifeBuoy} label="Support" />
      </div>
    </nav>
  );
}

function SideFooterItem({
  icon: Icon,
  label,
}: {
  icon: typeof Cpu;
  label: string;
}) {
  return (
    <button
      className="flex items-center gap-3 rounded-lg px-4 py-2 transition-all hover:bg-white/5"
      style={{ color: "var(--stitch-on-surface-variant)" }}
    >
      <Icon size={18} />
      <span className="sentinel-caps">{label}</span>
    </button>
  );
}
