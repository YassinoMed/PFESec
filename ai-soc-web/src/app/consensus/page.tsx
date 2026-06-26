"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import ConsensusPanel from "@/components/consensus/ConsensusPanel";
import { Brain } from "lucide-react";

export default function ConsensusPage() {
  return (
    <div>
      <PageHeader
        icon={<Brain size={22} />}
        title="Consensus IA"
        description="Moteur de consensus et scoring multi-modèles — score pondéré, filtrage 80%, classement."
      />
      <ConsensusPanel />
    </div>
  );
}
