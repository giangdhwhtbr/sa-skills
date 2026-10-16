"""One diagrams run: check the design, choose the steps, draw what changed, merge, and export PNGs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from sacheck import catalog, checks

from . import drawio, elk, export, mermaid, stamp
from .builders import BUILDERS, NEEDS_ELK, BuildContext
from .model import DiagramSet

DIAGRAMS_DIR = "diagrams"
ALL_FILE = "all-diagrams.drawio"
ALWAYS_BLOCKING = {"sa-config.yaml", "design-state.yaml"}


class UsageError(ValueError):
    """Bad arguments or an unreadable design folder (exit 2)."""


@dataclass
class RunResult:
    written: list[str] = field(default_factory=list)     # "04-context-map.drawio (1 page)"
    unchanged: list[str] = field(default_factory=list)   # "03-subdomains.drawio"
    skipped: list[str] = field(default_factory=list)     # "06-use-cases (todo)"
    png_exported: int = 0
    png_cached: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    exit_code: int = 0


def _stem(key: str) -> str:
    return f"{BUILDERS[key][0]:02d}-{key}"


def _select(design_dir: Path, only: list[str] | None, result: RunResult) -> list[str]:
    """Drawable steps to draw, in step order; the others are reported as skipped."""
    drawable = list(BUILDERS)
    unknown = [k for k in only or [] if k not in BUILDERS]
    if unknown:
        raise UsageError(f"cannot draw {', '.join(unknown)}; drawable steps: {', '.join(drawable)}")
    status = {s["key"]: s["status"] for s in checks.load_state(design_dir).get("steps", [])}
    chosen = []
    for key in drawable:
        if only and key not in only:
            continue
        state = status.get(key, "todo")
        if state == "done":
            chosen.append(key)
        else:
            result.skipped.append(f"{_stem(key)} ({state})")
    return chosen


def _blocking_errors(design_dir: Path, refs: Path, keys: list[str]) -> list[str]:
    """Error findings in the data a drawn step reads (or in the configuration), one line per step."""
    _, findings, _ = checks.run(design_dir, refs)
    steps = catalog.load_steps(refs)
    owner = {name: s.key for s in steps for name in (s.data, s.markdown)}
    lines = []
    general = [f for f in findings if f.severity == "error" and f.file in ALWAYS_BLOCKING]
    for f in general:
        lines.append(f"{f.file}: {f.rule} {f.item}: {f.message}")
    for key in keys:
        inputs = set(BUILDERS[key][1])
        for f in findings:
            if f.severity == "error" and f.file in inputs:
                lines.append(f"{key}: {f.rule} in {owner.get(f.file, f.file)} ({f.file}) {f.item}: {f.message}")
    return lines


def _load(design_dir: Path, keys: list[str]) -> dict[str, object]:
    names = {name for key in keys for name in BUILDERS[key][1]}
    return {name: catalog.parse_yaml((design_dir / name).read_text()) for name in sorted(names)
            if (design_dir / name).exists()}


def _merge(folder: Path) -> None:
    files = [folder / f"{_stem(key)}.drawio" for key in BUILDERS if (folder / f"{_stem(key)}.drawio").exists()]
    if files:
        (folder / ALL_FILE).write_text(drawio.merge(files))


def _export_png(folder: Path, keys: list[str], cmd: str | None, result: RunResult) -> None:
    if cmd is None:
        result.warnings.append("png: draw.io CLI not found; skipped (set DRAWIO or install draw.io desktop)")
        return
    png_dir = folder / "png"
    for key in keys:
        stem = _stem(key)
        pages = drawio.page_xml((folder / f"{stem}.drawio").read_text())
        for i, page in enumerate(pages, 1):
            try:
                if export.png(page, png_dir / f"{stem}-p{i}.png", cmd, png_dir):
                    result.png_exported += 1
                else:
                    result.png_cached += 1
            except export.ExportError as error:
                result.warnings.append(f"png: {error}")
        for old in png_dir.glob(f"{stem}-p*.png"):  # pages that no longer exist
            match = re.fullmatch(rf"{re.escape(stem)}-p(\d+)\.png", old.name)
            if match and int(match.group(1)) > len(pages):
                old.unlink()


def run(design_dir: Path, refs: Path, only: list[str] | None = None, png: bool = False, force: bool = False,
        tools_dir: Path | None = None, drawio_cmd: str | None = None) -> RunResult:
    """Draw the design's diagrams into design_dir/diagrams. Never writes anywhere else."""
    result = RunResult()
    if not (design_dir / "sa-config.yaml").is_file() or not (design_dir / "design-state.yaml").is_file():
        raise UsageError(f"{design_dir}: not a design folder (sa-config.yaml and design-state.yaml are required)")
    tools = tools_dir or Path(__file__).resolve().parents[2] / "tools"
    keys = _select(design_dir, only, result)

    errors = _blocking_errors(design_dir, refs, keys)
    if errors:
        result.errors = errors
        result.exit_code = 1
        return result

    cfg = checks.config.effective(design_dir, refs)
    folder = design_dir / DIAGRAMS_DIR
    hashes = {key: stamp.step_hash(design_dir, key, cfg.options, cfg.cloud) for key in keys}
    todo = [k for k in keys if force or stamp.read(folder / f"{_stem(k)}.drawio") != hashes[k]
            or not (folder / f"{_stem(k)}.mermaid.md").exists()]
    if any(k in NEEDS_ELK for k in todo):
        hint = elk.available(tools)
        if hint:
            result.errors = [f"graph layout needs Node.js and elkjs: {hint}"]
            result.exit_code = 2
            return result

    context = BuildContext(_load(design_dir, keys), cfg.options, catalog.load_vendor_terms(refs))
    for key in keys:
        stem = _stem(key)
        if key not in todo:
            result.unchanged.append(f"{stem}.drawio")
            continue
        number, _, build = BUILDERS[key]
        diagram = DiagramSet(number, key, build(context), hashes[key])
        folder.mkdir(exist_ok=True)
        (folder / f"{stem}.drawio").write_text(drawio.render(diagram))
        (folder / f"{stem}.mermaid.md").write_text(mermaid.render(diagram))
        pages = len(diagram.pages)
        result.written.append(f"{stem}.drawio ({pages} page{'s' if pages != 1 else ''})")
    if result.written or (keys and not (folder / ALL_FILE).exists()):
        _merge(folder)
    if png and keys:
        _export_png(folder, keys, drawio_cmd or export.find_drawio(), result)
    return result
