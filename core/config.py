"""Load YAML configuration from project root."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


class AppConfig:
    def __init__(self, industry_config_name: str = "home_services") -> None:
        root = project_root()
        self.root = root
        self.generic = _load_yaml(root / "configs" / "generic.yaml")
        self.industry_config = _load_yaml(root / "configs" / f"{industry_config_name}.yaml")
        pack = self.industry_config.get("industry_pack", industry_config_name)
        pack_dir = root / "industry_packs" / pack
        self.industry_pack = pack
        self.industry_pack_dir = pack_dir
        self.taxonomy = _load_yaml(pack_dir / "taxonomy.yaml")
        self.action_rules = _load_yaml(pack_dir / "action_rules.yaml")
        self.prompts_dir = root / "prompts"


def load_config(industry_config_name: str = "home_services") -> AppConfig:
    return AppConfig(industry_config_name=industry_config_name)


def get_llm_model(config: AppConfig) -> str:
    return os.getenv("LLM_MODEL") or str(config.generic.get("llm_model", "gpt-4o-mini"))
