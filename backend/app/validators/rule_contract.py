"""Load frozen rule-set version metadata from contract YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

_DEFAULT_QUALITY_RULES = (
    Path(__file__).resolve().parents[3] / "specs/contracts/data_quality_rules.yaml"
)
_DEFAULT_CONFLICT_RULES = (
    Path(__file__).resolve().parents[3] / "specs/contracts/source_conflict_rules.yaml"
)


def load_rule_contract(rules_path: Path) -> tuple[str, str]:
    """Return (rule_set_id, rule_version) from contract YAML ``version`` field."""
    if not rules_path.is_file():
        return ("unknown", "unknown")
    raw = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    version = str(raw.get("version", "unknown"))
    return version, version


def default_quality_rule_contract() -> tuple[str, str]:
    return load_rule_contract(_DEFAULT_QUALITY_RULES)


def default_conflict_rule_contract() -> tuple[str, str]:
    return load_rule_contract(_DEFAULT_CONFLICT_RULES)
