"""Shared pytest fixtures."""

import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "sa-design" / "references"
TEMPLATES = REFS / "templates"

# Authoritative option table from the plan; used to stub step guides that do not exist yet.
OPTION_TABLE: dict[str, dict[str, dict[str, object]]] = {
    "subdomains": {"service-per-subdomain": {"values": ["one", "allow-shared"], "default": "one"}},
    "context-map": {"detail": {"values": ["ud-only", "with-patterns", "with-externals"], "default": "ud-only"}},
    "aggregates": {"detail": {"values": ["roots-only", "full"], "default": "roots-only"}},
    "logical-view": {"vendors": {"values": ["none", "technology-hints", "named-services"], "default": "none"}},
    "saga": {"failure-scenarios": {"values": [1, 2, 3], "default": 2}},
    "patterns": {"split": {"values": ["one-per-pattern", "combined"], "default": "one-per-pattern"}},
    "architecture": {"shared-layout": {"values": [True, False], "default": True}},
}
STEP_ORDER = [
    "brief", "functions", "subdomains", "context-map", "aggregates", "use-cases",
    "logical-view", "saga", "patterns", "architecture", "stack", "adrs",
]


@pytest.fixture
def refs_dir() -> Path:
    """The plugin's real reference directory."""
    return REFS


@pytest.fixture
def stub_refs(tmp_path: Path) -> Path:
    """A copy of the references where every missing step guide is a front-matter-only stub."""
    target = tmp_path / "refs"
    shutil.copytree(REFS, target)
    steps = target / "steps"
    steps.mkdir(exist_ok=True)
    for number, key in enumerate(STEP_ORDER, 1):
        if list(steps.glob(f"{number:02d}-*.md")):
            continue
        front = {
            "number": number, "key": key, "title": key, "markdown": f"{number:02d}-{key}.md",
            "data": f"{key}.yaml", "schema": f"{key}.schema.yaml", "inputs": [],
            "options": {
                name: {**spec, "affects": "stub"} for name, spec in OPTION_TABLE.get(key, {}).items()
            },
            "rules": [],
        }
        (steps / f"{number:02d}-{key}.md").write_text("---\n" + yaml.safe_dump(front, sort_keys=False) + "---\n")
    return target


@pytest.fixture
def design_dir(tmp_path: Path) -> Path:
    """A fresh design folder made from the templates."""
    target = tmp_path / "design"
    target.mkdir()
    for name in ("sa-config.yaml", "design-state.yaml"):
        shutil.copy(TEMPLATES / name, target / name)
    return target
