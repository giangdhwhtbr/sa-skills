"""Deck checks: time budget and script length (warnings), references and stated facts (errors)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from sacheck.checks import _COUNT, NUMBER_WORDS

from .assets import page_pages
from .model import Block, Deck, Slide
from .stamp import NUMBERS

WORDS_PER_MINUTE = 130
SCRIPT_SLACK = 1.15


@dataclass(frozen=True)
class Finding:
    severity: str      # error | warn
    slide: int         # 0 = the whole deck
    field: str
    message: str


def _clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _inside(deck_dir: Path, name: str) -> bool:
    try:
        (deck_dir / name).resolve().relative_to(deck_dir.resolve())
    except ValueError:
        return False
    return True


def _file(deck_dir: Path, name: str, slide: int, field: str) -> list[Finding]:
    if not _inside(deck_dir, name):
        return [Finding("error", slide, field, f"'{name}' must be a file inside deck/")]
    if not (deck_dir / name).is_file():
        return [Finding("error", slide, field, f"'{name}' does not exist in deck/")]
    return []


def _texts(slide: Slide) -> list[tuple[str, str]]:
    out = [("title", slide.title), ("message", slide.message), ("notes", slide.notes)]
    block: Block | None = slide.block
    if block is not None:
        out += [("block.items", t) for t in block.items]
        out += [("block.header", t) for t in block.header]
        out += [("block.rows", cell) for row in block.rows for cell in row]
    return out


def _services(design_dir: Path) -> int | None:
    try:
        data = yaml.safe_load((design_dir / "subdomains.yaml").read_text()) or {}
    except (OSError, yaml.YAMLError):
        return None
    return len({s["service"]["id"] for s in data.get("subdomains", [])})


def run(deck: Deck, design_dir: Path) -> list[Finding]:
    """Every finding on a loaded deck, in slide order (deck-wide findings first)."""
    deck_dir = design_dir / "deck"
    found: list[Finding] = []

    budget = deck.minutes * 60
    if deck.seconds > budget:
        found.append(Finding("warn", 0, "seconds",
                             f"deck runs {_clock(deck.seconds)} against a {_clock(budget)} budget"))
    if deck.theme.logo:
        found += _file(deck_dir, deck.theme.logo, 1, "theme.logo")

    services = _services(design_dir)
    for slide in deck.slides:
        spoken = len(slide.notes.split()) * 60 / WORDS_PER_MINUTE
        if spoken > slide.seconds * SCRIPT_SLACK:
            found.append(Finding("warn", slide.number, "notes",
                                 f"notes run about {round(spoken)} s for {slide.seconds} s"))
        block = slide.block
        if block is not None:
            for ref in block.diagrams:
                if ref.step not in NUMBERS:
                    found.append(Finding("error", slide.number, "block.step",
                                         f"'{ref.step}' has no diagram; drawable steps: {', '.join(NUMBERS)}"))
                    continue
                pages = page_pages(design_dir, ref.step)
                if pages == 0:
                    found.append(Finding("error", slide.number, "block.step",
                                         f"no diagram for '{ref.step}'; run /sa-diagrams first"))
                elif ref.page > pages:
                    found.append(Finding("error", slide.number, "block.page",
                                         f"'{ref.step}' has {pages} page(s), not page {ref.page}"))
            if block.kind == "image" and block.file:
                found += _file(deck_dir, block.file, slide.number, "block.file")
        if services is not None:
            for field, text in _texts(slide):
                for match in _COUNT.finditer(text):
                    word = match.group(1).lower()
                    stated = int(word) if word.isdigit() else NUMBER_WORDS[word]
                    if stated != services:
                        found.append(Finding("error", slide.number, field,
                                             f"states {stated} services; subdomains.yaml has {services}"))
    return found
