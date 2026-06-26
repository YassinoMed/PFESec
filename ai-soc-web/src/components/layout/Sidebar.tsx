"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Crosshair,
  FlaskConical,
  Boxes,
  Cpu,
  Scale,
  ShieldCheck,
  Brain,
  Layers,
  TrendingUp,
  UsersRound,
} from "lucide-react";

const nav = [
  { href: "/", label: "Command Center", icon: LayoutDashboard },
  { href: "/analyze", label: "Threat Analysis", icon: Crosshair },
  { href: "/orchestrate", label: "AI Orchestrator", icon: Brain },
  { href: "/council", label: "Security Council", icon: UsersRound },
  { href: "/consensus", label: "Consensus IA", icon: TrendingUp },
  { href: "/models", label: "AI Models", icon: Layers },
  { href: "/sandbox", label: "Sandbox", icon: FlaskConical },
  { href: "/batch", label: "Batch Evaluation", icon: Boxes },
  { href: "/gpu", label: "GPU Observatory", icon: Cpu },
  { href: "/governance", label: "AI Governance", icon: Scale },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-white/[0.06] bg-base-900/60 backdrop-blur-xl lg:flex">
      {/* Branding */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary shadow-glow">
          <ShieldCheck size={22} />
        </div>
        <div>
          <h1 className="font-display text-sm font-bold leading-tight text-[#f0f4ff]">
            AI-SOC
          </h1>
          <p className="text-[10px] uppercase tracking-[0.2em] text-tertiary">
            SecureRAG Hub
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {nav.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "border border-primary/30 bg-primary/10 text-primary shadow-glow"
                  : "border border-transparent text-secondary hover:bg-white/[0.04] hover:text-[#f0f4ff]"
              )}
            >
              <Icon
                size={17}
                className={cn(active ? "text-primary" : "text-tertiary group-hover:text-secondary")}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer version */}
      <div className="border-t border-white/[0.06] px-5 py-4">
        <p className="font-mono text-[10px] text-tertiary">
          v0.1.0 · multi-model inference
        </p>
      </div>
    </aside>
  );
}
