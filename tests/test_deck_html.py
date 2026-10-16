"""HTML deck renderer (Track 5 of sad-ap6)."""

import re
from pathlib import Path
from typing import Any

import pytest
from deck_helpers import make_deck, tiny_png
from sadeck import html
from sadeck.assets import SlideImage


def sections(text: str) -> list[str]:
    return re.findall(r'<section class="slide[^"]*".*?</section>', text, re.DOTALL)


def slide(data: dict[str, Any], section: int, index: int) -> dict[str, Any]:
    return data["sections"][section]["slides"][index]


# REQ-DECK-008
def test_one_section_per_slide(tmp_path: Path) -> None:
    deck, images, design = make_deck(tmp_path)
    text = html.render(deck, images, design)
    found = sections(text)
    assert len(found) == len(deck.slides)
    for part, s in zip(found, deck.slides, strict=True):
        notes = re.search(r'<aside class="notes">(.*?)</aside>', part, re.DOTALL).group(1)
        assert notes == s.notes
        assert f'data-n="{s.number}"' in part
    assert "<title>Clinic booking platform</title>" in text


# REQ-DECK-008
def test_self_contained(tmp_path: Path) -> None:
    deck, images, design = make_deck(tmp_path)
    text = html.render(deck, images, design)
    assert "http://" not in text and "https://" not in text
    srcs = re.findall(r'<img[^>]+src="([^"]*)"', text)
    assert srcs and all(s.startswith("data:image/") for s in srcs)


# REQ-DECK-008
def test_print_and_presenting(tmp_path: Path) -> None:
    deck, images, design = make_deck(tmp_path)
    text = html.render(deck, images, design)
    assert "@media print" in text and "page-break-after" in text and "@page" in text
    for key in ("ArrowRight", "ArrowLeft", "Home", "End", "location.hash"):
        assert key in text
    assert re.search(r"key\s*===?\s*['\"][nN]['\"]|toLowerCase\(\)\s*===?\s*['\"]n['\"]", text)
    assert "4:00" in text  # total time of the fixture deck (240 s)


BLOCKS = {
    "bullets": ({"type": "bullets", "items": ["a", "**b**", "c"]}, r"<li>", 3),
    "table": ({"type": "table", "header": ["A", "B"], "rows": [["1", "2"], ["3", "4"], ["5", "6"]]}, r"<tr>", 4),
    "diagram": ({"type": "diagram", "step": "context-map", "page": 1}, r"<img ", 1),
    "diagrams": ({"type": "diagrams", "left": {"step": "architecture", "page": 1},
                  "right": {"step": "architecture", "page": 2}}, r"<img ", 2),
    "diagram-text": ({"type": "diagram-text", "step": "saga", "page": 2, "items": ["x", "y"]}, r"<li>", 2),
    "agenda": ({"type": "agenda"}, r'class="ag-item"', 2),
}


# REQ-DECK-004
@pytest.mark.parametrize("kind", sorted(BLOCKS))
def test_blocks_render(kind: str, tmp_path: Path) -> None:
    block, pattern, count = BLOCKS[kind]
    deck, images, design = make_deck(tmp_path, lambda d, _: slide(d, 2, 0).update(block=block))
    part = sections(html.render(deck, images, design))[5]
    assert len(re.findall(pattern, part)) == count, part
    if "step" in block or kind == "diagrams":
        assert part.count('class="chip"') == 2  # chips of the page legend (merged for two pages)
    if kind == "bullets":
        assert "<b>b</b>" in part


# REQ-DECK-004
def test_image_block(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any], design: Path) -> None:
        tiny_png(design / "deck" / "photo.png")
        slide(d, 2, 0).update(block={"type": "image", "file": "photo.png"})
    deck, images, design = make_deck(tmp_path, mutate)
    part = sections(html.render(deck, images, design))[5]
    assert 'src="data:image/png;base64,' in part


# REQ-DECK-005
def test_placeholder(tmp_path: Path) -> None:
    deck, images, design = make_deck(tmp_path)
    ref = deck.slides[3].block.diagrams[0]
    images[ref] = SlideImage(None, 0, 0, images[ref].chips)
    part = sections(html.render(deck, images, design))[3]
    assert "Diagram not exported: run /sa-diagrams --png" in part and "<img" not in part


# REQ-DECK-010
def test_theme_applied(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any], design: Path) -> None:
        tiny_png(design / "deck" / "logo.png")
        d["theme"] = {"primary": "#0B5394", "logo": "logo.png", "footer": "Design review"}
    deck, images, design = make_deck(tmp_path, mutate)
    text = html.render(deck, images, design)
    assert "--primary:#0B5394" in text.replace(" ", "")
    cover = sections(text)[0]
    assert 'class="logo"' in cover and "data:image/png;base64," in cover
    assert "Design review" in sections(text)[2]


def test_escaping(tmp_path: Path) -> None:
    deck, images, design = make_deck(tmp_path, lambda d, _: slide(d, 2, 0).update(
        title="A <b> & C", message="**bold** and <i>"))
    part = sections(html.render(deck, images, design))[5]
    assert "A &lt;b&gt; &amp; C" in part
    assert "<b>bold</b> and &lt;i&gt;" in part
