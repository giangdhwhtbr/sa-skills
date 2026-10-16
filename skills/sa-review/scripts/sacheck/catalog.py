"""Load the plugin catalogue: step guides (front matter), rules and presets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

STEP_KEYS: tuple[str, ...] = (
    "brief", "functions", "subdomains", "context-map", "aggregates", "use-cases",
    "logical-view", "saga", "patterns", "architecture", "stack", "adrs",
)
SEVERITIES = ("error", "warn", "off")
CHECK_KINDS = ("script", "judgement")
_RULE_ID = re.compile(r"[A-Z]{2,3}-\d{2}")
_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class OptionSpec:
    """An option a step declares: its allowed values and default."""

    values: list[Any]
    default: Any
    affects: str = ""


@dataclass(frozen=True)
class StepSpec:
    """A design step as declared in the front matter of its guide."""

    number: int
    key: str
    title: str
    markdown: str
    data: str
    schema: str
    inputs: list[str] = field(default_factory=list)
    options: dict[str, OptionSpec] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Condition:
    """A rule is active only when the step option equals the value."""

    step: str
    option: str
    equals: Any


@dataclass(frozen=True)
class RuleSpec:
    """One review rule from rules.yaml."""

    id: str
    step: str
    severity: str
    condition: Condition | None
    check: str
    statement: str


def read_front_matter(path: Path) -> dict[str, Any]:
    """Return the YAML front matter of a Markdown file, or raise ValueError."""
    match = _FRONT_MATTER.match(path.read_text())
    if not match:
        raise ValueError(f"{path.name}: missing front matter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: front matter is not a mapping")
    return data


def load_steps(refs: Path) -> list[StepSpec]:
    """Load every step guide under refs/steps, ordered by step number."""
    steps_dir = refs / "steps"
    if not steps_dir.is_dir():
        return []
    steps = []
    for path in sorted(steps_dir.glob("[0-9][0-9]-*.md")):
        front = read_front_matter(path)
        options = {
            name: OptionSpec(values=list(spec["values"]), default=spec["default"], affects=spec.get("affects", ""))
            for name, spec in (front.get("options") or {}).items()
        }
        for name, spec in options.items():
            if spec.default not in spec.values:
                raise ValueError(f"{path.name}: default of option '{name}' is not one of its values")
        steps.append(StepSpec(
            number=int(front["number"]), key=str(front["key"]), title=str(front["title"]),
            markdown=str(front["markdown"]), data=str(front["data"]), schema=str(front["schema"]),
            inputs=list(front.get("inputs") or []), options=options, rules=list(front.get("rules") or []),
        ))
    return sorted(steps, key=lambda s: s.number)


def load_rules(refs: Path) -> dict[str, RuleSpec]:
    """Load and validate rules.yaml; raise ValueError naming the first bad rule."""
    raw = yaml.safe_load((refs / "rules.yaml").read_text())
    rules: dict[str, RuleSpec] = {}
    for entry in raw.get("rules", []):
        rule_id = str(entry.get("id", ""))
        if not _RULE_ID.fullmatch(rule_id):
            raise ValueError(f"rule '{rule_id}': id must look like AB-01")
        if rule_id in rules:
            raise ValueError(f"rule '{rule_id}': duplicate id")
        step = entry.get("step")
        if step not in STEP_KEYS and step != "all":
            raise ValueError(f"rule '{rule_id}': unknown step '{step}'")
        if entry.get("severity") not in SEVERITIES:
            raise ValueError(f"rule '{rule_id}': severity must be one of {', '.join(SEVERITIES)}")
        if entry.get("check") not in CHECK_KINDS:
            raise ValueError(f"rule '{rule_id}': check must be one of {', '.join(CHECK_KINDS)}")
        if not entry.get("statement"):
            raise ValueError(f"rule '{rule_id}': statement is required")
        cond = entry.get("condition")
        condition = None
        if cond is not None:
            if cond.get("step") not in STEP_KEYS or not cond.get("option") or "equals" not in cond:
                raise ValueError(f"rule '{rule_id}': condition needs step, option and equals")
            condition = Condition(step=cond["step"], option=cond["option"], equals=cond["equals"])
        rules[rule_id] = RuleSpec(
            id=rule_id, step=step, severity=entry["severity"], condition=condition,
            check=entry["check"], statement=entry["statement"],
        )
    return rules


def load_presets(refs: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Load presets.yaml: preset name -> step key -> option -> value."""
    data = yaml.safe_load((refs / "presets.yaml").read_text())
    return {str(name): {str(k): dict(v) for k, v in steps.items()} for name, steps in data.items()}


def load_vendor_terms(refs: Path) -> list[str]:
    """Load the vendor and product names used by vendor-neutrality checks."""
    return [str(t).lower() for t in yaml.safe_load((refs / "vendor-terms.yaml").read_text())["terms"]]


def cloud_profiles(refs: Path) -> list[str]:
    """Names of the cloud profiles shipped under refs/profiles."""
    return sorted(p.stem for p in (refs / "profiles").glob("*.md"))
