"""Step guide tests: front matter, sections, options, rules and vendor neutrality."""

import re
from pathlib import Path

import pytest
from sacheck import catalog

REFS = Path(__file__).resolve().parents[1] / "skills" / "sa-design" / "references"
FRONT_KEYS = ["number", "key", "title", "markdown", "data", "schema", "inputs", "options", "rules"]
SECTIONS = ["## Purpose", "## Inputs", "## Propose", "## Key questions", "## Write", "## Checklist", "## Good and bad"]
DATA = {
    "brief": "brief.yaml", "functions": "functions.yaml", "subdomains": "subdomains.yaml",
    "context-map": "context-map.yaml", "aggregates": "aggregates.yaml", "use-cases": "use-cases.yaml",
    "logical-view": "logical.yaml", "saga": "saga.yaml", "patterns": "patterns.yaml",
    "architecture": "architecture.yaml", "stack": "stack.yaml", "adrs": "adrs.yaml",
}
INPUTS = {
    "brief": [], "functions": ["brief.yaml"], "subdomains": ["brief.yaml", "functions.yaml"],
    "context-map": ["subdomains.yaml"], "aggregates": ["subdomains.yaml", "context-map.yaml"],
    "use-cases": ["brief.yaml", "functions.yaml"],
    "logical-view": ["brief.yaml", "subdomains.yaml", "context-map.yaml"],
    "saga": ["subdomains.yaml", "aggregates.yaml", "logical.yaml"], "patterns": ["logical.yaml"],
    "architecture": ["logical.yaml", "patterns.yaml"], "stack": ["architecture.yaml"],
    "adrs": [
        "brief.yaml", "functions.yaml", "subdomains.yaml", "context-map.yaml", "aggregates.yaml", "use-cases.yaml",
        "logical.yaml", "saga.yaml", "patterns.yaml", "architecture.yaml", "stack.yaml",
    ],
}
OPTIONS = {
    "subdomains": {"service-per-subdomain": (["one", "allow-shared"], "one")},
    "context-map": {"detail": (["ud-only", "with-patterns", "with-externals"], "ud-only")},
    "aggregates": {"detail": (["roots-only", "full"], "roots-only")},
    "logical-view": {"vendors": (["none", "technology-hints", "named-services"], "none")},
    "saga": {"failure-scenarios": ([1, 2, 3], 2)},
    "patterns": {"split": (["one-per-pattern", "combined"], "one-per-pattern")},
    "architecture": {"shared-layout": ([True, False], True)},
}


def _guide(number: int) -> Path | None:
    found = sorted((REFS / "steps").glob(f"{number:02d}-*.md"))
    return found[0] if found else None


@pytest.mark.parametrize("number,key", list(enumerate(catalog.STEP_KEYS, 1)))
def test_guides_front_matter(number: int, key: str) -> None:
    """REQ-DESIGN-003, REQ-CONFIG-001: front matter, options and rules match the plan."""
    path = _guide(number)
    if path is None:
        pytest.skip(f"guide {number:02d} not written yet")
    front = catalog.read_front_matter(path)
    assert list(front) == FRONT_KEYS
    assert front["number"] == number and front["key"] == key
    assert path.name == f"{number:02d}-{key}.md" == front["markdown"]
    assert front["data"] == DATA[key]
    assert front["schema"] == DATA[key].replace(".yaml", ".schema.yaml")
    assert front["inputs"] == INPUTS[key]
    declared = {name: (spec["values"], spec["default"]) for name, spec in (front["options"] or {}).items()}
    assert declared == OPTIONS.get(key, {})
    assert all(spec.get("affects") for spec in (front["options"] or {}).values())
    rules = catalog.load_rules(REFS)
    expected_rules = sorted(r.id for r in rules.values() if r.step == key)
    assert sorted(front["rules"]) == expected_rules


@pytest.mark.parametrize("number", range(1, 13))
def test_guides_sections_in_order(number: int) -> None:
    """REQ-DESIGN-004: every guide has the sections the orchestrator relies on, in order."""
    path = _guide(number)
    if path is None:
        pytest.skip(f"guide {number:02d} not written yet")
    text = path.read_text()
    positions = [text.find(heading + "\n") for heading in SECTIONS]
    assert all(p >= 0 for p in positions), [h for h, p in zip(SECTIONS, positions, strict=True) if p < 0]
    assert positions == sorted(positions)
    questions = text.split("## Key questions\n", 1)[1].split("\n## ", 1)[0]
    numbered = re.findall(r"^\d+\. ", questions, re.MULTILINE)
    assert 2 <= len(numbered) <= 5
    assert questions.count("Recommended:") >= len(numbered)


@pytest.mark.parametrize("number", range(1, 10))
def test_guides_vendor_neutral(number: int) -> None:
    """REQ-CONFIG-006: guides 01-09 name no vendor or product."""
    path = _guide(number)
    if path is None:
        pytest.skip(f"guide {number:02d} not written yet")
    text = path.read_text().lower()
    hits = [t for t in catalog.load_vendor_terms(REFS) if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", text)]
    assert hits == []


def test_presets_only_set_declared_options() -> None:
    """REQ-CONFIG-002: presets only set options that the guides declare, with allowed values."""
    steps = {s.key: s for s in catalog.load_steps(REFS)}
    for preset, by_step in catalog.load_presets(REFS).items():
        for key, values in by_step.items():
            if key not in steps:
                pytest.skip(f"guide for {key} not written yet")
            for name, value in values.items():
                assert value in steps[key].options[name].values, (preset, key, name)


def test_aws_profile_covers_kinds() -> None:
    """REQ-CONFIG-006: the AWS profile maps every logical component kind except client and external."""
    text = (REFS / "profiles" / "aws.md").read_text()
    rows = {line.split("|")[1].strip() for line in text.splitlines() if line.startswith("| ") and "---" not in line}
    for kind in ("gateway", "identity-provider", "service", "broker", "datastore"):
        assert kind in rows, kind


def test_inputs_come_from_earlier_steps() -> None:
    """REQ-DESIGN-007: every input of a step is produced by an earlier step, so a missing prerequisite can be named."""
    steps = catalog.load_steps(REFS)
    producer = {s.data: s for s in steps}
    for step in steps:
        for name in step.inputs:
            assert name in producer, (step.key, name)
            assert producer[name].number < step.number, (step.key, name)
