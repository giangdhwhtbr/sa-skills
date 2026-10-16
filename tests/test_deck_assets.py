"""Slide images and legend chips from /sa-diagrams pages (Track 4 of sad-ap6)."""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from sadeck import assets
from sadeck.model import DiagramRef
from sadiagram import export

ROOT = Path(__file__).resolve().parents[1]
CLINIC = ROOT / "examples" / "clinic-booking" / "design"


def copy_design(tmp_path: Path) -> Path:
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck", "png"))
    (design / "deck").mkdir()
    return design


# REQ-DECK-005
def test_chips_from_legend() -> None:
    _, chips = assets.slide_xml(CLINIC, DiagramRef("context-map", 1))
    assert [(c.kind, c.label) for c in chips] == [
        ("node", "Core subdomain"), ("node", "Supporting subdomain"), ("node", "Generic subdomain"),
        ("edge", "Sync call"), ("edge", "Async event")]
    sync, asynchronous = chips[3], chips[4]
    assert sync.stroke == "#1A73E8" and not sync.dashed
    assert asynchronous.dashed
    assert chips[0].fill == "#dae8fc"


# REQ-DECK-005
def test_stripped_page_has_no_legend() -> None:
    xml, _ = assets.slide_xml(CLINIC, DiagramRef("context-map", 1))
    cells = list(ET.fromstring(xml).iter("mxCell"))
    ids = {c.get("id") for c in cells}
    assert not [i for i in ids if "-legend-" in i or i.endswith("-title")]
    for cell in cells:
        for end in ("source", "target", "parent"):
            if cell.get(end):
                assert cell.get(end) in ids
    assert any(c.get("value", "").startswith("Appointments") for c in cells)


# REQ-DECK-005
def test_page_count() -> None:
    assert assets.page_pages(CLINIC, "saga") == 3
    assert assets.page_pages(CLINIC, "context-map") == 1
    assert assets.page_pages(CLINIC / "missing", "saga") == 0


# REQ-DECK-005
def test_placeholder_without_drawio(tmp_path: Path) -> None:
    design = copy_design(tmp_path)
    image = assets.slide_image(design, DiagramRef("context-map", 1), None)
    assert image.path is None and image.width == 0
    assert len(image.chips) == 5


# REQ-DECK-005
@pytest.mark.skipif(export.find_drawio() is None, reason="draw.io desktop not installed")
def test_slide_png(tmp_path: Path) -> None:
    design = copy_design(tmp_path)
    cmd = export.find_drawio()
    image = assets.slide_image(design, DiagramRef("context-map", 1), cmd)
    assert image.path is not None and image.path.read_bytes()[:4] == b"\x89PNG"
    assert image.path.parent == design / "deck" / "assets"
    assert image.width > 1200 and image.height > 1000  # exported at scale 2
    again = assets.slide_image(design, DiagramRef("context-map", 1), None)  # cached: no draw.io needed
    assert again.path == image.path and again.width == image.width
