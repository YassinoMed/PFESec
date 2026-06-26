import { cn } from "@/lib/utils";
import type { ModelType } from "@/types/api";

interface ModelBadgeProps {
  type: ModelType;
  className?: string;
}

const map: Record<ModelType, { label: string; color: string }> = {
  bert: { label: "BERT", color: "text-bert border-bert/40 bg-bert/10" },
  lora: { label: "LoRA", color: "text-lora border-lora/40 bg-lora/10" },
  llm: { label: "LLM", color: "text-llm border-llm/40 bg-llm/10" },
};

/** Badge de type de modèle (BERT / LoRA / LLM). */
export function ModelBadge({ type, className }: ModelBadgeProps) {
  const m = map[type];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase",
        m.color,
        className
      )}
    >
      {m.label}
    </span>
  );
}
