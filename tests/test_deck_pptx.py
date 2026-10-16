"""PowerPoint renderer and HTML/PPTX parity (Track 6 of sad-ap6)."""

import html as htmllib
import re
import zipfile
from pathlib import Path
from typing import Any

import pytest
from deck_helpers import ROOT, make_deck
from sadeck import html, pptx

TOOLS = ROOT / "skills" / "sa-deck" / "tools"
needs_pptx = pytest.mark.skipif(pptx.available(TOOLS) is not None, reason="Node or pptxgenjs not installed")


def slide_xml(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                       key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        return [z.read(n).decode() for n in names]


def notes_xml(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)),
                       key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        return [z.read(n).decode() for n in names]


def text_of(xml: str) -> str:
    return htmllib.unescape("".join(re.findall(r"<a:t>(.*?)</a:t>", xml, re.DOTALL)))


def shape_text(xml: str, name: str) -> str:
    """Text of the shape whose cNvPr name is `name`."""
    for shape in re.findall(r"<p:sp>.*?</p:sp>", xml, re.DOTALL):
        if f'name="{name}"' in shape:
            return text_of(shape)
    return ""


# REQ-DECK-009
def test_available_reports_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hint = pptx.available(tmp_path)
    assert hint is not None and f"npm install --prefix {tmp_path}" in hint
    monkeypatch.setenv("PATH", "")
    hint = pptx.available(TOOLS)
    assert hint is not None and "Node" in hint


def render(tmp_path: Path, mutate: Any = None) -> tuple[Path, Any, str]:
    deck, images, design = make_deck(tmp_path, mutate)
    out = design / "deck" / "deck.pptx"
    pptx.render(deck, images, design, out, TOOLS)
    return out, deck, html.render(deck, images, design)


# REQ-DECK-009
@needs_pptx
def test_pptx_structure(tmp_path: Path) -> None:
    out, deck, _ = render(tmp_path)
    slides = slide_xml(out)
    assert len(slides) == len(deck.slides)
    for xml, s in zip(slides, deck.slides, strict=True):
        assert shape_text(xml, "Title") == s.title.replace("**", "")
    notes = notes_xml(out)
    assert [n for s in deck.slides for n in [s.notes] if any(s.notes in text_of(x) for x in notes)] == \
        [s.notes for s in deck.slides]


# REQ-DECK-004
@needs_pptx
def test_pptx_tables_are_tables(tmp_path: Path) -> None:
    out, deck, _ = render(tmp_path)
    table_slide = slide_xml(out)[2]  # "Proposed solution": header + 2 rows
    assert table_slide.count("<a:tbl>") == 1 and table_slide.count("<a:tr ") + table_slide.count("<a:tr>") == 3
    assert "Scheduling owns every slot" in text_of(table_slide)
    diagram_slide = slide_xml(out)[3]
    assert "<p:pic>" in diagram_slide and "Core subdomain" in text_of(diagram_slide)


# REQ-DECK-009
@needs_pptx
def test_html_pptx_parity(tmp_path: Path) -> None:
    out, deck, page = render(tmp_path)
    html_titles = [htmllib.unescape(re.sub(r"<[^>]+>", "", t))
                   for t in re.findall(r"<section.*?<h1>(.*?)</h1>", page, re.DOTALL)]
    html_notes = [htmllib.unescape(n) for n in re.findall(r'<aside class="notes">(.*?)</aside>', page, re.DOTALL)]
    pptx_titles = [shape_text(x, "Title") for x in slide_xml(out)]
    pptx_notes = [text_of(x) for x in notes_xml(out)]
    assert html_titles == pptx_titles
    assert len(html_notes) == len(pptx_notes)
    assert all(h in p for h, p in zip(html_notes, pptx_notes, strict=True))


# REQ-DECK-010
@needs_pptx
def test_pptx_theme(tmp_path: Path) -> None:
    out, _, _ = render(tmp_path, lambda d, _: d.update(theme={"primary": "#0B5394"}))
    slides = slide_xml(out)
    assert "0B5394" in slides[0]  # cover background
    title = re.search(r'<p:sp>(?:(?!</p:sp>).)*name="Title".*?</p:sp>', slides[3], re.DOTALL).group(0)
    assert "0B5394" in title


# REQ-DECK-004
@needs_pptx
def test_pptx_every_block(tmp_path: Path) -> None:
    def mutate(d: dict[str, Any], design: Path) -> None:
        d["sections"][2]["slides"] += [
            {"title": "B", "message": "m", "block": {"type": "bullets", "items": ["one", "**two**"]},
             "notes": "n", "seconds": 20},
            {"title": "D2", "message": "m", "block": {"type": "diagrams", "left": {"step": "architecture", "page": 1},
                                                      "right": {"step": "architecture", "page": 2}},
             "notes": "n", "seconds": 20}]
    out, deck, _ = render(tmp_path, mutate)
    slides = slide_xml(out)
    assert "one" in text_of(slides[6]) and "<a:buChar" in slides[6]
    assert slides[7].count("<p:pic>") == 2
    assert "Domain design" in text_of(slides[1])  # agenda lists the sections
