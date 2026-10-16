"""Shared helpers for the sa-deck renderer tests."""

import shutil
import struct
import zlib
from pathlib import Path
from typing import Any

import yaml
from sadeck import schema
from sadeck.assets import Chip, SlideImage
from sadeck.model import Deck, DiagramRef

ROOT = Path(__file__).resolve().parents[1]
DECK_REFS = ROOT / "skills" / "sa-deck" / "references"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "deck" / "deck.yaml"
CHIPS = [Chip("node", "Core subdomain", "#dae8fc", "#6c8ebf", False), Chip("edge", "Async event", "none", "#E8A400", True)]


def tiny_png(path: Path, width: int = 40, height: int = 20) -> Path:
    """A valid white PNG of the given size."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return path


def make_deck(tmp_path: Path, mutate: Any = None) -> tuple[Deck, dict[DiagramRef, SlideImage], Path]:
    """The fixture deck on a copy of clinic-booking, with tiny PNGs standing in for every diagram page."""
    design = tmp_path / "design"
    shutil.copytree(CLINIC, design, ignore=shutil.ignore_patterns("deck", "png"))
    (design / "deck").mkdir()
    data = yaml.safe_load(FIXTURE.read_text())
    if mutate:
        mutate(data, design)
    (design / "deck" / "deck.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    deck = schema.load(design, DECK_REFS)
    images = {}
    for slide in deck.slides:
        for ref in slide.block.diagrams if slide.block else []:
            png = tiny_png(design / "deck" / f"{ref.step}-{ref.page}.png")
            images[ref] = SlideImage(png, 40, 20, list(CHIPS))
    return deck, images, design
