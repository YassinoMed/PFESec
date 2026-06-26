"use client";

import CouncilPanel from "@/components/council/CouncilPanel";
import { PageHeader } from "@/components/layout/PageHeader";
import { UsersRound } from "lucide-react";

export default function CouncilPage() {
  return (
    <div>
      <PageHeader
        icon={<UsersRound size={22} />}
        title="AI Security Council"
        description="Master AI, discussion multi-experts, validation croisée, fact checking local et consensus explicable."
      />
      <CouncilPanel />
    </div>
  );
}
