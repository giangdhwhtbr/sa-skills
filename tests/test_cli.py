"""check.py command-line tests."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "sa-review" / "scripts" / "check.py"
CLEAN = Path(__file__).resolve().parent / "fixtures" / "clean" / "design"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECK), *args], capture_output=True, text=True, check=False)


def broken(tmp_path: Path) -> Path:
    target = tmp_path / "design"
    shutil.copytree(CLEAN, target)
    saga = yaml.safe_load((target / "saga.yaml").read_text())
    saga["participants"].append("unknown-svc")
    (target / "saga.yaml").write_text(yaml.safe_dump(saga, sort_keys=False))
    return target


def test_clean_exit_zero() -> None:
    """REQ-REVIEW-006: no errors -> exit 0 and a summary line."""
    result = run(str(CLEAN))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().splitlines()[-1] == "0 errors, 0 warnings"


def test_broken_reference_exit_one(tmp_path: Path) -> None:
    """REQ-REVIEW-006: an error finding -> exit 1 and one line per finding, errors first."""
    result = run(str(broken(tmp_path)))
    assert result.returncode == 1
    assert result.stdout.splitlines()[0].startswith("ERROR XS-01 saga.yaml unknown-svc:")
    assert result.stdout.strip().splitlines()[-1] == "1 errors, 0 warnings"


def test_missing_directory_exit_two(tmp_path: Path) -> None:
    """REQ-REVIEW-006: unreadable input -> exit 2."""
    result = run(str(tmp_path / "nope"))
    assert result.returncode == 2
    assert "not a design folder" in result.stderr


def test_json_format(tmp_path: Path) -> None:
    """REQ-REVIEW-006: --format json gives config, findings and exceptions."""
    result = run(str(broken(tmp_path)), "--format", "json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert set(payload) == {"config", "findings", "exceptions"}
    assert payload["config"]["profile"] == "high-level"
    assert payload["findings"][0]["rule"] == "XS-01"


def test_dependents_flag() -> None:
    """REQ-DESIGN-006: --dependents prints the steps that read a step's data."""
    result = run(str(CLEAN), "--dependents", "subdomains")
    assert result.returncode == 0
    assert result.stdout.split() == [
        "context-map", "aggregates", "logical-view", "saga", "patterns", "architecture", "stack", "adrs",
    ]


def test_step_flag_limits_scope(tmp_path: Path) -> None:
    """REQ-DESIGN-009: --step checks one step only."""
    result = run(str(broken(tmp_path)), "--step", "context-map")
    assert result.returncode == 0


def test_unknown_step_exit_two() -> None:
    """REQ-REVIEW-006: a bad --step value is a usage error."""
    result = run(str(CLEAN), "--step", "nowhere")
    assert result.returncode == 2


def test_changed_flag(tmp_path: Path) -> None:
    """REQ-DESIGN-008: --changed lists files edited after their recorded hash."""
    target = tmp_path / "design"
    shutil.copytree(CLEAN, target)
    state = yaml.safe_load((target / "design-state.yaml").read_text())
    state["steps"][0]["files"] = {"brief.yaml": "0" * 64}
    (target / "design-state.yaml").write_text(yaml.safe_dump(state, sort_keys=False))
    result = run(str(target), "--changed")
    assert result.returncode == 0
    assert result.stdout.split() == ["brief.yaml"]
