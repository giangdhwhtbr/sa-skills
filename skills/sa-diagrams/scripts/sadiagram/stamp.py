"""Source-hash stamps: which data a diagram was drawn from, stored on the <mxfile> element."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ATTRIBUTE = "sa-source-hash"


def source_hash(design_dir: Path, inputs: list[str], options: dict[str, Any] | None = None) -> str:
    """sha256 over each input data file (in order) and the effective options the drawing depends on.
    Keep identical to sacheck.checks._diagram_hash (a test compares them)."""
    digest = hashlib.sha256()
    for name in inputs:
        path = design_dir / name
        digest.update(name.encode() + b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
        digest.update(b"\0")
    digest.update(json.dumps(options or {}, sort_keys=True).encode())
    return digest.hexdigest()


def read(drawio_file: Path) -> str | None:
    """The recorded source hash, or None when the file is missing, unreadable or unstamped."""
    try:
        return ET.parse(drawio_file).getroot().get(ATTRIBUTE)
    except (OSError, ET.ParseError):
        return None
