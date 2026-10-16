"""Schema and template tests."""

from pathlib import Path

import pytest
from sacheck import catalog, schemas

REFS = Path(__file__).resolve().parents[1] / "skills" / "sa-design" / "references"
DATA = {
    "brief": "brief", "functions": "functions", "subdomains": "subdomains", "context-map": "context-map",
    "aggregates": "aggregates", "use-cases": "use-cases", "logical-view": "logical", "saga": "saga",
    "patterns": "patterns", "architecture": "architecture", "stack": "stack", "adrs": "adrs",
}


@pytest.mark.parametrize("key", catalog.STEP_KEYS)
def test_templates_validate(key: str) -> None:
    """REQ-QUALITY-001: every data template validates against its schema."""
    name = DATA[key]
    findings = schemas.validate(REFS / "templates" / f"{name}.yaml", REFS / "schema" / f"{name}.schema.yaml")
    assert findings == []


@pytest.mark.parametrize("name", ["sa-config", "design-state"])
def test_config_templates_validate(name: str) -> None:
    """REQ-QUALITY-001: the configuration and state templates validate against their schemas."""
    assert schemas.validate(REFS / "templates" / f"{name}.yaml", REFS / "schema" / f"{name}.schema.yaml") == []


@pytest.mark.parametrize("number,key", list(enumerate(catalog.STEP_KEYS, 1)))
def test_every_step_has_schema_and_templates(number: int, key: str) -> None:
    """REQ-DESIGN-003: each step has its schema, its data template and its Markdown template."""
    name = DATA[key]
    assert (REFS / "schema" / f"{name}.schema.yaml").is_file()
    assert (REFS / "templates" / f"{name}.yaml").is_file()
    assert (REFS / "templates" / f"{number:02d}-{key}.md").is_file()


def test_bad_edge_type_rejected(tmp_path: Path) -> None:
    """REQ-DESIGN-005: a context-map relationship with an unknown pattern is a schema error."""
    bad = tmp_path / "context-map.yaml"
    bad.write_text("relationships:\n  - {upstream: a, downstream: b, pattern: friendly, label: x}\n")
    findings = schemas.validate(bad, REFS / "schema" / "context-map.schema.yaml")
    assert len(findings) == 1
    assert findings[0].rule == "SCHEMA"
    assert findings[0].item == "relationships[0].pattern"


def test_invalid_yaml_reported(tmp_path: Path) -> None:
    """REQ-DESIGN-005: unparsable YAML is reported, not raised."""
    bad = tmp_path / "brief.yaml"
    bad.write_text("system: [unclosed\n")
    findings = schemas.validate(bad, REFS / "schema" / "brief.schema.yaml")
    assert [f.rule for f in findings] == ["SCHEMA"]


def test_bad_id_rejected(tmp_path: Path) -> None:
    """REQ-DESIGN-005: IDs must be kebab-case."""
    bad = tmp_path / "subdomains.yaml"
    bad.write_text(
        "subdomains:\n  - {id: Bad_Id, name: n, type: core, description: d,\n"
        "     service: {id: s, name: S}, function_ids: []}\n"
    )
    findings = schemas.validate(bad, REFS / "schema" / "subdomains.schema.yaml")
    assert [f.item for f in findings] == ["subdomains[0].id"]
