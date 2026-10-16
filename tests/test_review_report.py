"""Review report rendering tests."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from sacheck import review_md

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "sa-review" / "scripts" / "check.py"
CLEAN = Path(__file__).resolve().parent / "fixtures" / "clean" / "design"
HEADINGS = ["# Design review", "## Configuration", "## Summary", "## Errors", "## Warnings",
            "## Accepted exceptions", "## Step status"]


def exception_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "design"
    shutil.copytree(CLEAN, target)
    logical = yaml.safe_load((target / "logical.yaml").read_text())
    logical["layers"][3]["components"][0]["name"] = "Kafka broker"
    (target / "logical.yaml").write_text(yaml.safe_dump(logical, sort_keys=False))
    state = yaml.safe_load((target / "design-state.yaml").read_text())
    for step in state["steps"]:
        if step["key"] == "logical-view":
            step["exceptions"] = [{"rule": "LV-01", "reason": "Broker product fixed by contract"}]
    (target / "design-state.yaml").write_text(yaml.safe_dump(state, sort_keys=False))
    config = yaml.safe_load((target / "sa-config.yaml").read_text())
    config["rules"] = {"LV-01": "warn"}
    (target / "sa-config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    return target


def check_json(design: Path) -> dict:
    result = subprocess.run([sys.executable, str(CHECK), str(design), "--format", "json"],
                            capture_output=True, text=True, check=False)
    return json.loads(result.stdout)


def test_render_order(tmp_path: Path) -> None:
    """REQ-REVIEW-001: the report starts with the effective configuration and lists findings errors first."""
    design = exception_fixture(tmp_path)
    state = yaml.safe_load((design / "design-state.yaml").read_text())
    judgement = [{"rule": "DOC-01", "severity": "warn", "file": "07-logical-view.md", "item": "title",
                  "message": "Title says logical view; content shows deployment"}]
    text = review_md.render(check_json(design), judgement, state)
    positions = [text.find(h + "\n") for h in HEADINGS]
    assert all(p >= 0 for p in positions) and positions == sorted(positions)
    config = text.split("## Configuration\n", 1)[1].split("\n## ", 1)[0]
    assert "high-level" in config and "LV-01: warn" in config
    warnings = text.split("## Warnings\n", 1)[1].split("\n## ", 1)[0]
    assert "DOC-01" in warnings


def test_exceptions_listed_separately(tmp_path: Path) -> None:
    """REQ-REVIEW-003: an accepted exception appears with its reason under Accepted exceptions, not Errors."""
    design = exception_fixture(tmp_path)
    state = yaml.safe_load((design / "design-state.yaml").read_text())
    text = review_md.render(check_json(design), [], state)
    errors = text.split("## Errors\n", 1)[1].split("\n## ", 1)[0]
    accepted = text.split("## Accepted exceptions\n", 1)[1].split("\n## ", 1)[0]
    assert "LV-01" not in errors
    assert "LV-01" in accepted and "Broker product fixed by contract" in accepted


def test_step_status_listed(tmp_path: Path) -> None:
    """REQ-REVIEW-002: the report lists every step with its status."""
    state = yaml.safe_load((CLEAN / "design-state.yaml").read_text())
    text = review_md.render(check_json(CLEAN), [], state)
    status = text.split("## Step status\n", 1)[1]
    assert status.count("| done |") == 12


def test_render_report_writes_only_the_report(tmp_path: Path) -> None:
    """REQ-REVIEW-001: the review writes review-report.md and changes no other design file."""
    import hashlib
    design = tmp_path / "design"
    shutil.copytree(CLEAN, design)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in design.iterdir()}
    script = ROOT / "skills" / "sa-review" / "scripts" / "render_report.py"
    result = subprocess.run([sys.executable, str(script), str(design)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in design.iterdir()}
    assert set(after) - set(before) == {"review-report.md"}
    assert {k: after[k] for k in before} == before
    assert (design / "review-report.md").read_text().startswith("# Design review\n")
