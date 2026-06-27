"""Base class for all Virtual Expert agents."""

import re
import time
from typing import Any, Dict, List, Optional

from backend.council.expert import CouncilExpert
from backend.council.types import ExpertAnalysis


class VirtualExpert(CouncilExpert):
    """
    Base class for all virtual expert agents.
    Implements heuristic-based analysis + structured ExpertAnalysis output.
    Subclasses define: expert_id, expert_name, category, capabilities,
    and override _analyze_query().
    """
    expert_id: str = "virtual_base"
    expert_name: str = "Virtual Expert"
    category: str = "virtual"
    capabilities: List[str] = []

    # Keywords that indicate high confidence
    HIGH_CONF_KEYWORDS: List[str] = []
    # Keywords that indicate medium confidence
    MED_CONF_KEYWORDS: List[str] = []
    # Domain-specific MITRE techniques
    MITRE_TECHNIQUES: List[str] = []

    async def analyze(self, query: str, context: Optional[Dict] = None) -> ExpertAnalysis:
        t0 = time.time()
        try:
            result = self._analyze_query(query.lower(), context or {})
            elapsed = (time.time() - t0) * 1000
            return ExpertAnalysis(
                expert_id=self.expert_id,
                expert_name=self.expert_name,
                category=self.category,
                status="completed",
                response=result.get("response", "Analyse complétée."),
                conclusion=result.get("conclusion", "UNKNOWN"),
                confidence=result.get("confidence", 0.0),
                evidence=result.get("evidence", []),
                limitations=result.get("limitations", []),
                inference_ms=elapsed,
                recommendations=result.get("recommendations", []),
                iocs=result.get("iocs", []),
                mitre_techniques=result.get("mitre_techniques", self.MITRE_TECHNIQUES[:3]),
                severity=result.get("severity", "UNKNOWN"),
            )
        except Exception as exc:
            return ExpertAnalysis(
                expert_id=self.expert_id,
                expert_name=self.expert_name,
                category=self.category,
                status="error",
                confidence=0.0,
                inference_ms=(time.time() - t0) * 1000,
                error=str(exc),
                limitations=["exception_in_virtual_expert"],
            )

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        """Override in subclasses to provide domain-specific analysis."""
        raise NotImplementedError

    def _compute_confidence(self, query: str, high_kws: List[str], med_kws: List[str]) -> float:
        """Compute confidence score based on keyword matches."""
        high_hits = sum(1 for kw in high_kws if kw in query)
        med_hits = sum(1 for kw in med_kws if kw in query)
        score = high_hits * 15 + med_hits * 8
        return min(max(score, 0.0), 95.0)

    def _extract_iocs(self, query: str) -> List[Dict]:
        iocs = []
        patterns = [
            ("url", re.compile(r"https?://[^\s\"\'>]+")),
            ("ip", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
            ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
            ("domain", re.compile(r"\b(?:[a-z0-9\-]+\.)+(?:xyz|ru|cn|tk|pw|cc|top|club)\b")),
            ("cve", re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)),
        ]
        for ioc_type, pattern in patterns:
            for m in pattern.findall(query):
                iocs.append({"type": ioc_type, "value": m, "confidence": 0.9})
        return iocs[:8]
