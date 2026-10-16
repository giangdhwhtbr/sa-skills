"""Deck checks: time budget, script length, references and stated counts (Track 3 of sad-ap6)."""

import shutil
from pathlib import Path
from typing import Any

import yaml
from sadeck import checks, schema

ROOT = Path(__file__).resolve().parents[1]
DECK_REFS = ROOT / "skills" / "sa-deck" / "references"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "deck" / "deck.yaml"


def findings(tmp_path: Path, mutate: Any = None) -> list[checks.Finding]:
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck"))
    (design / "deck").mkdir()
    data = yaml.safe_load(FIXTURE.read_text())
    if mutate:
        mutate(data, design)
    (design / "deck" / "deck.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    return checks.run(schema.load(design, DECK_REFS), design)


def slide(data: dict[str, Any], section: int, index: int) -> dict[str, Any]:
    return data["sections"][section]["slides"][index]


def test_fixture_is_clean(tmp_path: Path) -> None:
    assert findings(tmp_path) == []


# REQ-DECK-006
def test_over_budget_warns(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any], _: Path) -> None:
        d["meta"]["minutes"] = 20
        for section in d["sections"]:
            for s in section["slides"]:
                s["seconds"] = 260  # 5 x 260 + 20 = 1320 s
    found = findings(tmp_path, mutate)
    assert [(f.severity, f.slide) for f in found] == [("warn", 0)]
    assert "22:00" in found[0].message and "20:00" in found[0].message


# REQ-DECK-006
def test_long_script_warns(tmp_path: Path) -> None:
    found = findings(tmp_path, lambda d, _: slide(d, 1, 0).update(notes=" ".join(["word"] * 300)))
    assert [(f.severity, f.slide, f.field) for f in found] == [("warn", 4, "notes")]
    assert "60 s" in found[0].message
    assert findings(tmp_path / "b", lambda d, _: slide(d, 1, 0).update(notes=" ".join(["word"] * 100))) == []


# REQ-DECK-007
def test_unknown_diagram_page(tmp_path: Path) -> None:
    found = findings(tmp_path, lambda d, _: slide(d, 1, 0)["block"].update(page=2))
    assert [(f.severity, f.slide) for f in found] == [("error", 4)]
    found = findings(tmp_path / "b", lambda d, _: slide(d, 1, 0)["block"].update(step="brief"))
    assert [(f.severity, f.slide) for f in found] == [("error", 4)]


# REQ-DECK-007
def test_missing_diagram_file(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any], design: Path) -> None:
        (design / "diagrams" / "04-context-map.drawio").unlink()
    found = findings(tmp_path, mutate)
    assert [(f.severity, f.slide) for f in found] == [("error", 4)] and "/sa-diagrams" in found[0].message


# REQ-DECK-007
def test_wrong_service_count(tmp_path: Path) -> None:
    found = findings(tmp_path, lambda d, _: slide(d, 1, 0).update(message="Twelve services, one per subdomain"))
    assert [(f.severity, f.slide, f.field) for f in found] == [("error", 4, "message")]
    assert findings(tmp_path / "b", lambda d, _: slide(d, 1, 0).update(message="8 services, one per subdomain")) == []
    found = findings(tmp_path / "c", lambda d, _: slide(d, 0, 1)["block"]["rows"].append(["Scale", "Ten services"]))
    assert [(f.severity, f.slide, f.field) for f in found] == [("error", 3, "block.rows")]


# REQ-DECK-007
def test_image_outside_deck(tmp_path: Path) -> None:
    found = findings(tmp_path, lambda d, _: slide(d, 2, 0).update(block={"type": "image", "file": "../brief.yaml"}))
    assert [(f.severity, f.slide, f.field) for f in found] == [("error", 6, "block.file")]

    def missing(d: dict[str, Any], _: Path) -> None:
        slide(d, 2, 0).update(block={"type": "image", "file": "photo.png"})
    assert [f.severity for f in findings(tmp_path / "b", missing)] == ["error"]

    def logo(d: dict[str, Any], design: Path) -> None:
        d["theme"] = {"logo": "logo.png"}
    assert [(f.slide, f.field) for f in findings(tmp_path / "c", logo)] == [(1, "theme.logo")]


# REQ-DECK-007
def test_table_row_width_matches_header(tmp_path: Path) -> None:
    # an unquoted comma in a YAML flow list splits one cell into two
    found = findings(tmp_path, lambda d, _: slide(d, 0, 1)["block"]["rows"].append(["Spreadsheets", " so double bookings", "x"]))
    assert [(f.severity, f.slide, f.field) for f in found] == [("error", 3, "block.rows")]
    assert "3 cells" in found[0].message and "2 columns" in found[0].message
