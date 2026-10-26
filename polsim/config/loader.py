"""Configuration loader and serializer for scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from polsim.config.schema import ScenarioConfig


def load_scenario(path: str | Path) -> ScenarioConfig:
    """Load a ScenarioConfig from a YAML or JSON file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Scenario configuration file not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return ScenarioConfig.model_validate(data)


def save_scenario(config: ScenarioConfig, path: str | Path) -> None:
    """Save a ScenarioConfig to a YAML or JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(mode="json")
    if p.suffix.lower() in {".yaml", ".yml"}:
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(data, indent=2)
    p.write_text(text, encoding="utf-8")


def get_json_schema() -> dict[str, Any]:
    """Generate OpenAPI / JSON Schema with UI annotations for frontend consumers."""
    return ScenarioConfig.model_json_schema()
