from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ConsensusConfig:
    high_confidence_threshold: float = 90.0
    medium_confidence_threshold: float = 80.0
    weight_high: int = 4
    weight_medium: int = 2
    weight_low: int = 1
    min_models_for_strong_consensus: int = 2
    consensus_overlap_ratio: float = 0.6

    @classmethod
    def default(cls) -> "ConsensusConfig":
        return cls()

    @classmethod
    def from_dict(cls, d: Dict) -> "ConsensusConfig":
        return cls(
            high_confidence_threshold=d.get("high_confidence_threshold", 90.0),
            medium_confidence_threshold=d.get("medium_confidence_threshold", 80.0),
            weight_high=d.get("weight_high", 4),
            weight_medium=d.get("weight_medium", 2),
            weight_low=d.get("weight_low", 1),
            min_models_for_strong_consensus=d.get("min_models_for_strong_consensus", 2),
            consensus_overlap_ratio=d.get("consensus_overlap_ratio", 0.6),
        )

    def to_dict(self) -> Dict:
        return {
            "high_confidence_threshold": self.high_confidence_threshold,
            "medium_confidence_threshold": self.medium_confidence_threshold,
            "weight_high": self.weight_high,
            "weight_medium": self.weight_medium,
            "weight_low": self.weight_low,
            "min_models_for_strong_consensus": self.min_models_for_strong_consensus,
            "consensus_overlap_ratio": self.consensus_overlap_ratio,
        }

    def get_weight(self, confidence: float) -> int:
        if confidence >= self.high_confidence_threshold:
            return self.weight_high
        elif confidence >= self.medium_confidence_threshold:
            return self.weight_medium
        return self.weight_low

    def get_confidence_level(self, score: float) -> str:
        if score >= self.high_confidence_threshold:
            return "High"
        elif score >= self.medium_confidence_threshold:
            return "Medium"
        return "Low"
