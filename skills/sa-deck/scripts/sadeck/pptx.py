"""Render a deck as an editable PowerPoint: the render model as JSON -> node tools/pptx.js (pptxgenjs)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .assets import Chip, SlideImage
from .model import Block, Deck, DiagramRef, Slide

TIMEOUT = 180
_BOLD = re.compile(r"(\*\*.+?\*\*)")


class PptxError(RuntimeError):
    """pptxgenjs could not write the file."""


def install_hint(tools_dir: Path) -> str:
    return f"npm install --prefix {tools_dir}"


def available(tools_dir: Path) -> str | None:
    """None when the PowerPoint renderer can run; otherwise what to install."""
    if shutil.which("node") is None:
        return f"Node.js (18 or newer) is not installed; install it, then run: {install_hint(tools_dir)}"
    if not (tools_dir / "node_modules" / "pptxgenjs").is_dir():
        return f"pptxgenjs is not installed; run: {install_hint(tools_dir)}"
    return None


def runs(text: str) -> list[list[Any]]:
    """'a **b** c' -> [['a ', False], ['b', True], [' c', False]]."""
    out: list[list[Any]] = []
    for part in _BOLD.split(text):
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append([part[2:-2], True])
        elif part:
            out.append([part, False])
    return out or [["", False]]


def _hex(colour: str) -> str:
    return colour.lstrip("#").upper()


def _image(image: SlideImage) -> dict[str, Any]:
    return {"path": str(image.path) if image.path else None, "w": image.width, "h": image.height}


def _chip(chip: Chip) -> dict[str, Any]:
    fill = "" if chip.fill in ("", "none") else _hex(chip.fill)
    return {"kind": chip.kind, "label": chip.label, "fill": fill, "stroke": _hex(chip.stroke), "dashed": chip.dashed}


def _chips(images: list[SlideImage]) -> list[dict[str, Any]]:
    seen: list[Chip] = []
    for image in images:
        for chip in image.chips:
            if all((c.kind, c.label) != (chip.kind, chip.label) for c in seen):
                seen.append(chip)
    return [_chip(c) for c in seen]


def _agenda(deck: Deck, slide: Slide) -> list[dict[str, Any]]:
    out = []
    for title in deck.sections:
        if title == slide.section:
            continue
        numbers = [s.number for s in deck.slides if s.section == title]
        pages = f"{numbers[0]}" if len(numbers) == 1 else f"{numbers[0]}–{numbers[-1]}"
        out.append({"n": len(out) + 1, "title": title, "pages": pages})
    return out


def _block(deck: Deck, slide: Slide, images: dict[DiagramRef, SlideImage], design_dir: Path) -> dict[str, Any] | None:
    block: Block | None = slide.block
    if block is None:
        return None
    data: dict[str, Any] = {"kind": block.kind}
    if block.kind in ("bullets", "diagram-text"):
        data["items"] = [runs(i) for i in block.items]
    if block.kind == "table":
        data["header"] = [runs(h) for h in block.header]
        data["rows"] = [[runs(c) for c in row] for row in block.rows]
        data["widths"] = block.widths
    if block.diagrams:
        pictures = [images[ref] for ref in block.diagrams]
        data["images"] = [_image(p) for p in pictures]
        data["chips"] = _chips(pictures)
    if block.kind == "agenda":
        data["agenda"] = _agenda(deck, slide)
    if block.kind == "image" and block.file:
        path = design_dir / "deck" / block.file
        size = _size(path)
        data["images"] = [{"path": str(path.resolve()), "w": size[0], "h": size[1]}]
    return data


def _size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    i = 2  # JPEG: walk the segments to the frame header
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + length
    return 4, 3


def to_json(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path) -> dict[str, Any]:
    theme = deck.theme
    logo = None
    if theme.logo:
        path = (design_dir / "deck" / theme.logo).resolve()
        w, h = _size(path)
        logo = {"path": str(path), "w": w, "h": h}
    return {
        "meta": {"title": deck.title, "subtitle": deck.subtitle, "presenter": deck.presenter, "date": deck.date,
                 "footer": theme.footer},
        "theme": {"primary": _hex(theme.primary), "accent": _hex(theme.accent), "text": _hex(theme.text),
                  "muted": _hex(theme.muted), "font": theme.font, "logo": logo},
        "slides": [{"kind": s.kind, "number": s.number, "title": s.title.replace("**", ""),
                    "message": runs(s.message), "notes": s.notes,
                    "block": _block(deck, s, images, design_dir)} for s in deck.slides],
    }


def render(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path, out: Path, tools_dir: Path) -> None:
    """Write `out` with pptxgenjs. Raises PptxError when Node or pptxgenjs fails."""
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "deck.json"
        target = Path(tmp) / "deck.pptx"
        source.write_text(json.dumps(to_json(deck, images, design_dir)))
        try:
            done = subprocess.run(["node", str(tools_dir / "pptx.js"), str(source), str(target)],
                                  capture_output=True, text=True, timeout=TIMEOUT, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PptxError(f"PowerPoint renderer could not run: {error}") from error
        if done.returncode != 0 or not target.exists():
            raise PptxError(f"PowerPoint renderer failed: {(done.stderr or done.stdout).strip()}")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, out)
