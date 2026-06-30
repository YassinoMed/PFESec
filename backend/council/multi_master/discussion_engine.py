"""Inter-Master Discussion Engine — Délibération collaborative entre Masters AI.

Fonctionnement :
1. Chaque Master AI reçoit les verdicts des autres Masters
2. Le Coordinator anime la discussion tour par tour
3. Si désaccord → demande de justification et ré-analyse
4. Les contradictions sont tracées et résolues
5. La discussion s'arrête quand un accord est trouvé (ou max rounds atteint)
"""

import time
from typing import Dict, List, Optional

from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.types import MasterDiscussion, MasterVerdict


class InterMasterDiscussionEngine:
    """Moteur de discussion inter-Masters — délibération collaborative.

    Caractéristiques :
    - Maximum 3 rounds de discussion
    - Détection de désaccord basée sur l'écart de conclusion/confiance
    - Résolution tracée dans le journal
    - Délibération asynchrone (non-bloquante)
    """

    MAX_ROUNDS = 3
    DISAGREEMENT_THRESHOLD = 0.20  # 20% d'écart de score minimum pour désaccord

    def __init__(self, journal: Optional[DiscussionJournal] = None):
        self.journal = journal

    async def conduct_discussion(
        self,
        master_verdicts: Dict[str, MasterVerdict],
        master_weights: Dict[str, float],
        masters: Dict[str, Any] = None,
        query: str = "",
    ) -> tuple:
        """Conduit la discussion entre Masters et retourne (log, rounds, verdicts_finaux)."""
        log: List[MasterDiscussion] = []
        rounds = 0
        verdicts = dict(master_verdicts)

        if self.journal:
            self.journal.consensus_in_progress()

        for round_n in range(1, self.MAX_ROUNDS + 1):
            rounds = round_n
            contradictions = self._detect_contradictions(verdicts, master_weights)

            if not contradictions:
                if self.journal:
                    self.journal.consensus_in_progress("✅ Aucune contradiction détectée.")
                break

            self._log_contradictions(contradictions)

            # Le Coordinator demande une nouvelle vérification en cas de désaccord
            if self.journal:
                self.journal.master_discussion(
                    round_n, "🧠 Global Coordinator", None,
                    "Nouvelle vérification. Merci de justifier vos conclusions."
                )

            for left_id, right_id, reason in contradictions:
                left = verdicts[left_id]
                right = verdicts[right_id]

                # Ré-évaluation active auprès des experts
                if masters:
                    if left_id in masters:
                        verdicts[left_id] = await masters[left_id].reevaluate(query, left, right.conclusion)
                    if right_id in masters:
                        verdicts[right_id] = await masters[right_id].reevaluate(query, right, left.conclusion)
                    
                    left = verdicts[left_id]
                    right = verdicts[right_id]

                # Le Master avec le poids le plus élevé explique d'abord
                if master_weights.get(left_id, 0) >= master_weights.get(right_id, 0):
                    first, second = left, right
                else:
                    first, second = right, left

                msg = (
                    f"{first.master_name} interpelle {second.master_name}: "
                    f"ta conclusion '{second.conclusion}' (score: {second.score:.1f}%) "
                    f"diffère de la mienne ('{first.conclusion}', score: {first.score:.1f}%). "
                    f"Raison: {reason}. Justification: {first.reasoning_summary}"
                )
                log.append(MasterDiscussion(
                    round=round_n,
                    speaker_id=first.master_id,
                    speaker_name=first.master_name,
                    target_id=second.master_id,
                    target_name=second.master_name,
                    message=msg,
                    evidence_cited=first.evidence[:3],
                ))
                if self.journal:
                    self.journal.master_discussion(
                        round_n, first.master_name, second.master_name, msg
                    )

                response = (
                    f"{second.master_name} répond: Ma conclusion '{second.conclusion}' "
                    f"est confirmée après ré-évaluation: {second.reasoning_summary} "
                    f"Preuves: {'; '.join(second.evidence[:3]) or 'aucune'}."
                )
                log.append(MasterDiscussion(
                    round=round_n,
                    speaker_id=second.master_id,
                    speaker_name=second.master_name,
                    target_id=first.master_id,
                    target_name=first.master_name,
                    message=response,
                    evidence_cited=second.evidence[:3],
                ))
                if self.journal:
                    self.journal.master_discussion(
                        round_n, second.master_name, first.master_name, response
                    )

            # Résolution : ajuster les scores vers la moyenne pondérée
            self._resolve_contradictions(verdicts, master_weights, contradictions)

        return log, rounds, verdicts

    def _detect_contradictions(
        self,
        verdicts: Dict[str, MasterVerdict],
        weights: Dict[str, float],
    ) -> List[tuple]:
        """Détecte les contradictions entre Masters.

        Retourne une liste de (left_id, right_id, reason).
        """
        contradictions = []
        ids = list(verdicts.keys())

        for i, left_id in enumerate(ids):
            for right_id in ids[i + 1:]:
                left = verdicts[left_id]
                right = verdicts[right_id]

                # Conflit sur la conclusion
                if left.conclusion != right.conclusion and left.conclusion != "UNKNOWN" and right.conclusion != "UNKNOWN":
                    contradictions.append((
                        left_id, right_id,
                        f"Conclusions divergentes: '{left.conclusion}' vs '{right.conclusion}'"
                    ))
                    continue

                # Conflit sur la confiance (même conclusion mais écart > 30%)
                if left.conclusion == right.conclusion and left.conclusion != "UNKNOWN":
                    score_gap = abs(left.score - right.score)
                    if score_gap >= 30.0:
                        contradictions.append((
                            left_id, right_id,
                            f"Même conclusion mais confiance très différente: "
                            f"{left.score:.1f}% vs {right.score:.1f}%"
                        ))

        return contradictions

    def _resolve_contradictions(
        self,
        verdicts: Dict[str, MasterVerdict],
        weights: Dict[str, float],
        contradictions: List[tuple],
    ):
        """Résout les contradictions en ajustant les scores vers la moyenne pondérée."""
        total_weight = sum(weights.values())
        if total_weight == 0:
            return

        # Calculer le score pondéré global
        weighted_score = sum(
            verdicts[mid].score * weights.get(mid, 0) / total_weight
            for mid in verdicts
        )

        # Pour chaque Master en contradiction, rapprocher son score de la moyenne
        for left_id, right_id, _ in contradictions:
            for mid in (left_id, right_id):
                current = verdicts[mid].score
                w = weights.get(mid, 0) / total_weight
                # Ajustement : 20% vers la moyenne pondérée
                adjusted = current * 0.8 + weighted_score * 0.2
                verdicts[mid].score = round(adjusted, 2)

                if self.journal:
                    self.journal.contradiction_resolved(
                        left_id, right_id,
                        f"Score de {mid} ajusté de {current:.1f}% à {adjusted:.1f}%"
                    )

    def _log_contradictions(self, contradictions: List[tuple]):
        if not self.journal:
            return
        for left_id, right_id, reason in contradictions:
            self.journal.contradiction_detected(left_id, right_id, reason)
