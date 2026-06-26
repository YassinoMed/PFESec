"use client";

import { cn } from "@/lib/utils";

interface RadialGaugeProps {
  /** 0..100 */
  value: number;
  label?: string;
  sublabel?: string;
  size?: number;
  tone?: "primary" | "accept" | "warn" | "block";
  className?: string;
}

const toneStroke = {
  primary: "hsl(220, 95%, 62%)",
  accept: "hsl(142, 72%, 46%)",
  warn: "hsl(38, 92%, 55%)",
  block: "hsl(0, 82%, 58%)",
};

/** Jauge circulaire SVG pour VRAM / accuracy / etc. */
export function RadialGauge({
  value,
  label,
  sublabel,
  size = 120,
  tone = "primary",
  className,
}: RadialGaugeProps) {
  const stroke = 8;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = c - (clamped / 100) * c;
  const color = toneStroke[tone];

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)",
              filter: `drop-shadow(0 0 6px ${color})`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-xl font-bold tabular-nums text-[#f0f4ff]">
            {clamped.toFixed(0)}
            <span className="text-sm text-secondary">%</span>
          </span>
          {sublabel && (
            <span className="text-[10px] uppercase tracking-wider text-tertiary">
              {sublabel}
            </span>
          )}
        </div>
      </div>
      {label && (
        <span className="mt-2 text-xs font-medium text-secondary">{label}</span>
      )}
    </div>
  );
}
