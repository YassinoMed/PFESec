"use client";

import { cn } from "@/lib/utils";

interface GlowBadgeProps {
  label: string;
  color?: string;
  pulse?: boolean;
  className?: string;
}

export function GlowBadge({ label, color = "#60a5fa", pulse = false, className }: GlowBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase border",
        pulse && "animate-pulse-slow",
        className
      )}
      style={{
        color,
        borderColor: `${color}44`,
        backgroundColor: `${color}15`,
        boxShadow: `0 0 12px ${color}30`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
      />
      {label}
    </span>
  );
}
