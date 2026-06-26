import { cn } from "@/lib/utils";
import type { ReactNode, HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
  glow?: boolean;
}

/** Carte glassmorphism de base. */
export function Card({
  children,
  className,
  hover = false,
  glow = false,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "glass p-5 shadow-glass",
        hover && "transition-all duration-300 hover:border-white/[0.14] hover:bg-white/[0.05]",
        glow && "shadow-glow",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function CardHeader({
  title,
  subtitle,
  icon,
  action,
  className,
}: CardHeaderProps) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-3", className)}>
      <div className="flex items-start gap-3">
        {icon && (
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-primary">
            {icon}
          </div>
        )}
        <div>
          <h3 className="font-display text-sm font-semibold tracking-wide text-[#f0f4ff]">
            {title}
          </h3>
          {subtitle && (
            <p className="mt-0.5 text-xs text-secondary">{subtitle}</p>
          )}
        </div>
      </div>
      {action}
    </div>
  );
}
