"use client";

import { cn } from "@/lib/utils";
import { AlertTriangle } from "lucide-react";

/** Bandeau affiché quand le backend est en mode démo. */
export function DemoBanner({ demo }: { demo: boolean }) {
  if (!demo) return null;
  return (
    <div className="mb-5 flex items-center gap-3 rounded-xl border border-warn/30 bg-warn/[0.07] px-4 py-2.5 text-sm">
      <AlertTriangle size={16} className="shrink-0 text-warn" />
      <span className="text-warn/90">
        <strong className="font-semibold">Mode démo</strong> — le serveur
        d'inférence n'est pas détecté. Les données affichées sont simulées.
        Lancez <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-xs">python inference_server.py</code> pour des données réelles.
      </span>
    </div>
  );
}

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon,
  action,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("mb-6 flex items-end justify-between gap-4", className)}>
      <div className="flex items-start gap-3">
        {icon && (
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary">
            {icon}
          </div>
        )}
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight text-[#f0f4ff]">
            {title}
          </h2>
          {description && (
            <p className="mt-1 text-sm text-secondary">{description}</p>
          )}
        </div>
      </div>
      {action}
    </div>
  );
}
