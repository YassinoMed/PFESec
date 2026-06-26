import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  /** Couleur d'accent sémantique. */
  tone?: "primary" | "accept" | "block" | "warn" | "info" | "neutral";
  sub?: string;
  className?: string;
}

const toneMap = {
  primary: "text-primary",
  accept: "text-accept",
  block: "text-block",
  warn: "text-warn",
  info: "text-info",
  neutral: "text-[#f0f4ff]",
};

const toneBg = {
  primary: "border-primary/30 bg-primary/5",
  accept: "border-accept/30 bg-accept/5",
  block: "border-block/30 bg-block/5",
  warn: "border-warn/30 bg-warn/5",
  info: "border-info/30 bg-info/5",
  neutral: "border-white/10 bg-white/[0.02]",
};

/** Carte KPI compacte pour les tableaux de bord. */
export function StatCard({
  label,
  value,
  icon,
  tone = "neutral",
  sub,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "glass flex flex-col gap-2 rounded-xl border p-4",
        toneBg[tone],
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-secondary">
          {label}
        </span>
        {icon && <span className={cn("opacity-80", toneMap[tone])}>{icon}</span>}
      </div>
      <div className={cn("font-display text-2xl font-bold tabular-nums", toneMap[tone])}>
        {value}
      </div>
      {sub && <span className="text-[11px] text-tertiary">{sub}</span>}
    </div>
  );
}
