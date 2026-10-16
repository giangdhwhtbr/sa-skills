"""Proposed outline in 4+1 order (Track 2 of sad-ap6)."""

import shutil
from pathlib import Path

import yaml
from sadeck import outline, schema

ROOT = Path(__file__).resolve().parents[1]
SA_REFS = ROOT / "skills" / "sa-design" / "references"
DECK_REFS = ROOT / "skills" / "sa-deck" / "references"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FOOD = ROOT / "examples" / "food-delivery" / "design"


def sections(text: str) -> list[dict]:
    return yaml.safe_load(text)["sections"]


def total(data: dict) -> int:
    return data["cover"]["seconds"] + sum(s["seconds"] for sec in data["sections"] for s in sec["slides"])


# REQ-DECK-002
def test_outline_clinic_full() -> None:
    text = outline.draft(CLINIC, SA_REFS, 20)
    data = yaml.safe_load(text)
    titles = [s["title"] for s in data["sections"]]
    assert titles == ["Agenda", "Introduction", "Domain design", "Use case view", "Logical view", "Process view",
                      "Core patterns", "High-level and physical view", "Development view", "Q&A"]
    count = {s["title"]: len(s["slides"]) for s in data["sections"]}
    assert count["Use case view"] == 3 and count["Process view"] == 3 and count["Core patterns"] == 3
    assert count["High-level and physical view"] == 2 and count["Development view"] >= 2
    assert total(data) <= 1200
    assert all(s["seconds"] >= 15 and s["seconds"] % 5 == 0 for sec in data["sections"] for s in sec["slides"])
    domain = next(s for s in data["sections"] if s["title"] == "Domain design")["slides"]
    assert [s["block"] for s in domain][1] == {"type": "diagram", "step": "context-map", "page": 1}
    intro = next(s for s in data["sections"] if s["title"] == "Introduction")["slides"]
    pains = yaml.safe_load((CLINIC / "brief.yaml").read_text())["pain_points"]
    assert [r[0] for r in intro[0]["block"]["rows"]] == [p["text"] for p in pains]
    assert data["meta"]["minutes"] == 20


# REQ-DECK-002
def test_outline_partial() -> None:
    data = yaml.safe_load(outline.draft(FOOD, SA_REFS, 10))
    assert [s["title"] for s in data["sections"]] == ["Agenda", "Introduction", "Domain design", "Q&A"]
    assert total(data) <= 600
    steps = {s["block"]["step"] for sec in data["sections"] for s in sec["slides"] if "step" in s.get("block", {})}
    assert steps <= {"functions", "subdomains", "context-map", "aggregates"}


# REQ-DECK-002
def test_outline_tight_budget_stays_within() -> None:
    data = yaml.safe_load(outline.draft(CLINIC, SA_REFS, 8))
    assert total(data) <= 480


# REQ-DECK-002, REQ-DECK-003
def test_outline_parses(tmp_path: Path) -> None:
    text = outline.draft(CLINIC, SA_REFS, 20)
    assert text.startswith("#")  # instructions for the author
    data = yaml.safe_load(text)
    data["cover"]["notes"] = "x"
    for section in data["sections"]:
        for slide in section["slides"]:
            slide["message"], slide["notes"] = "x", "x"
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck"))
    (design / "deck").mkdir()
    (design / "deck" / "deck.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    deck = schema.load(design, DECK_REFS)
    assert deck.slides[0].kind == "cover" and len(deck.slides) > 15
