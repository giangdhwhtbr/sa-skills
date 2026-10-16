"""Slide images: a /sa-diagrams page without its title, legend and notes, exported at slide resolution,
plus the page's legend entries as chips to draw under the image."""

from __future__ import annotations

import html
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from sadiagram import export

from .model import DiagramRef
from .stamp import NUMBERS

ASSETS_DIR = "assets"
SCALE = 2


@dataclass(frozen=True)
class Chip:
    kind: str          # node | edge
    label: str
    fill: str
    stroke: str
    dashed: bool


@dataclass(frozen=True)
class SlideImage:
    path: Path | None  # None: not exported (draw.io missing) -> the renderers draw a placeholder
    width: int
    height: int
    chips: list[Chip]


def _style(style: str, key: str, default: str = "") -> str:
    match = re.search(rf"(?:^|;){re.escape(key)}=([^;]*)", style or "")
    return match.group(1) if match else default


def _diagram_file(design_dir: Path, step: str) -> Path:
    return design_dir / "diagrams" / f"{NUMBERS[step]:02d}-{step}.drawio"


def page_pages(design_dir: Path, step: str) -> int:
    """Pages of diagrams/NN-step.drawio (0 when the file is missing or unreadable)."""
    try:
        return len(ET.parse(_diagram_file(design_dir, step)).getroot().findall("diagram"))
    except (OSError, ET.ParseError, KeyError):
        return 0


def slide_xml(design_dir: Path, ref: DiagramRef) -> tuple[str, list[Chip]]:
    """The page as a single-page mxfile without title, legend and notes cells, and the legend as chips."""
    diagram = ET.parse(_diagram_file(design_dir, ref.step)).getroot().findall("diagram")[ref.page - 1]
    root = diagram.find("mxGraphModel/root")
    cells = list(root) if root is not None else []
    by_id = {c.get("id", ""): c for c in cells}
    chips: list[Chip] = []
    index = 0
    while True:
        suffix = f"-legend-{index}-label"
        prefix = next((i[: -len(suffix)] for i in by_id if i.endswith(suffix)), None)
        if prefix is None:
            break
        label = html.unescape(by_id[f"{prefix}-legend-{index}-label"].get("value", ""))
        swatch, line = by_id.get(f"{prefix}-legend-{index}-swatch"), by_id.get(f"{prefix}-legend-{index}-line")
        if line is not None:
            style = line.get("style", "")
            chips.append(Chip("edge", label, "none", _style(style, "strokeColor", "#333333"),
                              _style(style, "dashed") == "1"))
        elif swatch is not None:
            style = swatch.get("style", "")
            chips.append(Chip("node", label, _style(style, "fillColor", "#ffffff"),
                              _style(style, "strokeColor", "#333333"), _style(style, "dashed") == "1"))
        index += 1
    removed = {i for i in by_id if "-legend-" in i or i.endswith("-title")}
    changed = True
    while changed:  # children of removed cells go too
        extra = {i for i, c in by_id.items() if c.get("parent") in removed and i not in removed}
        removed |= extra
        changed = bool(extra)
    for cell_id in removed:
        root.remove(by_id[cell_id])
    mxfile = ET.Element("mxfile", host="sa-design-kit", type="device")
    mxfile.append(diagram)
    return ET.tostring(mxfile, encoding="unicode"), chips


def _png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def slide_image(design_dir: Path, ref: DiagramRef, drawio_cmd: str | None) -> SlideImage:
    """Export the slide version of a diagram page into deck/assets (cached by page content)."""
    xml, chips = slide_xml(design_dir, ref)
    folder = design_dir / "deck" / ASSETS_DIR
    out = folder / f"{NUMBERS[ref.step]:02d}-{ref.step}-p{ref.page}.png"
    if not export.cached(xml, out, folder, SCALE):
        if drawio_cmd is None:
            return SlideImage(None, 0, 0, chips)
        export.png(xml, out, drawio_cmd, folder, SCALE)
    width, height = _png_size(out)
    return SlideImage(out, width, height, chips)
