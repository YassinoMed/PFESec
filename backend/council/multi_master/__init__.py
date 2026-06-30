"""Multi-Master AI — Architecture hiérarchique de délibération collaborative.

Plusieurs Master AI spécialisés (Threat, SOC, RAG) analysent une requête,
confrontent leurs conclusions via l'Inter-Master Discussion Engine,
et produisent une décision finale via le Weighted Consensus Engine.
"""

from backend.council.multi_master.base_master import BaseMaster, MasterResult
from backend.council.multi_master.discussion_engine import InterMasterDiscussionEngine
from backend.council.multi_master.discussion_journal import DiscussionJournal
from backend.council.multi_master.global_coordinator import GlobalCoordinator
from backend.council.multi_master.rag_master import RAGMaster
from backend.council.multi_master.soc_master import SOCMaster
from backend.council.multi_master.threat_master import ThreatMaster
from backend.council.multi_master.governance_master import GovernanceMaster
from backend.council.multi_master.types import (
    MasterDiscussion,
    MasterPlan,
    MasterVerdict,
    MultiMasterResult,
    WeightedConsensus,
)
from backend.council.multi_master.weighted_consensus import WeightedConsensusEngine

__all__ = [
    "GlobalCoordinator",
    "BaseMaster", "MasterResult",
    "ThreatMaster",
    "SOCMaster",
    "RAGMaster",
    "GovernanceMaster",
    "InterMasterDiscussionEngine",
    "WeightedConsensusEngine", "WeightedConsensus",
    "DiscussionJournal",
    "MultiMasterResult", "MasterVerdict", "MasterPlan", "MasterDiscussion",
]
