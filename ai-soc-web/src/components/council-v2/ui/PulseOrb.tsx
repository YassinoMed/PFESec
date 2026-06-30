"use client";

interface PulseOrbProps {
  color?: string;
  size?: number;
  active?: boolean;
  className?: string;
}

export function PulseOrb({ color = "#60a5fa", size = 12, active = true, className }: PulseOrbProps) {
  return (
    <span className={`relative inline-flex ${className || ""}`} style={{ width: size, height: size }}>
      {active && (
        <span
          className="absolute inset-0 rounded-full animate-ping"
          style={{ backgroundColor: `${color}40` }}
        />
      )}
      <span
        className="relative inline-flex rounded-full w-full h-full"
        style={{
          backgroundColor: color,
          boxShadow: active ? `0 0 10px ${color}80` : "none",
        }}
      />
    </span>
  );
}
