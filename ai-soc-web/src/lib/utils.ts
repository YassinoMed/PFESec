import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Fusionne classes Tailwind proprement (gère les conflits). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Niveau de menace à partir d'un score 0..100. */
export function threatTier(score: number): "low" | "medium" | "high" {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

/** Couleur associée à un verdict. */
export function verdictColor(
  verdict: string
): "accept" | "block" | "warn" | "neutral" {
  const v = verdict.toUpperCase();
  if (v === "ACCEPT" || v === "SAFE") return "accept";
  if (v === "BLOCK") return "block";
  if (v === "UNCERTAIN" || v === "UNKNOWN") return "warn";
  return "neutral";
}
