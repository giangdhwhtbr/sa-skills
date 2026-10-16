"""Load design/deck/deck.yaml, validate it and build the render model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .model import Block, Deck, DiagramRef, Slide, Theme

DECK_DIR = "deck"
DECK_FILE = "deck.yaml"


class DeckError(ValueError):
    """deck.yaml cannot be used; `problems` lists each one as 'slide N: field: message' or 'deck: field: ...'."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


def _slide_numbers(data: dict[str, Any]) -> list[list[int]]:
    numbers, n = [], 1
    for section in data.get("sections") or []:
        row = []
        for _ in (section or {}).get("slides") or []:
            n += 1
            row.append(n)
        numbers.append(row)
    return numbers


def _where(path: list[Any], numbers: list[list[int]]) -> str:
    """'slide N: rest.of.path' for a path inside a slide, else 'deck: path'."""
    if len(path) >= 4 and path[0] == "sections" and path[2] == "slides":
        try:
            n = numbers[path[1]][path[3]]
        except IndexError:
            n = 0
        rest = ".".join(str(p) for p in path[4:]) or "slide"
        return f"slide {n}: {rest}"
    if path and path[0] == "cover":
        return "slide 1: " + (".".join(str(p) for p in path[1:]) or "cover")
    return "deck: " + (".".join(str(p) for p in path) or "deck.yaml")


def _validate(data: Any, schema: dict[str, Any]) -> list[str]:
    root = {k: v for k, v in schema.items() if k != "$defs"}
    numbers = _slide_numbers(data) if isinstance(data, dict) else []
    problems = [f"{_where(list(e.absolute_path), numbers)}: {e.message}"
                for e in sorted(Draft202012Validator(root).iter_errors(data), key=lambda e: list(e.absolute_path))]
    if problems or not isinstance(data, dict):
        return problems
    for i, section in enumerate(data["sections"]):
        for j, slide in enumerate(section["slides"]):
            block = slide.get("block")
            if block is None:
                continue
            sub = Draft202012Validator(schema["$defs"][block["type"]])
            for e in sorted(sub.iter_errors(block), key=lambda e: list(e.absolute_path)):
                path = ["sections", i, "slides", j, "block", *e.absolute_path]
                problems.append(f"{_where(path, numbers)}: {e.message}")
    return problems


def _inside(deck_dir: Path, name: str) -> bool:
    try:
        (deck_dir / name).resolve().relative_to(deck_dir.resolve())
    except ValueError:
        return False
    return True


def _block(raw: dict[str, Any] | None) -> Block | None:
    if raw is None:
        return None
    kind = raw["type"]
    if kind == "diagrams":
        refs = [DiagramRef(raw[side]["step"], raw[side]["page"]) for side in ("left", "right")]
    elif kind in ("diagram", "diagram-text"):
        refs = [DiagramRef(raw["step"], raw["page"])]
    else:
        refs = []
    return Block(kind, items=list(raw.get("items") or []), header=list(raw.get("header") or []),
                 rows=[list(r) for r in raw.get("rows") or []], widths=list(raw.get("widths") or []),
                 diagrams=refs, file=raw.get("file"))


def load(design_dir: Path, refs: Path) -> Deck:
    """Read and validate deck.yaml. Raises DeckError with every problem found."""
    deck_dir = design_dir / DECK_DIR
    path = deck_dir / DECK_FILE
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as error:
        raise DeckError([f"deck: {DECK_FILE} is not valid YAML: {error}"]) from error
    schema = yaml.safe_load((refs / "deck.schema.yaml").read_text())
    problems = _validate(data, schema)
    theme_data = {**yaml.safe_load((refs / "theme.yaml").read_text()), **(data.get("theme") or {})} \
        if isinstance(data, dict) else {}
    logo = theme_data.get("logo")
    if logo and not _inside(deck_dir, logo):
        problems.append(f"deck: theme.logo: '{logo}' must be a file inside {DECK_DIR}/")
    if problems:
        raise DeckError(problems)

    meta = data["meta"]
    slides = [Slide(1, "cover", "", meta["title"], meta.get("subtitle", ""), None, data["cover"]["notes"],
                    data["cover"]["seconds"])]
    for section in data["sections"]:
        for raw in section["slides"]:
            slides.append(Slide(len(slides) + 1, "content", section["title"], raw["title"], raw.get("message", ""),
                                _block(raw.get("block")), raw["notes"], raw["seconds"]))
    theme = Theme(primary=theme_data["primary"], accent=theme_data["accent"], text=theme_data["text"],
                  muted=theme_data["muted"], font=theme_data["font"], logo=logo or None,
                  footer=theme_data.get("footer") or "")
    return Deck(meta["title"], meta.get("subtitle", ""), meta.get("presenter", ""), str(meta.get("date", "")),
                meta["minutes"], theme, slides, [s["title"] for s in data["sections"]])
