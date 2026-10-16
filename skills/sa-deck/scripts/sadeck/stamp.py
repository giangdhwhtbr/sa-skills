"""Deck source hash: deck.yaml, the image and logo files, and the XML of every diagram page it shows.
Keep identical to sacheck.checks.deck_hash (a test compares them)."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

STAMP_FILE = ".deck-stamp.json"
NUMBERS = {"functions": 2, "subdomains": 3, "context-map": 4, "aggregates": 5, "use-cases": 6,
           "logical-view": 7, "saga": 8, "patterns": 9, "architecture": 10}


def _refs(block: dict[str, Any]) -> list[tuple[str, int]]:
    if block.get("type") == "diagrams":
        return [(block[s]["step"], block[s]["page"]) for s in ("left", "right") if isinstance(block.get(s), dict)]
    if "step" in block and "page" in block:
        return [(block["step"], block["page"])]
    return []


def _page(design_dir: Path, step: str, page: int) -> bytes:
    path = design_dir / "diagrams" / f"{NUMBERS.get(step, 0):02d}-{step}.drawio"
    try:
        pages = ET.parse(path).getroot().findall("diagram")
    except (OSError, ET.ParseError):
        return b"<missing>"
    if not 1 <= page <= len(pages):
        return b"<missing>"
    return ET.tostring(pages[page - 1])


def deck_hash(design_dir: Path) -> str:
    deck_dir = design_dir / "deck"
    source = (deck_dir / "deck.yaml").read_bytes()
    digest = hashlib.sha256(source)
    try:
        data = yaml.safe_load(source) or {}
    except yaml.YAMLError:
        data = {}
    files = [((data.get("theme") or {}).get("logo"))]
    refs: list[tuple[str, int]] = []
    for section in data.get("sections") or []:
        for slide in section.get("slides") or []:
            block = slide.get("block") or {}
            if block.get("type") == "image":
                files.append(block.get("file"))
            refs += _refs(block)
    for name in files:
        if name:
            path = deck_dir / name
            digest.update(name.encode() + b"\0" + (path.read_bytes() if path.is_file() else b"<missing>"))
    for step, page in refs:
        digest.update(f"{step}:{page}".encode() + b"\0" + _page(design_dir, step, page))
    return digest.hexdigest()


def read(design_dir: Path) -> str | None:
    try:
        return json.loads((design_dir / "deck" / STAMP_FILE).read_text()).get("hash")
    except (OSError, ValueError, AttributeError):
        return None


def write(design_dir: Path, value: str) -> None:
    (design_dir / "deck" / STAMP_FILE).write_text(json.dumps({"hash": value}) + "\n")
