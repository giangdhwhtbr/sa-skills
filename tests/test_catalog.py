"""Catalogue tests: rules, presets and step specs."""

import re
from pathlib import Path

import pytest
from sacheck import catalog

STEP_KEYS = set(catalog.STEP_KEYS)


def test_rules_well_formed(refs_dir: Path) -> None:
    """REQ-QUALITY-001, REQ-CONFIG-003: every rule has a valid id, step, severity and check kind."""
    rules = catalog.load_rules(refs_dir)
    assert rules
    for rule in rules.values():
        assert re.fullmatch(r"[A-Z]{2,3}-\d{2}", rule.id)
        assert rule.step in STEP_KEYS | {"all"}
        assert rule.severity in {"error", "warn", "off"}
        assert rule.check in {"script", "judgement"}
        assert rule.statement


def test_rule_catalogue_matches_plan(refs_dir: Path) -> None:
    """REQ-CONFIG-003: the catalogue holds exactly the planned rule IDs."""
    expected = {
        "BR-01", "FN-01", "FN-02", "SD-01", "SD-02", "CM-01", "CM-02", "CM-03", "AG-01", "AG-02",
        "AG-03", "UC-01", "LV-01", "LV-02", "SG-01", "SG-02", "SG-03", "PT-01", "PT-02", "AR-01",
        "AR-02", "AR-03", "ST-01", "AD-01", "TR-01", "XS-01", "XS-02", "DOC-01", "DOC-02",
    }
    assert set(catalog.load_rules(refs_dir)) == expected


def test_conditions_reference_step_options(refs_dir: Path) -> None:
    """REQ-CONFIG-003: a rule condition names a step key and an option."""
    for rule in catalog.load_rules(refs_dir).values():
        if rule.condition is not None:
            assert rule.condition.step in STEP_KEYS
            assert rule.condition.option


def test_bad_severity_rejected(tmp_path: Path) -> None:
    """REQ-QUALITY-001: a rule with an unknown severity is rejected and named."""
    (tmp_path / "rules.yaml").write_text(
        "rules:\n  - {id: XX-01, step: brief, severity: fatal, condition: null, check: script, statement: s}\n"
    )
    with pytest.raises(ValueError, match="XX-01"):
        catalog.load_rules(tmp_path)


def test_presets_cover_high_level_and_detailed(refs_dir: Path) -> None:
    """REQ-CONFIG-002: both presets exist with the planned option values."""
    presets = catalog.load_presets(refs_dir)
    assert set(presets) == {"high-level", "detailed"}
    assert presets["high-level"]["aggregates"]["detail"] == "roots-only"
    assert presets["detailed"]["context-map"]["detail"] == "with-externals"


def test_load_steps_reads_front_matter(stub_refs: Path) -> None:
    """REQ-CONFIG-001: options are declared with allowed values and a default in each step guide."""
    steps = catalog.load_steps(stub_refs)
    assert [s.key for s in steps] == list(catalog.STEP_KEYS)
    context_map = next(s for s in steps if s.key == "context-map")
    assert context_map.options["detail"].default == "ud-only"
    assert "with-externals" in context_map.options["detail"].values
