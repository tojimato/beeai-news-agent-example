"""
Profession definitions and dynamic metadata loader for BeeAI pipeline.
All profession metadata is loaded from profession_config.yaml.
"""

from enum import Enum
from typing import Any, Dict
from pathlib import Path
import yaml

class Profession(Enum):
    SOLO_DEVELOPER = "solo_developer"
    INTERIOR_DESIGNER = "interior_designer"
    LAWYER = "lawyer"
    MARKETING_MANAGER = "marketing_manager"
    CONSERVATION_PROJECT_PLANNING_MANAGER = "conservation_project_planning_manager"

class ProfessionConfig:
    """Holds all configuration for a profession loaded from YAML."""
    def __init__(self, data: Dict[str, Any]) -> None:
        self.display_name: str = data.get("display_name", "")
        self.applicability_domains: list[str] = data.get("applicability_domains", [])
        self.risk_factors: list[str] = data.get("risk_factors", [])
        self.success_metrics: list[str] = data.get("success_metrics", [])
        self.peer_review_lens: str = data.get("peer_review_lens", "")

def _load_profession_configs() -> Dict[Profession, ProfessionConfig]:
    yaml_path = Path(__file__).parent.parent / "prompts" / "profession_config.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    professions = raw["professions"]
    configs = {}
    for key, value in professions.items():
        try:
            profession = Profession(key)
            configs[profession] = ProfessionConfig(value)
        except ValueError:
            continue  # Ignore unknown professions
    return configs

_PROFESSION_CONFIGS: Dict[Profession, ProfessionConfig] = _load_profession_configs()

def get_profession_config(profession: Profession) -> ProfessionConfig:
    return _PROFESSION_CONFIGS[profession]
