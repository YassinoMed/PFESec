import { cn, threatTier } from "@/lib/utils";

interface ThreatBarProps {
  /** 0..100 */
  score: number;
  showLabel?: boolean;
  className?: string;
}

/** Barre de score de menace à 3 niveaux (bas/moyen/élevé). */
export function ThreatBar({ score, showLabel = true, className }: ThreatBarProps) {
  const tier = threatTier(score);
  const tierColor = {
    low: "from-info to-accept",
    medium: "from-warn to-warn",
    high: "from-warn to-block",
  }[tier];

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="mb-1 flex items-center justify-between text-[11px]">
          <span className="uppercase tracking-wider text-secondary">
            Score de menace
          </span>
          <span
            className={cn(
              "font-mono font-semibold tabular-nums",
              tier === "high"
                ? "text-block"
                : tier === "medium"
                ? "text-warn"
                : "text-accept"
            )}
          >
            {score.toFixed(1)}/100
          </span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
        <div
          className={cn("h-full rounded-full bg-gradient-to-r transition-all duration-700", tierColor)}
          style={{ width: `${Math.max(2, Math.min(100, score))}%` }}
        />
      </div>
    </div>
  );
}
