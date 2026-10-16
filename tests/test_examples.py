"""Example design sets and neutral-content tests."""

import re
import subprocess
import sys
from pathlib import Path

import yaml
from sacheck import checks, config
from sadiagram import stamp

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "sa-review" / "scripts" / "check.py"
EXAMPLES = ROOT / "examples"


def check(design: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECK), str(design)], capture_output=True, text=True, check=False)


def statuses(design: Path) -> dict[str, str]:
    state = yaml.safe_load((design / "design-state.yaml").read_text())
    return {s["key"]: s["status"] for s in state["steps"]}


def test_clinic_booking_passes() -> None:
    """REQ-QUALITY-003: the complete worked example has all 12 steps done and no errors."""
    design = EXAMPLES / "clinic-booking" / "design"
    result = check(design)
    assert result.returncode == 0, result.stdout
    assert set(statuses(design).values()) == {"done"}
    assert len(statuses(design)) == 12
    assert (design / "review-report.md").read_text().startswith("# Design review\n")


def test_food_delivery_passes() -> None:
    """REQ-QUALITY-004: the second domain has steps 01-05 done and no errors, under both presets."""
    first_five = ["brief", "functions", "subdomains", "context-map", "aggregates"]
    for folder in ("design", "design-detailed"):
        design = EXAMPLES / "food-delivery" / folder
        result = check(design)
        assert result.returncode == 0, (folder, result.stdout)
        done = [k for k, v in statuses(design).items() if v == "done"]
        assert done == first_five


def test_detailed_differs() -> None:
    """REQ-CONFIG-002: the detailed preset adds aggregate internals and external systems; high-level has neither."""
    base = EXAMPLES / "food-delivery"
    high = {n: yaml.safe_load((base / "design" / n).read_text()) for n in ("aggregates.yaml", "context-map.yaml")}
    det = {n: yaml.safe_load((base / "design-detailed" / n).read_text()) for n in ("aggregates.yaml", "context-map.yaml")}
    assert any(a["entities"] for a in det["aggregates.yaml"]["aggregates"])
    assert det["context-map.yaml"].get("externals")
    assert not any(a["entities"] or a["value_objects"] or a["events"] for a in high["aggregates.yaml"]["aggregates"])
    assert not high["context-map.yaml"].get("externals")
    assert yaml.safe_load((base / "design-detailed" / "sa-config.yaml").read_text())["profile"] == "detailed"


def test_neutral_content() -> None:
    """REQ-QUALITY-005: skills and examples name no real client, course, organisation or past project."""
    terms = [t.strip().lower() for t in (ROOT / "tests" / "deny-terms.txt").read_text().splitlines() if t.strip()]
    hits = []
    for folder in ("skills", "examples"):
        for path in (ROOT / folder).rglob("*"):
            skip = {"__pycache__", "node_modules"} & set(path.parts)
            if path.is_file() and path.suffix in {".md", ".yaml", ".py", ".json", ".drawio", ".js"} and not skip:
                text = path.read_text().lower()
                hits += [(str(path.relative_to(ROOT)), t) for t in terms if re.search(rf"\b{re.escape(t)}\b", text)]
    assert hits == []


DRAWN = {
    EXAMPLES / "clinic-booking" / "design": list(stamp.DRAWN),
    EXAMPLES / "food-delivery" / "design": ["functions", "subdomains", "context-map", "aggregates"],
    EXAMPLES / "food-delivery" / "design-detailed": ["functions", "subdomains", "context-map", "aggregates"],
}


def test_example_diagrams_up_to_date() -> None:
    """REQ-QUALITY-006: the examples ship their diagrams, each stamped with the hash of its current data."""
    refs = ROOT / "skills" / "sa-design" / "references"
    for design, keys in DRAWN.items():
        cfg = config.effective(design, refs)
        folder = design / "diagrams"
        drawn = sorted(p.name for p in folder.glob("[0-9][0-9]-*.drawio"))
        assert drawn == [f"{stamp.DRAWN[k][0]:02d}-{k}.drawio" for k in keys], design
        for key in keys:
            stem = f"{stamp.DRAWN[key][0]:02d}-{key}"
            assert stamp.read(folder / f"{stem}.drawio") == stamp.step_hash(design, key, cfg.options, cfg.cloud), stem
            assert (folder / f"{stem}.mermaid.md").exists(), stem
        assert (folder / "all-diagrams.drawio").exists()
        assert not [f for f in checks.run(design, refs)[1] if f.rule == "DG-01"]
