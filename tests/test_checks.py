"""Mechanical check tests: a clean fixture and one-change fault fixtures built from it."""

import hashlib
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml
from sacheck import catalog, checks

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "sa-design" / "references"
CLEAN = Path(__file__).resolve().parent / "fixtures" / "clean" / "design"

Mutation = Callable[[dict[str, Any]], None]


def make_design(tmp_path: Path, mutations: dict[str, Mutation] | None = None) -> Path:
    """Copy the clean fixture and apply one mutation per data file."""
    target = tmp_path / "design"
    shutil.copytree(CLEAN, target)
    for name, mutate in (mutations or {}).items():
        path = target / name
        data = yaml.safe_load(path.read_text())
        mutate(data)
        path.write_text(yaml.safe_dump(data, sort_keys=False))
    return target


def errors(design: Path, step: str | None = None) -> list[tuple[str, str, str]]:
    _, findings, _ = checks.run(design, REFS, step)
    return [(f.rule, f.file, f.item) for f in findings if f.severity == "error"]


def findings_of(design: Path, rule: str) -> list[Any]:
    _, findings, _ = checks.run(design, REFS)
    return [f for f in findings if f.rule == rule]


def test_clean_fixture_has_no_errors() -> None:
    """REQ-QUALITY-002: the clean fixture produces no error findings and no warnings."""
    _, findings, exceptions = checks.run(CLEAN, REFS)
    assert findings == []
    assert exceptions == []


def test_broken_reference(tmp_path: Path) -> None:
    """REQ-REVIEW-004, REQ-QUALITY-002: an unknown participant is one XS-01 error on saga.yaml."""
    design = make_design(tmp_path, {"saga.yaml": lambda d: d["participants"].append("unknown-svc")})
    assert errors(design) == [("XS-01", "saga.yaml", "unknown-svc")]


def test_vendor_in_logical(tmp_path: Path) -> None:
    """REQ-DESIGN-009, REQ-QUALITY-002: a vendor name in the logical view fails LV-01."""
    def rename(d: dict[str, Any]) -> None:
        d["layers"][3]["components"][0]["name"] = "Kafka broker"
    design = make_design(tmp_path, {"logical.yaml": rename})
    assert errors(design) == [("LV-01", "logical.yaml", "message-broker")]


def test_vendor_allowed_with_hints(tmp_path: Path) -> None:
    """REQ-CONFIG-003: LV-01 is inactive when the logical view may carry technology hints."""
    def rename(d: dict[str, Any]) -> None:
        d["layers"][3]["components"][0]["name"] = "Kafka broker"
    design = make_design(tmp_path, {
        "logical.yaml": rename,
        "sa-config.yaml": lambda d: d.update(steps={"logical-view": {"vendors": "technology-hints"}}),
    })
    assert errors(design) == []


def test_adr_without_tradeoff(tmp_path: Path) -> None:
    """REQ-REVIEW-005: an ADR without a trade-off fails AD-01."""
    design = make_design(tmp_path, {"adrs.yaml": lambda d: d["adrs"][0].update(tradeoff="")})
    assert errors(design) == [("AD-01", "adrs.yaml", "adr-service-per-subdomain")]


def test_unaddressed_pain_point(tmp_path: Path) -> None:
    """REQ-REVIEW-005: a pain point no ADR or subdomain addresses fails TR-01."""
    design = make_design(tmp_path, {
        "brief.yaml": lambda d: d["pain_points"].append({"id": "pp-unaddressed", "text": "Nobody answers this"}),
    })
    assert errors(design) == [("TR-01", "brief.yaml", "pp-unaddressed")]


def test_missing_file(tmp_path: Path) -> None:
    """REQ-REVIEW-002: a done step without its data file is a MISSING error."""
    design = make_design(tmp_path)
    (design / "use-cases.yaml").unlink()
    assert ("MISSING", "use-cases.yaml", "use-cases") in errors(design)


def test_schema_error_reported(tmp_path: Path) -> None:
    """REQ-REVIEW-002: a done step whose data fails its schema is a SCHEMA error."""
    design = make_design(tmp_path, {"stack.yaml": lambda d: d["layers"][0].update(colour="red")})
    assert [e[0] for e in errors(design)] == ["SCHEMA"]


def test_count_mismatch(tmp_path: Path) -> None:
    """REQ-REVIEW-004: a Markdown statement of the service count that differs fails XS-02."""
    design = make_design(tmp_path)
    md = design / "03-subdomains.md"
    md.write_text(md.read_text().replace("5 services", "9 services"))
    assert errors(design) == [("XS-02", "03-subdomains.md", "9 services")]


def test_roots_only_violated(tmp_path: Path) -> None:
    """REQ-QUALITY-002: entities under roots-only fail AG-01; allowed under full."""
    def add_entity(d: dict[str, Any]) -> None:
        d["aggregates"][0]["entities"] = ["Compartment"]
    design = make_design(tmp_path, {"aggregates.yaml": add_entity})
    assert errors(design) == [("AG-01", "aggregates.yaml", "delivery")]
    design_full = make_design(tmp_path / "full", {
        "aggregates.yaml": add_entity,
        "sa-config.yaml": lambda d: d.update(steps={"aggregates": {"detail": "full"}}),
    })
    assert errors(design_full) == []


def test_exception_accepted(tmp_path: Path) -> None:
    """REQ-DESIGN-009, REQ-REVIEW-003: an accepted exception removes the error and is returned with its reason."""
    def rename(d: dict[str, Any]) -> None:
        d["layers"][3]["components"][0]["name"] = "Kafka broker"

    def accept(d: dict[str, Any]) -> None:
        step = next(s for s in d["steps"] if s["key"] == "logical-view")
        step["exceptions"] = [{"rule": "LV-01", "reason": "Broker product fixed by contract"}]
    design = make_design(tmp_path, {"logical.yaml": rename, "design-state.yaml": accept})
    _, findings, exceptions = checks.run(design, REFS)
    assert [f.rule for f in findings] == []
    assert exceptions == [{"step": "logical-view", "rule": "LV-01", "reason": "Broker product fixed by contract"}]


def test_severity_warn_does_not_error(tmp_path: Path) -> None:
    """REQ-CONFIG-004: a rule downgraded to warn reports a warning, not an error."""
    def rename(d: dict[str, Any]) -> None:
        d["layers"][3]["components"][0]["name"] = "Kafka broker"
    design = make_design(tmp_path, {"logical.yaml": rename, "sa-config.yaml": lambda d: d.update(rules={"LV-01": "warn"})})
    assert errors(design) == []
    assert [f.severity for f in findings_of(design, "LV-01")] == ["warn"]


def test_config_problem_reported(tmp_path: Path) -> None:
    """REQ-CONFIG-001: invalid configuration is reported as CONFIG errors."""
    design = make_design(tmp_path, {"sa-config.yaml": lambda d: d.update(steps={"context-map": {"detail": "all"}})})
    assert ("CONFIG", "sa-config.yaml", "steps.context-map.detail") in errors(design)


def _first(key: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    return lambda d: d[key][0]


# rule -> (file, mutation, expected item)
NEGATIVE: dict[str, tuple[str, Mutation, str]] = {
    "BR-01": ("brief.yaml", lambda d: d["actors"].append({"id": "customer", "name": "Again", "kind": "person"}), "customer"),
    "FN-02": ("functions.yaml", lambda d: d["groups"][1].update(actor_ids=[]), "courier-functions"),
    "SD-01": ("subdomains.yaml", lambda d: [s.update(type="supporting") for s in d["subdomains"] if s["type"] == "core"],
              "subdomains"),
    "SD-02": ("subdomains.yaml", lambda d: d["subdomains"][1]["service"].update(id="delivery-service"), "lockers"),
    "CM-01": ("context-map.yaml", lambda d: d.update(externals=[{"id": "x", "name": "X", "direction": "inbound"}]), "x"),
    "CM-02": ("context-map.yaml", lambda d: d["relationships"][0].update(upstream="deliveries"), "deliveries->deliveries"),
    "CM-03": ("context-map.yaml", lambda d: d["relationships"].pop(3), "notifications"),
    "AG-02": ("aggregates.yaml", lambda d: d["references"][0].update(to="nowhere"), "delivery->nowhere"),
    "AG-03": ("aggregates.yaml", lambda d: d["aggregates"].pop(2), "notifications"),
    "UC-01": ("use-cases.yaml", lambda d: d["use_cases"][0].update(actor_ids=["ghost"]), "uc-sign-in"),
    "LV-02": ("logical.yaml", lambda d: d["layers"][2]["components"].pop(4), "identity-service"),
    "SG-01": ("saga.yaml", lambda d: d["scenarios"].pop(2), "send-parcel-saga"),
    "SG-02": ("saga.yaml", lambda d: d["scenarios"][1]["steps"].pop(2), "locker-full"),
    "SG-03": ("saga.yaml", lambda d: d["flow"].update(orchestrator="payment-provider"), "payment-provider"),
    "PT-01": ("patterns.yaml", lambda d: d["patterns"].pop(2), "resilience"),
    "AR-01": ("architecture.yaml", lambda d: d["mapping"].pop(4), "cache"),
    "AR-02": ("architecture.yaml", lambda d: d["physical"]["groups"].reverse(), "groups"),
    "AR-03": ("architecture.yaml", lambda d: d["physical"]["tiers"][2].update(internet_route=True), "data"),
    "ST-01": ("stack.yaml", lambda d: d["layers"][0].update(reason=""), "clients"),
}


# A mutation that breaks one rule may legitimately break these related rules as well.
ALSO_TRIGGERS: dict[str, set[str]] = {"SD-02": {"XS-01", "XS-02", "SG-03"}, "CM-02": {"CM-03"}, "AG-03": {"AG-02"}}


def test_every_script_rule_implemented() -> None:
    """REQ-REVIEW-006: every script rule in the catalogue has an implementation."""
    script_rules = {r.id for r in catalog.load_rules(REFS).values() if r.check == "script"}
    assert set(checks.RULES) == script_rules


def test_every_script_rule_has_negative_test() -> None:
    """REQ-QUALITY-002: every script rule has a negative case here or in a dedicated test above."""
    dedicated = {"LV-01", "AD-01", "TR-01", "XS-01", "XS-02", "AG-01"}
    assert set(checks.RULES) == set(NEGATIVE) | dedicated


@pytest.mark.parametrize("rule", sorted(NEGATIVE))
def test_rule_negative(rule: str, tmp_path: Path) -> None:
    """REQ-QUALITY-002: a one-change mutation of the clean fixture triggers exactly this rule."""
    file, mutate, item = NEGATIVE[rule]
    design = make_design(tmp_path, {file: mutate})
    hits = findings_of(design, rule)
    assert [f.item for f in hits] == [item], hits
    others = {f.rule for f in checks.run(design, REFS)[1] if f.rule != rule}
    assert others <= ALSO_TRIGGERS.get(rule, set()), others


def test_dependents() -> None:
    """REQ-DESIGN-006, REQ-CONFIG-005: steps that read a step's data, directly or transitively."""
    steps = catalog.load_steps(REFS)
    assert checks.dependents("subdomains", steps) == [
        "context-map", "aggregates", "logical-view", "saga", "patterns", "architecture", "stack", "adrs",
    ]
    assert checks.dependents("brief", steps) == list(catalog.STEP_KEYS[1:])
    assert checks.dependents("adrs", steps) == []


def test_changed_files(tmp_path: Path) -> None:
    """REQ-DESIGN-008: files edited after the recorded hash are reported."""
    design = make_design(tmp_path)
    state_path = design / "design-state.yaml"
    state = yaml.safe_load(state_path.read_text())
    for step in state["steps"]:
        if step["key"] == "subdomains":
            step["files"] = {
                name: hashlib.sha256((design / name).read_bytes()).hexdigest()
                for name in ("subdomains.yaml", "03-subdomains.md")
            }
    state_path.write_text(yaml.safe_dump(state, sort_keys=False))
    assert checks.changed_files(design) == []
    path = design / "subdomains.yaml"
    path.write_text(path.read_text() + "\n# edited by hand\n")
    assert checks.changed_files(design) == ["subdomains.yaml"]


def test_step_only_checks_that_step(tmp_path: Path) -> None:
    """REQ-DESIGN-009: --step limits the run to one step's schema and rules."""
    design = make_design(tmp_path, {"saga.yaml": lambda d: d["participants"].append("unknown-svc")})
    assert errors(design, "context-map") == []
