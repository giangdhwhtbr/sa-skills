"""Optional PNG export through the draw.io desktop CLI, with a timeout, retries and a content-hash cache."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT = 120
RETRIES = 2
MAC_APP = "/Applications/draw.io.app/Contents/MacOS/draw.io"
CACHE_FILE = ".export-cache.json"


class ExportError(RuntimeError):
    """draw.io could not export a page after the retries."""


def find_drawio() -> str | None:
    """The draw.io desktop CLI: the DRAWIO variable when set (and usable), else the macOS app, else PATH."""
    configured = os.environ.get("DRAWIO")
    if configured is not None:
        return configured if os.access(configured, os.X_OK) and Path(configured).is_file() else None
    if os.access(MAC_APP, os.X_OK):
        return MAC_APP
    return shutil.which("drawio") or shutil.which("draw.io")


def _cache(cache_dir: Path) -> dict[str, str]:
    try:
        return json.loads((cache_dir / CACHE_FILE).read_text())
    except (OSError, ValueError):
        return {}


def _key(page_xml: str, scale: float) -> str:
    """Cache key: the page content, plus the scale when it is not 1 (keeps existing caches valid)."""
    text = page_xml if scale == 1 else f"{page_xml}\0scale={scale:g}"
    return hashlib.sha256(text.encode()).hexdigest()


def cached(page_xml: str, out: Path, cache_dir: Path, scale: float = 1) -> bool:
    """True when `out` already holds the export of this page content at this scale."""
    return out.exists() and _cache(cache_dir).get(out.name) == _key(page_xml, scale)


def png(page_xml: str, out: Path, cmd: str, cache_dir: Path, scale: float = 1) -> bool:
    """Export one single-page mxfile to `out`. Returns True when exported, False when the cached PNG for the
    same page content was kept. Raises ExportError after the retries."""
    key = _key(page_xml, scale)
    cache = _cache(cache_dir)
    if cache.get(out.name) == key and out.exists():
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    last = ""
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "page.drawio"
        target = Path(tmp) / "page.png"
        source.write_text(page_xml)
        for _ in range(1 + RETRIES):
            try:
                args = [cmd, "--export", "--format", "png", "--border", "10", "--output", str(target)]
                if scale != 1:
                    args += ["--scale", f"{scale:g}"]
                done = subprocess.run([*args, str(source)], capture_output=True, text=True, timeout=TIMEOUT,
                                      check=False)
                if done.returncode == 0 and target.exists() and target.stat().st_size > 0:
                    shutil.copyfile(target, out)
                    cache[out.name] = key
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    (cache_dir / CACHE_FILE).write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")
                    return True
                last = (done.stderr or done.stdout).strip() or f"exit {done.returncode}"
            except (OSError, subprocess.TimeoutExpired) as error:
                last = str(error)
    raise ExportError(f"draw.io could not export {out.name}: {last}")
