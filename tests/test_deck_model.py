"""Render model, deck.yaml schema, theme and deck hash (Track 1 of sad-ap6)."""

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from sadeck import schema, stamp

ROOT = Path(__file__).resolve().parents[1]
DECK_REFS = ROOT / "skills" / "sa-deck" / "references"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "deck" / "deck.yaml"


def make_design(tmp_path: Path, mutate: Any = None) -> Path:
    """A copy of the clinic-booking design with the fixture deck (optionally changed)."""
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck"))
    (design / "deck").mkdir()
    data = yaml.safe_load(FIXTURE.read_text())
    if mutate:
        mutate(data)
    (design / "deck" / "deck.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    return design


# REQ-DECK-003
def test_valid_deck_loads(tmp_path: Path) -> None:
    deck = schema.load(make_design(tmp_path), DECK_REFS)
    assert [s.number for s in deck.slides] == list(range(1, 7))
    assert deck.slides[0].kind == "cover" and deck.slides[0].title == "Clinic booking platform"
    assert deck.sections == ["Introduction", "Domain design", "Close"]
    assert deck.slides[3].block.kind == "diagram"
    assert deck.slides[3].block.diagrams[0].step == "context-map" and deck.slides[3].block.diagrams[0].page == 1
    assert deck.slides[4].block.items == ["One gateway for web and mobile", "Every service owns its data"]
    assert deck.slides[5].block is None
    assert deck.minutes == 10
    defaults = yaml.safe_load((DECK_REFS / "theme.yaml").read_text())
    assert deck.theme.primary == defaults["primary"] and deck.theme.font == defaults["font"]


def _slide(data: dict[str, Any], section: int, slide: int) -> dict[str, Any]:
    return data["sections"][section]["slides"][slide]


BAD = {
    "unknown block type": (lambda d: _slide(d, 1, 0)["block"].update(type="chart"), "slide 4", "block"),
    "seven bullets": (lambda d: _slide(d, 1, 0).update(block={"type": "bullets", "items": ["x"] * 7}), "slide 4", "items"),
    "nine table rows": (lambda d: _slide(d, 0, 1)["block"].update(rows=[["a", "b"]] * 9), "slide 3", "rows"),
    "diagram-text one item": (lambda d: _slide(d, 1, 1)["block"].update(items=["only"]), "slide 5", "items"),
    "empty notes": (lambda d: _slide(d, 2, 0).update(notes=""), "slide 6", "notes"),
    "zero seconds": (lambda d: _slide(d, 0, 0).update(seconds=0), "slide 2", "seconds"),
    "missing minutes": (lambda d: d["meta"].pop("minutes"), "deck", "minutes"),
}


# REQ-DECK-003
@pytest.mark.parametrize("case", sorted(BAD))
def test_schema_rejects(case: str, tmp_path: Path) -> None:
    mutate, where, field = BAD[case]
    design = make_design(tmp_path, mutate)
    with pytest.raises(schema.DeckError) as caught:
        schema.load(design, DECK_REFS)
    assert any(p.startswith(where) and field in p for p in caught.value.problems), caught.value.problems


# REQ-DECK-010
def test_custom_theme(tmp_path: Path) -> None:
    design = make_design(tmp_path, lambda d: d.update(theme={"primary": "#0B5394", "footer": "Review"}))
    deck = schema.load(design, DECK_REFS)
    assert deck.theme.primary == "#0B5394" and deck.theme.footer == "Review"
    bad = make_design(tmp_path / "b", lambda d: d.update(theme={"logo": "../x.png"}))
    with pytest.raises(schema.DeckError):
        schema.load(bad, DECK_REFS)


# REQ-DECK-011
def test_deck_hash(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    first = stamp.deck_hash(design)
    assert first == stamp.deck_hash(design)
    deck_file = design / "deck" / "deck.yaml"
    deck_file.write_text(deck_file.read_text() + "\n")
    second = stamp.deck_hash(design)
    assert second != first
    (design / "deck" / "logo.png").write_bytes(b"one")
    deck_file.write_text(deck_file.read_text().replace("meta:\n", "theme: {logo: logo.png}\nmeta:\n", 1))
    third = stamp.deck_hash(design)
    (design / "deck" / "logo.png").write_bytes(b"two")
    assert stamp.deck_hash(design) != third
    # a referenced diagram page changes the hash, an unreferenced one does not
    before = stamp.deck_hash(design)
    unreferenced = design / "diagrams" / "02-functions.drawio"
    unreferenced.write_text(unreferenced.read_text().replace("Main business functions", "Functions"))
    assert stamp.deck_hash(design) == before
    referenced = design / "diagrams" / "04-context-map.drawio"
    referenced.write_text(referenced.read_text().replace("Context map", "Context map (v2)"))
    assert stamp.deck_hash(design) != before


def test_stamp_read_write(tmp_path: Path) -> None:
    design = make_design(tmp_path)
    assert stamp.read(design) is None
    stamp.write(design, "abc")
    assert stamp.read(design) == "abc"


# REQ-DECK-011
def test_step_numbers_match_diagrams() -> None:
    from sadiagram import stamp as diagram_stamp

    assert stamp.NUMBERS == {key: number for key, (number, _, _) in diagram_stamp.DRAWN.items()}
