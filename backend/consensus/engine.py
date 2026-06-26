import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.consensus.config import ConsensusConfig


@dataclass
class ModelVote:
    model_id: str
    model_name: str
    category: str
    confidence: float
    weight: int
    response: Any
    inference_ms: float
    error: Optional[str] = None

    @property
    def weighted_score(self) -> float:
        return self.confidence * self.weight

    @property
    def is_valid(self) -> bool:
        return self.rejection_reason is None

    @property
    def rejection_reason(self) -> Optional[str]:
        if self.error:
            return self.error
        if self.response is None:
            return "empty_response"
        if isinstance(self.response, str) and not self.response.strip():
            return "empty_response"
        if self.confidence is None:
            return "missing_confidence"
        if not isinstance(self.confidence, (int, float)) or math.isnan(float(self.confidence)):
            return "invalid_confidence"
        if self.confidence < 0 or self.confidence > 100:
            return "confidence_out_of_range"
        return None


@dataclass
class ConsensusResult:
    query: str
    global_score: float
    confidence_level: str
    final_response: Any
    primary_model: Optional[ModelVote] = None
    votes: List[ModelVote] = field(default_factory=list)
    retained: List[ModelVote] = field(default_factory=list)
    rejected: List[ModelVote] = field(default_factory=list)
    total_models_executed: int = 0
    total_retained: int = 0
    total_rejected: int = 0
    total_execution_ms: float = 0.0
    consensus_reached: bool = False
    warning: Optional[str] = None
    contributions: Dict[str, float] = field(default_factory=dict)
    config: ConsensusConfig = field(default_factory=ConsensusConfig)

    def to_dict(self) -> Dict:
        def vote_dict(v: ModelVote) -> Dict:
            rejection_reason = v.rejection_reason
            if v in self.rejected and rejection_reason is None and v.confidence < self.config.medium_confidence_threshold:
                rejection_reason = f"confidence_below_threshold ({v.confidence:.1f}%)"
            return {
                "model_id": v.model_id,
                "model_name": v.model_name,
                "category": v.category,
                "confidence": round(v.confidence, 2),
                "weight": v.weight,
                "weighted_score": round(v.weighted_score, 2),
                "contribution": round(self.contributions.get(v.model_id, 0.0), 2),
                "inference_ms": round(v.inference_ms, 2),
                "error": v.error,
                "rejection_reason": rejection_reason,
            }

        ranking = sorted(self.retained, key=lambda v: v.confidence, reverse=True)
        strongest = sorted(self.retained, key=lambda v: (self.contributions.get(v.model_id, 0.0), v.confidence), reverse=True)

        return {
            "query": self.query[:200],
            "global_score": round(self.global_score, 2),
            "confidence_level": self.confidence_level,
            "consensus_reached": self.consensus_reached,
            "warning": self.warning,
            "final_response": self.final_response,
            "primary_model": vote_dict(self.primary_model) if self.primary_model else None,
            "total_models_executed": self.total_models_executed,
            "total_retained": self.total_retained,
            "total_rejected": self.total_rejected,
            "total_execution_ms": round(self.total_execution_ms, 2),
            "config": self.config.to_dict(),
            "ranking": [vote_dict(v) for v in ranking],
            "top_contributors": [vote_dict(v) for v in strongest],
            "retained": [vote_dict(v) for v in self.retained],
            "rejected": [vote_dict(v) for v in self.rejected],
            "contributions": {k: round(v, 2) for k, v in sorted(self.contributions.items(), key=lambda x: x[1], reverse=True)},
            "timestamp": datetime.utcnow().isoformat(),
        }


class ConsensusEngine:
    def __init__(self, config: Optional[ConsensusConfig] = None, registry=None):
        self.config = config or ConsensusConfig.default()
        self.registry = registry

    def compute(self, query: str, votes: List[ModelVote]) -> ConsensusResult:
        t0 = time.time()
        result = ConsensusResult(
            query=query,
            global_score=0.0,
            confidence_level="Low",
            final_response=None,
            total_models_executed=len(votes),
            config=self.config,
        )

        for v in votes:
            if v.is_valid:
                result.votes.append(v)
            else:
                v.error = v.rejection_reason
                result.rejected.append(v)

        self._filter(result)
        if result.retained:
            self._weight(result)
            self._calculate_global_score(result)
            self._select_primary_model(result)
            self._assess_consensus(result)
        else:
            self._fallback(result)

        result.total_execution_ms = (time.time() - t0) * 1000
        result.total_rejected = len(result.rejected)
        result.total_retained = len(result.retained)
        result.confidence_level = self.config.get_confidence_level(result.global_score)

        self._log(result)
        return result

    def _filter(self, result: ConsensusResult):
        for v in result.votes:
            if v.confidence >= self.config.medium_confidence_threshold:
                result.retained.append(v)
            else:
                result.rejected.append(v)

    def _weight(self, result: ConsensusResult):
        for v in result.retained:
            v.weight = self.config.get_weight(v.confidence)

    def _calculate_global_score(self, result: ConsensusResult):
        total_weighted = sum(v.weighted_score for v in result.retained)
        total_weights = sum(v.weight for v in result.retained)

        if total_weights > 0:
            result.global_score = total_weighted / total_weights
        else:
            result.global_score = 0.0

        for v in result.retained:
            if total_weighted > 0:
                result.contributions[v.model_id] = (v.weighted_score / total_weighted) * 100.0
            else:
                result.contributions[v.model_id] = 0.0

    def _select_primary_model(self, result: ConsensusResult):
        best = max(result.retained, key=lambda v: (v.weighted_score, v.confidence, -v.inference_ms))
        result.primary_model = best
        result.final_response = best.response

        high_conf = [v for v in result.retained if v.confidence >= self.config.high_confidence_threshold]
        if len(high_conf) >= 2:
            responses = [str(v.response) for v in high_conf]
            if self._responses_similar(responses, self.config.consensus_overlap_ratio):
                result.consensus_reached = True
                if len(high_conf) > 1:
                    result.final_response = self._synthesize(high_conf)

    def _assess_consensus(self, result: ConsensusResult):
        retained = result.retained
        if len(retained) >= self.config.min_models_for_strong_consensus:
            high_conf = [v for v in retained if v.confidence >= self.config.high_confidence_threshold]
            if len(high_conf) >= 2 and self._responses_similar([str(v.response) for v in high_conf], self.config.consensus_overlap_ratio):
                result.consensus_reached = True
                result.confidence_level = "High"
            elif len(retained) >= 2:
                result.consensus_reached = False
                result.confidence_level = "Medium"

    def _fallback(self, result: ConsensusResult):
        available = [v for v in result.votes if v.is_valid]
        if available:
            best = max(available, key=lambda v: (v.confidence, -v.inference_ms))
            best.weight = self.config.weight_low
            result.retained = [best]
            result.rejected = [v for v in result.rejected if v.model_id != best.model_id]
            result.primary_model = best
            result.global_score = best.confidence
            result.final_response = best.response
            result.contributions[best.model_id] = 100.0
            result.warning = f"Aucun modele n'atteint le seuil de {self.config.medium_confidence_threshold}%. Meilleure reponse utilisee avec faible confiance ({best.confidence:.1f}%)."
            result.consensus_reached = False

    def _responses_similar(self, responses: List[str], threshold: float = 0.6) -> bool:
        if len(responses) < 2:
            return True
        labels = [self._extract_conclusion(r) for r in responses]
        known = [label for label in labels if label]
        if len(known) >= 2 and len(set(known)) > 1:
            return False
        if len(known) >= 2 and len(set(known)) == 1:
            return True
        pairs = 0
        similar = 0
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                pairs += 1
                if self._text_similarity(responses[i], responses[j]) >= threshold:
                    similar += 1
        if pairs == 0:
            return True
        return (similar / pairs) >= threshold

    def _text_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        set_a, set_b = set(a.lower().split()), set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def _extract_conclusion(self, response: str) -> Optional[str]:
        text = response.lower()
        labels = {
            "block": ("block", "phishing", "malicious", "malware", "menace", "danger", "unsafe"),
            "accept": ("accept", "safe", "legitimate", "legitime", "benign", "normal", "sain"),
        }
        matches = [label for label, words in labels.items() if any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)]
        if len(matches) == 1:
            return matches[0]
        return None

    def _synthesize(self, high_conf_votes: List[ModelVote]) -> Dict:
        responses = [v.response for v in high_conf_votes]
        if all(isinstance(r, dict) for r in responses):
            merged = {}
            for r in responses:
                merged.update(r)
            merged["_synthesis"] = {
                "sources": [v.model_id for v in high_conf_votes],
                "method": "merge",
            }
            return merged
        best = max(high_conf_votes, key=lambda v: v.confidence)
        return best.response

    def _log(self, result: ConsensusResult):
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "query_preview": result.query[:150],
                "global_score": result.global_score,
                "confidence_level": result.confidence_level,
                "consensus_reached": result.consensus_reached,
                "total_executed": result.total_models_executed,
                "total_retained": result.total_retained,
                "total_rejected": result.total_rejected,
                "primary_model": result.primary_model.model_id if result.primary_model else None,
                "warning": result.warning,
                "scores": {v.model_id: v.confidence for v in result.votes + result.rejected},
                "weights": {v.model_id: v.weight for v in result.retained + result.rejected},
                "contributions": result.contributions,
                "rejected": [{"model_id": v.model_id, "reason": v.error or f"confidence_too_low ({v.confidence:.1f}%)"} for v in result.rejected],
            }
            entry["selected_response"] = result.final_response
            log_dir = os.getenv("CONSENSUS_LOG_DIR", self.config.log_dir)
            os.makedirs(log_dir, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            with open(os.path.join(log_dir, f"consensus_{ts}.json"), "w") as f:
                json.dump(entry, f, indent=2, default=str)
        except Exception:
            pass
