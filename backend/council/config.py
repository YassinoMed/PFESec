import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class CouncilConfig:
    enabled: bool = True
    max_debate_rounds: int = 2
    min_confidence_for_no_debate: float = 80.0
    disagreement_threshold: float = 0.35
    expert_timeout_s: float = 30.0
    cross_validation_enabled: bool = True
    reflection_enabled: bool = True
    fact_check_enabled: bool = True
    max_selected_experts: int = 10
    log_dir: str = "logs/council"

    @classmethod
    def default(cls) -> "CouncilConfig":
        config_path = os.getenv("COUNCIL_CONFIG_PATH")
        if config_path:
            return cls.from_file(config_path)
        default_path = Path(__file__).with_name("council_config.json")
        if default_path.exists():
            return cls.from_file(default_path)
        return cls()

    @classmethod
    def from_file(cls, path: str) -> "CouncilConfig":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_dict(cls, data: Dict) -> "CouncilConfig":
        return cls(
            enabled=data.get("enabled", True),
            max_debate_rounds=data.get("max_debate_rounds", 2),
            min_confidence_for_no_debate=data.get("min_confidence_for_no_debate", 80.0),
            disagreement_threshold=data.get("disagreement_threshold", 0.35),
            expert_timeout_s=data.get("expert_timeout_s", 30.0),
            cross_validation_enabled=data.get("cross_validation_enabled", True),
            reflection_enabled=data.get("reflection_enabled", True),
            fact_check_enabled=data.get("fact_check_enabled", True),
            max_selected_experts=data.get("max_selected_experts", 6),
            log_dir=data.get("log_dir", "logs/council"),
        )

    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "max_debate_rounds": self.max_debate_rounds,
            "min_confidence_for_no_debate": self.min_confidence_for_no_debate,
            "disagreement_threshold": self.disagreement_threshold,
            "expert_timeout_s": self.expert_timeout_s,
            "cross_validation_enabled": self.cross_validation_enabled,
            "reflection_enabled": self.reflection_enabled,
            "fact_check_enabled": self.fact_check_enabled,
            "max_selected_experts": self.max_selected_experts,
            "log_dir": self.log_dir,
        }
