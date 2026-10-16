"""Source-hash stamps: which data a diagram was drawn from, stored on the <mxfile> element."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ATTRIBUTE = "sa-source-hash"

# step key -> (number, data files read, (step, option) pairs the drawing depends on).
# Keep identical to sacheck.checks.DRAWN (a test compares them).
DRAWN: dict[str, tuple[int, list[str], list[tuple[str, str]]]] = {
    "functions": (2, ["brief.yaml", "functions.yaml"], []),
    "subdomains": (3, ["subdomains.yaml"], []),
    "context-map": (4, ["subdomains.yaml", "context-map.yaml"], [("context-map", "detail")]),
    "aggregates": (5, ["subdomains.yaml", "aggregates.yaml"], [("aggregates", "detail")]),
    "use-cases": (6, ["brief.yaml", "functions.yaml", "use-cases.yaml"], []),
    "logical-view": (7, ["logical.yaml"], [("logical-view", "vendors")]),
    "saga": (8, ["subdomains.yaml", "logical.yaml", "saga.yaml"], []),
    "patterns": (9, ["logical.yaml", "patterns.yaml"], [("patterns", "split")]),
    "architecture": (10, ["subdomains.yaml", "logical.yaml", "architecture.yaml"], [("architecture", "shared-layout")]),
}


def drawing_options(key: str, options: dict[str, dict[str, Any]], cloud: str) -> dict[str, Any]:
    """The effective option values a step's drawing depends on (the cloud matters for the physical view)."""
    picked: dict[str, Any] = {f"{step}.{name}": options.get(step, {}).get(name) for step, name in DRAWN[key][2]}
    if key == "architecture":
        picked["cloud"] = cloud
    return picked


def step_hash(design_dir: Path, key: str, options: dict[str, dict[str, Any]], cloud: str) -> str:
    """Source hash of one drawn step."""
    return source_hash(design_dir, DRAWN[key][1], drawing_options(key, options, cloud))


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
