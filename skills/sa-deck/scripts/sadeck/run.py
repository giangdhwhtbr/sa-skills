"""One deck run: outline, or load + check + render deck.html and deck.pptx when the sources changed."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sadiagram import export

from . import assets, checks, html, outline, pptx, schema, stamp
from .assets import SlideImage
from .model import DiagramRef

HTML_FILE = "deck.html"
PPTX_FILE = "deck.pptx"


class UsageError(ValueError):
    """Wrong folder or a missing deck.yaml (exit 2)."""


@dataclass
class RunResult:
    written: list[str] = field(default_factory=list)
    unchanged: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = 0
    outline: str = ""


def _images(design_dir: Path, refs: list[DiagramRef], cmd: str | None,
            result: RunResult, slides: dict[DiagramRef, int]) -> dict[DiagramRef, SlideImage]:
    images = {}
    for ref in refs:
        try:
            image = assets.slide_image(design_dir, ref, cmd)
        except export.ExportError as error:
            image = SlideImage(None, 0, 0, assets.slide_xml(design_dir, ref)[1])
            result.warnings.append(f"slide {slides[ref]}: {error}")
        if image.path is None:
            result.warnings.append(f"slide {slides[ref]}: diagram {ref.step} page {ref.page} not exported; "
                                   "run /sa-diagrams --png or install draw.io desktop")
        images[ref] = image
    return images


def run(design_dir: Path, refs: Path, sa_refs: Path, outline: bool = False, minutes: int = 20,
        force: bool = False, tools_dir: Path | None = None, drawio_cmd: str | None = None) -> RunResult:
    """Build the deck of a design folder. drawio_cmd: None = find draw.io; "" = treat it as missing."""
    result = RunResult()
    if not (design_dir / "sa-config.yaml").is_file() or not (design_dir / "design-state.yaml").is_file():
        raise UsageError(f"{design_dir}: not a design folder (sa-config.yaml and design-state.yaml are required)")
    if outline:
        result.outline = _outline(design_dir, sa_refs, minutes)
        return result
    deck_dir = design_dir / schema.DECK_DIR
    if not (deck_dir / schema.DECK_FILE).is_file():
        raise UsageError(f"{deck_dir / schema.DECK_FILE} not found; draft it first with --outline")
    tools = tools_dir or Path(__file__).resolve().parents[2] / "tools"

    try:
        deck = schema.load(design_dir, refs)
    except schema.DeckError as error:
        result.errors, result.exit_code = error.problems, 1
        return result
    found = checks.run(deck, design_dir)
    result.errors = [f"slide {f.slide}: {f.field}: {f.message}" if f.slide else f"deck: {f.field}: {f.message}"
                     for f in found if f.severity == "error"]
    result.warnings = [f"slide {f.slide}: {f.message}" if f.slide else f"deck: {f.message}"
                       for f in found if f.severity == "warn"]
    if result.errors:
        result.exit_code = 1
        return result

    pptx_hint = pptx.available(tools)
    current = stamp.deck_hash(design_dir)
    outputs = [deck_dir / HTML_FILE] + ([] if pptx_hint else [deck_dir / PPTX_FILE])
    if not force and stamp.read(design_dir) == current and all(p.exists() for p in outputs):
        result.unchanged = True
        return result

    slides = {ref: s.number for s in deck.slides if s.block for ref in s.block.diagrams}
    cmd = export.find_drawio() if drawio_cmd is None else (drawio_cmd or None)
    images = _images(design_dir, list(slides), cmd, result, slides)
    (deck_dir / HTML_FILE).write_text(html.render(deck, images, design_dir))
    result.written.append(f"{HTML_FILE} ({len(deck.slides)} slides, {html.clock(deck.seconds)} of "
                          f"{html.clock(deck.minutes * 60)})")
    if pptx_hint:
        result.warnings.append(f"pptx skipped: {pptx_hint}")
    else:
        try:
            pptx.render(deck, images, design_dir, deck_dir / PPTX_FILE, tools)
        except pptx.PptxError as error:
            result.errors, result.exit_code = [str(error)], 2
            return result
        result.written.append(PPTX_FILE)

    placeholders = any(i.path is None for i in images.values())
    stamp_file = deck_dir / stamp.STAMP_FILE
    if placeholders:  # not final: rebuild once the diagrams can be exported
        stamp_file.unlink(missing_ok=True)
    else:
        stamp.write(design_dir, current)
    return result


def _outline(design_dir: Path, sa_refs: Path, minutes: int) -> str:
    return outline.draft(design_dir, sa_refs, minutes)
