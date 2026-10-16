"""deck.py CLI: writes only deck/, errors write nothing, outline, rebuilds, missing Node (Track 7 of sad-ap6)."""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from sadeck import pptx, run

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "sa-deck" / "scripts" / "deck.py"
DECK_REFS = ROOT / "skills" / "sa-deck" / "references"
SA_REFS = ROOT / "skills" / "sa-design" / "references"
TOOLS = ROOT / "skills" / "sa-deck" / "tools"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "deck" / "deck.yaml"
NO_DRAWIO = {**os.environ, "DRAWIO": "/nonexistent/draw.io"}


def make_design(tmp_path: Path, with_deck: bool = True) -> Path:
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck"))
    if with_deck:
        (design / "deck").mkdir()
        shutil.copy(FIXTURE, design / "deck" / "deck.yaml")
    return design


def build(design: Path, **kwargs: object) -> run.RunResult:
    return run.run(design, DECK_REFS, SA_REFS, tools_dir=TOOLS, **kwargs)


def cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True,
                          env=env or NO_DRAWIO, check=False)


def digests(design: Path) -> dict[str, str]:
    out = {}
    for path in sorted(design.rglob("*")):
        rel = path.relative_to(design)
        if path.is_file() and (rel.parts[0] != "deck" or rel.name == "deck.yaml"):
            out[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# REQ-DECK-001
def test_writes_only_deck(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    before = digests(design)
    result = build(design)
    assert result.exit_code == 0, result.errors
    assert digests(design) == before
    assert (design / "deck" / "deck.html").exists()
    assert (design / "deck" / "assets").is_dir()
    if pptx.available(TOOLS) is None:
        assert (design / "deck" / "deck.pptx").exists()
    assert result.written[0].startswith("deck.html (6 slides, 4:00 of 10:00)")


# REQ-DECK-007
def test_errors_write_nothing(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    data = yaml.safe_load(FIXTURE.read_text())
    data["sections"][1]["slides"][0]["message"] = "Twelve services, one per subdomain"
    (design / "deck" / "deck.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    done = cli(str(design))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "slide 4" in done.stdout
    assert not (design / "deck" / "deck.html").exists() and not (design / "deck" / "assets").exists()


# REQ-DECK-003
def test_schema_error_exit_1(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    (design / "deck" / "deck.yaml").write_text(FIXTURE.read_text().replace("type: agenda", "type: chart"))
    done = cli(str(design))
    assert done.returncode == 1 and "slide 2" in done.stdout


# REQ-DECK-002
def test_outline_and_missing_deck(tmp_path: Path) -> None:
    design = make_design(tmp_path, with_deck=False)
    done = cli(str(design))
    assert done.returncode == 2 and "--outline" in done.stderr
    done = cli(str(design), "--outline", "--minutes", "20")
    assert done.returncode == 0, done.stderr
    data = yaml.safe_load(done.stdout)
    assert data["meta"]["minutes"] == 20 and data["sections"][0]["title"] == "Agenda"
    assert not (design / "deck").exists()


# REQ-DECK-011
def test_unchanged_and_force(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    first = build(design, drawio_cmd=None)
    html = design / "deck" / "deck.html"
    if any("not exported" in w for w in first.warnings):
        # placeholders are never considered final: draw.io is missing here, so rebuilds are expected
        return
    stamp = html.stat().st_mtime_ns
    second = build(design)
    assert second.unchanged and second.written == [] and html.stat().st_mtime_ns == stamp
    forced = build(design, force=True)
    assert not forced.unchanged and forced.written
    deck_file = design / "deck" / "deck.yaml"
    deck_file.write_text(deck_file.read_text().replace("Thank you", "Thanks"))
    assert build(design).written


# REQ-DECK-011
def test_placeholders_force_rebuild(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    result = build(design, drawio_cmd="")  # "" = draw.io explicitly unavailable, no cached slide images
    assert result.exit_code == 0
    assert any("slide 4" in w and "/sa-diagrams --png" in w for w in result.warnings)
    assert "Diagram not exported" in (design / "deck" / "deck.html").read_text()
    assert not build(design, drawio_cmd="").unchanged  # a deck with placeholders is rebuilt next time


# REQ-DECK-009
def test_node_missing_keeps_html(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    done = cli(str(design), env={**NO_DRAWIO, "PATH": str(Path(sys.executable).parent)})
    assert done.returncode == 0, done.stdout + done.stderr
    assert (design / "deck" / "deck.html").exists() and not (design / "deck" / "deck.pptx").exists()
    assert "npm install" in done.stdout


def test_not_a_design_folder(tmp_path: Path) -> None:
    assert cli(str(tmp_path)).returncode == 2
