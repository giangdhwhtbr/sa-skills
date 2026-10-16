"""The diagrams CLI: checks first, step selection, outputs, incremental runs, dependencies (Track 7 of sad-qwi)."""

import hashlib
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from sadiagram import elk, export, run

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "sa-design" / "references"
TOOLS = ROOT / "skills" / "sa-diagrams" / "tools"
CLI = ROOT / "skills" / "sa-diagrams" / "scripts" / "diagrams.py"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FOOD = ROOT / "examples" / "food-delivery" / "design"
ALL_STEMS = ["02-functions", "03-subdomains", "04-context-map", "05-aggregates", "06-use-cases",
             "07-logical-view", "08-saga", "09-patterns", "10-architecture"]

needs_elk = pytest.mark.skipif(elk.available(TOOLS) is not None, reason="Node or elkjs not installed")


def copy_design(tmp_path: Path, source: Path) -> Path:
    target = tmp_path / "design"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("diagrams"))
    return target


def draw(design: Path, *, only: list[str] | None = None, png: bool = False, force: bool = False,
         drawio_cmd: str | None = None) -> run.RunResult:
    return run.run(design, REFS, only=only, png=png, force=force, tools_dir=TOOLS, drawio_cmd=drawio_cmd)


def cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, env=env, check=False)


def digests(folder: Path) -> dict[str, str]:
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and "diagrams" not in p.relative_to(folder).parts}


# REQ-DIAGRAMS-001
@needs_elk
def test_writes_only_diagrams(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    before = digests(design)
    result = draw(design)
    assert result.exit_code == 0
    assert digests(design) == before
    files = {p.name for p in (design / "diagrams").iterdir()}
    for stem in ALL_STEMS:
        assert {f"{stem}.drawio", f"{stem}.mermaid.md"} <= files
    assert "all-diagrams.drawio" in files
    assert [w.split(" ")[0] for w in result.written] == [f"{s}.drawio" for s in ALL_STEMS]


# REQ-DIAGRAMS-002
def test_errors_stop_drawing(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    saga = design / "saga.yaml"
    data = yaml.safe_load(saga.read_text())
    data["scenarios"][0]["steps"][1]["to"] = "ghost-service"
    saga.write_text(yaml.safe_dump(data, sort_keys=False))
    done = cli(str(design))
    assert done.returncode == 1, done.stdout + done.stderr
    assert not (design / "diagrams").exists()
    assert "saga" in done.stdout + done.stderr


# REQ-DIAGRAMS-003
@needs_elk
def test_partial_design(tmp_path: Path) -> None:
    design = copy_design(tmp_path, FOOD)
    result = draw(design)
    assert result.exit_code == 0
    assert [w.split(" ")[0] for w in result.written] == [f"{s}.drawio" for s in ALL_STEMS[:4]]
    assert [s.split(" ")[0] for s in result.skipped] == ALL_STEMS[4:]
    assert all("(todo)" in s for s in result.skipped)


# REQ-DIAGRAMS-004
@needs_elk
def test_consolidated_file(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    draw(design)
    names = [d.get("name") for d in ET.parse(design / "diagrams" / "all-diagrams.drawio").getroot().findall("diagram")]
    numbers = [n.split(" ")[0] for n in names]
    assert numbers == sorted(numbers) and numbers[0] == "02" and numbers[-1] == "10"
    expected = sum(len(ET.parse(design / "diagrams" / f"{s}.drawio").getroot().findall("diagram")) for s in ALL_STEMS)
    assert len(names) == expected


# REQ-DIAGRAMS-012
@needs_elk
def test_incremental(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    draw(design)
    second = draw(design)
    assert second.written == [] and len(second.unchanged) == len(ALL_STEMS)
    path = design / "context-map.yaml"
    path.write_text(path.read_text() + "# reviewed\n")
    third = draw(design)
    assert [w.split(" ")[0] for w in third.written] == ["04-context-map.drawio"]
    forced = draw(design, force=True)
    assert len(forced.written) == len(ALL_STEMS)


# REQ-DIAGRAMS-003
def test_unknown_only_key(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    done = cli(str(design), "--only", "brief")
    assert done.returncode == 2
    assert "functions" in done.stderr  # lists the drawable steps
    assert not (design / "diagrams").exists()


# REQ-DIAGRAMS-010
def test_node_missing(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    env = {**os.environ, "PATH": ""}
    done = cli(str(design), env=env)
    assert done.returncode == 2
    assert "npm install" in done.stderr
    assert not (design / "diagrams").exists()
    done = cli(str(design), "--only", "functions", "subdomains", env=env)
    assert done.returncode == 0, done.stderr
    assert (design / "diagrams" / "02-functions.drawio").exists()
    assert (design / "diagrams" / "03-subdomains.mermaid.md").exists()


# REQ-DIAGRAMS-011
def test_png_without_drawio(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    done = cli(str(design), "--only", "functions", "--png", env={**os.environ, "DRAWIO": "/nonexistent/draw.io"})
    assert done.returncode == 0, done.stderr
    assert "draw.io CLI not found" in done.stdout + done.stderr
    assert (design / "diagrams" / "02-functions.drawio").exists()
    assert not (design / "diagrams" / "png").exists()


def test_find_drawio(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = tmp_path / "drawio"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setenv("DRAWIO", str(fake))
    assert export.find_drawio() == str(fake)
    monkeypatch.setenv("DRAWIO", str(tmp_path / "missing"))
    assert export.find_drawio() is None


# REQ-DIAGRAMS-011
@pytest.mark.skipif(export.find_drawio() is None, reason="draw.io desktop not installed")
def test_png_cache(tmp_path: Path) -> None:
    design = copy_design(tmp_path, CLINIC)
    first = draw(design, only=["subdomains", "patterns"], png=True)
    assert first.exit_code == 0 and first.png_exported == 4 and first.png_cached == 0, first.warnings
    pngs = sorted(p.name for p in (design / "diagrams" / "png").glob("*.png"))
    assert pngs == ["03-subdomains-p1.png", "09-patterns-p1.png", "09-patterns-p2.png", "09-patterns-p3.png"]
    assert all((design / "diagrams" / "png" / n).read_bytes()[:4] == b"\x89PNG" for n in pngs)
    second = draw(design, only=["subdomains", "patterns"], png=True)
    assert second.png_exported == 0 and second.png_cached == 4
