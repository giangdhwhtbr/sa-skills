"""Effective configuration of a design folder: preset + step options + rule severities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import catalog
from .model import Finding

CONFIG_FILE = "sa-config.yaml"


@dataclass(frozen=True)
class EffectiveConfig:
    """What a design is checked against, after presets and overrides are applied."""

    profile: str
    cloud: str
    options: dict[str, dict[str, Any]]
    severities: dict[str, str]
    overrides: dict[str, str] = field(default_factory=dict)
    problems: list[Finding] = field(default_factory=list)


def _problem(item: str, message: str) -> Finding:
    return Finding(rule="CONFIG", severity="error", file=CONFIG_FILE, item=item, message=message)


def _allowed(values: list[Any]) -> str:
    return ", ".join(str(v).lower() if isinstance(v, bool) else str(v) for v in values)


def _apply(options: dict[str, dict[str, Any]], steps: dict[str, catalog.StepSpec],
           source: dict[str, Any], where: str, problems: list[Finding]) -> None:
    """Overlay option values from a preset or sa-config.yaml, reporting unknown keys and values."""
    for step_key, values in (source or {}).items():
        step = steps.get(step_key)
        if step is None:
            problems.append(_problem(f"{where}.{step_key}", f"unknown step; known: {_allowed(list(steps))}"))
            continue
        for name, value in (values or {}).items():
            spec = step.options.get(name)
            if spec is None:
                known = _allowed(list(step.options)) or "none"
                problems.append(_problem(f"{where}.{step_key}.{name}", f"unknown option; known: {known}"))
            elif value not in spec.values or isinstance(value, bool) != isinstance(spec.default, bool):
                problems.append(_problem(
                    f"{where}.{step_key}.{name}", f"'{value}' is not allowed; allowed: {_allowed(spec.values)}"
                ))
            else:
                options[step_key][name] = value


def effective(design_dir: Path, refs: Path) -> EffectiveConfig:
    """Compute the effective configuration of a design folder; problems are returned, not raised."""
    raw = yaml.safe_load((design_dir / CONFIG_FILE).read_text()) or {}
    steps = {s.key: s for s in catalog.load_steps(refs)}
    rules = catalog.load_rules(refs)
    presets = catalog.load_presets(refs)
    problems: list[Finding] = []

    options = {key: {name: spec.default for name, spec in step.options.items()} for key, step in steps.items()}
    profile = str(raw.get("profile", "high-level"))
    if profile in presets:
        _apply(options, steps, presets[profile], f"preset {profile}", problems)
    elif profile != "custom":
        problems.append(_problem("profile", f"unknown profile '{profile}'; allowed: {_allowed([*presets, 'custom'])}"))
    _apply(options, steps, raw.get("steps") or {}, "steps", problems)

    cloud = str(raw.get("cloud", "aws"))
    known_clouds = catalog.cloud_profiles(refs)
    if known_clouds and cloud not in known_clouds:
        problems.append(_problem("cloud", f"unknown cloud profile '{cloud}'; available: {_allowed(known_clouds)}"))

    severities = {rule_id: rule.severity for rule_id, rule in rules.items()}
    overrides: dict[str, str] = {}
    for rule_id, severity in (raw.get("rules") or {}).items():
        if rule_id not in rules:
            problems.append(_problem(f"rules.{rule_id}", "unknown rule ID"))
        elif severity not in catalog.SEVERITIES:
            problems.append(_problem(f"rules.{rule_id}", f"'{severity}' is not allowed; allowed: error, warn, off"))
        else:
            severities[rule_id] = severity
            overrides[rule_id] = severity

    return EffectiveConfig(profile=profile, cloud=cloud, options=options, severities=severities,
                           overrides=overrides, problems=problems)


def rule_active(rule: catalog.RuleSpec, cfg: EffectiveConfig) -> bool:
    """True when the rule is not switched off and its option condition (if any) holds."""
    if cfg.severities.get(rule.id, rule.severity) == "off":
        return False
    if rule.condition is None:
        return True
    return cfg.options.get(rule.condition.step, {}).get(rule.condition.option) == rule.condition.equals
