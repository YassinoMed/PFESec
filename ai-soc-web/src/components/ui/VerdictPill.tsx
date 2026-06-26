import { cn } from "@/lib/utils";

type Variant = "accept" | "block" | "warn" | "neutral";

const variants: Record<Variant, string> = {
  accept: "border-accept/40 bg-accept/10 text-accept",
  block: "border-block/40 bg-block/10 text-block",
  warn: "border-warn/40 bg-warn/10 text-warn",
  neutral: "border-white/15 bg-white/5 text-[#cbd5e1]",
};

interface VerdictPillProps {
  verdict: string;
  size?: "sm" | "md";
  className?: string;
}

/** Pilule de verdict ACCEPT / BLOCK / UNCERTAIN avec halo. */
export function VerdictPill({ verdict, size = "md", className }: VerdictPillProps) {
  const v = verdict.toUpperCase();
  let variant: Variant = "neutral";
  let icon = "•";

  if (v === "ACCEPT" || v === "SAFE") {
    variant = "accept";
    icon = "✓";
  } else if (v === "BLOCK") {
    variant = "block";
    icon = "✕";
  } else if (v === "UNCERTAIN" || v === "UNKNOWN") {
    variant = "warn";
    icon = "?";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-display font-semibold uppercase tracking-wide",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-3 py-1 text-xs",
        variants[variant],
        className
      )}
    >
      <span aria-hidden>{icon}</span>
      {v}
    </span>
  );
}
