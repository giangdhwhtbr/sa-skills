"""Effective configuration tests."""

from pathlib import Path

import yaml
from sacheck import catalog, config


def _write_config(design_dir: Path, **values: object) -> None:
    data = yaml.safe_load((design_dir / "sa-config.yaml").read_text())
    data.update(values)
    (design_dir / "sa-config.yaml").write_text(yaml.safe_dump(data))


def test_default_high_level(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-002: the template config uses the high-level preset."""
    cfg = config.effective(design_dir, stub_refs)
    assert cfg.problems == []
    assert cfg.profile == "high-level"
    assert cfg.options["aggregates"]["detail"] == "roots-only"
    assert cfg.options["context-map"]["detail"] == "ud-only"
    assert cfg.options["logical-view"]["vendors"] == "none"


def test_detailed_preset(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-002: the detailed preset raises aggregate and context-map detail."""
    _write_config(design_dir, profile="detailed")
    cfg = config.effective(design_dir, stub_refs)
    assert cfg.options["aggregates"]["detail"] == "full"
    assert cfg.options["context-map"]["detail"] == "with-externals"


def test_custom_uses_defaults_and_explicit(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-002: custom takes explicit values, else defaults."""
    _write_config(design_dir, profile="custom", steps={"saga": {"failure-scenarios": 3}})
    cfg = config.effective(design_dir, stub_refs)
    assert cfg.problems == []
    assert cfg.options["saga"]["failure-scenarios"] == 3
    assert cfg.options["context-map"]["detail"] == "ud-only"


def test_explicit_option_overrides_preset(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-001: a step option in sa-config.yaml wins over the preset."""
    _write_config(design_dir, steps={"context-map": {"detail": "with-patterns"}})
    cfg = config.effective(design_dir, stub_refs)
    assert cfg.options["context-map"]["detail"] == "with-patterns"


def test_unknown_value_rejected(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-001: an unknown option value is rejected with the allowed values."""
    _write_config(design_dir, steps={"context-map": {"detail": "everything"}})
    cfg = config.effective(design_dir, stub_refs)
    assert len(cfg.problems) == 1
    problem = cfg.problems[0]
    assert problem.rule == "CONFIG"
    assert "ud-only" in problem.message and "with-externals" in problem.message


def test_unknown_option_and_profile_rejected(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-001: unknown profiles, steps and options are reported."""
    _write_config(design_dir, profile="everything", steps={"nowhere": {"x": 1}, "saga": {"colour": "red"}})
    cfg = config.effective(design_dir, stub_refs)
    items = {p.item for p in cfg.problems}
    assert {"profile", "steps.nowhere", "steps.saga.colour"} <= items


def test_severity_override(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-004: a project severity replaces the rule default."""
    _write_config(design_dir, rules={"LV-01": "warn", "DOC-02": "off"})
    cfg = config.effective(design_dir, stub_refs)
    assert cfg.problems == []
    assert cfg.severities["LV-01"] == "warn"
    assert cfg.severities["DOC-02"] == "off"
    assert cfg.severities["CM-02"] == "error"


def test_unknown_rule_override_rejected(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-004: overriding an unknown rule or using a bad severity is reported."""
    _write_config(design_dir, rules={"ZZ-99": "warn", "LV-01": "loud"})
    cfg = config.effective(design_dir, stub_refs)
    assert {p.item for p in cfg.problems} == {"rules.ZZ-99", "rules.LV-01"}


def test_rule_active_condition(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-003: a conditional rule is active only when its option matches."""
    rules = catalog.load_rules(stub_refs)
    cfg = config.effective(design_dir, stub_refs)
    assert config.rule_active(rules["CM-01"], cfg)
    _write_config(design_dir, steps={"context-map": {"detail": "with-externals"}})
    cfg = config.effective(design_dir, stub_refs)
    assert not config.rule_active(rules["CM-01"], cfg)


def test_rule_off_is_inactive(design_dir: Path, stub_refs: Path) -> None:
    """REQ-CONFIG-004: a rule set to off is never active."""
    _write_config(design_dir, rules={"CM-02": "off"})
    rules = catalog.load_rules(stub_refs)
    cfg = config.effective(design_dir, stub_refs)
    assert not config.rule_active(rules["CM-02"], cfg)
