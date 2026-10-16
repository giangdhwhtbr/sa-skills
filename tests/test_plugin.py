"""Plugin packaging tests."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_names_two_skills() -> None:
    """REQ-PLUGIN-001: the plugin exposes exactly the sa-design and sa-review skills."""
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "sa-design-kit"
    assert manifest["version"]
    skills = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
    assert skills == ["sa-design", "sa-review"]


def test_marketplace_points_at_repository_root() -> None:
    """REQ-PLUGIN-001: installable from a local path or marketplace entry."""
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = market["plugins"]
    assert [e["name"] for e in entries] == ["sa-design-kit"]
    assert entries[0]["source"] == "./"


def test_skill_front_matter_has_name_and_description() -> None:
    """REQ-PLUGIN-001: each skill declares its name and when to use it."""
    for name in ("sa-design", "sa-review"):
        text = (ROOT / "skills" / name / "SKILL.md").read_text()
        assert text.startswith("---\n")
        head = text.split("---\n")[1]
        assert f"name: {name}" in head
        assert "description:" in head
