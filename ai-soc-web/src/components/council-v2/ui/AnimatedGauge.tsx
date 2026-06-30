"use client";

import { useEffect, useRef } from "react";

interface AnimatedGaugeProps {
  value: number;      // 0-100
  size?: number;       // px
  strokeWidth?: number;
  color?: string;
  bgColor?: string;
  label?: string;
  sublabel?: string;
  className?: string;
}

export function AnimatedGauge({
  value,
  size = 120,
  strokeWidth = 8,
  color = "#60a5fa",
  bgColor = "rgba(255,255,255,0.06)",
  label,
  sublabel,
  className,
}: AnimatedGaugeProps) {
  const circleRef = useRef<SVGCircleElement>(null);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference - (clamped / 100) * circumference;

  useEffect(() => {
    const el = circleRef.current;
    if (!el) return;
    el.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)";
    el.style.strokeDashoffset = `${offset}`;
  }, [offset]);

  return (
    <div className={`flex flex-col items-center ${className || ""}`}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={bgColor}
          strokeWidth={strokeWidth}
        />
        {/* Animated value arc */}
        <circle
          ref={circleRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          style={{
            filter: `drop-shadow(0 0 6px ${color}60)`,
          }}
        />
      </svg>
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span className="text-xl font-bold" style={{ color }}>
          {clamped.toFixed(0)}%
        </span>
        {label && (
          <span className="text-[10px] font-medium text-white/50 uppercase tracking-wider mt-0.5">
            {label}
          </span>
        )}
      </div>
      {sublabel && (
        <span className="text-[11px] text-white/40 mt-1.5">{sublabel}</span>
      )}
    </div>
  );
}
