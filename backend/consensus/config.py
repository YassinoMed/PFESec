import json
import os
from dataclasses import dataclass
from pathlib import Path
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
    model_timeout_s: float = 30.0
    log_dir: str = "logs/consensus"

    @classmethod
    def default(cls) -> "ConsensusConfig":
        config_path = os.getenv("CONSENSUS_CONFIG_PATH")
        if config_path:
            return cls.from_file(config_path)

        default_path = Path(__file__).with_name("consensus_config.json")
        if default_path.exists():
            return cls.from_file(default_path)

        return cls()

    @classmethod
    def from_file(cls, path: str) -> "ConsensusConfig":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

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
            model_timeout_s=d.get("model_timeout_s", 30.0),
            log_dir=d.get("log_dir", "logs/consensus"),
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
            "model_timeout_s": self.model_timeout_s,
            "log_dir": self.log_dir,
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
