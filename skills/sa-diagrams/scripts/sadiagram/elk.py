"""elkjs bridge: drawing model -> ELK JSON -> `node tools/layout.js` -> positions written back (absolute)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .model import Page

TIMEOUT = 60
GROUP_PADDING = "[top=44,left=24,bottom=24,right=24]"
CHAR_W = 7
GROUP_PREFIX = "group::"  # group and node IDs may coincide (an aggregate and its root)
LABEL_H = 16


class LayoutError(RuntimeError):
    """elkjs failed or could not be run."""


def install_hint(tools_dir: Path) -> str:
    return f"npm install --prefix {tools_dir}"


def available(tools_dir: Path) -> str | None:
    """None when graph layout can run; otherwise what to install."""
    if shutil.which("node") is None:
        return f"Node.js (18 or newer) is not installed; install it, then run: {install_hint(tools_dir)}"
    if not (tools_dir / "node_modules" / "elkjs").is_dir():
        return f"elkjs is not installed; run: {install_hint(tools_dir)}"
    return None


def _graph(page: Page, direction: str) -> dict[str, Any]:
    root: dict[str, Any] = {
        "id": "__root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": direction,
            "elk.hierarchyHandling": "INCLUDE_CHILDREN",
            "elk.edgeRouting": "ORTHOGONAL",
            "elk.spacing.nodeNode": "40",
            "elk.layered.spacing.nodeNodeBetweenLayers": "70",
            "elk.spacing.edgeNode": "20",
            "elk.spacing.edgeEdge": "14",
            "elk.spacing.edgeLabel": "4",
            "elk.edgeLabels.inline": "false",
            "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
            "elk.padding": "[top=20,left=20,bottom=20,right=20]",
        },
        "children": [],
        "edges": [],
    }
    elements: dict[str | None, dict[str, Any]] = {None: root}
    group_ids = {g.id for g in page.groups}
    pending = list(page.groups)
    while pending:  # parents before children
        progressed = False
        for group in list(pending):
            parent = group.parent if group.parent in group_ids else None
            if parent in elements:
                element = {"id": GROUP_PREFIX + group.id, "children": [], "edges": [],
                           "labels": [{"text": group.label, "width": len(group.label) * CHAR_W, "height": LABEL_H}],
                           "layoutOptions": {"elk.padding": GROUP_PADDING,
                                             "elk.nodeLabels.placement": "[H_LEFT, V_TOP, INSIDE]"}}
                elements[parent]["children"].append(element)
                elements[group.id] = element
                pending.remove(group)
                progressed = True
        if not progressed:
            raise LayoutError("group parents form a cycle")
    for node in page.nodes:
        parent = node.parent if node.parent in group_ids else None
        elements[parent]["children"].append({"id": node.id, "width": node.w, "height": node.h})
    for edge in page.edges:
        item: dict[str, Any] = {"id": edge.id, "sources": [edge.source], "targets": [edge.target]}
        if edge.label:
            item["labels"] = [{"text": edge.label, "width": len(edge.label) * CHAR_W, "height": LABEL_H}]
        root["edges"].append(item)
    return root


def _run(graph: Any, tools_dir: Path) -> Any:
    with tempfile.TemporaryDirectory() as tmp:
        source, target = Path(tmp) / "in.json", Path(tmp) / "out.json"
        source.write_text(json.dumps(graph))
        try:
            done = subprocess.run(["node", str(tools_dir / "layout.js"), str(source), str(target)],
                                  capture_output=True, text=True, timeout=TIMEOUT, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise LayoutError(f"elkjs layout could not run: {error}") from error
        if done.returncode != 0 or not target.exists():
            raise LayoutError(f"elkjs layout failed: {done.stderr.strip() or done.stdout.strip()}")
        return json.loads(target.read_text())


def layout(page: Page, direction: str = "RIGHT", tools_dir: Path | None = None) -> None:
    """Lay out the page's nodes, groups and edges with elkjs; geometry is written back in page coordinates."""
    layout_many([page], direction, tools_dir)


def layout_many(pages: list[Page], direction: str = "RIGHT", tools_dir: Path | None = None) -> None:
    """Lay out several pages in one Node process (Node and elkjs start once)."""
    if tools_dir is None:
        tools_dir = Path(__file__).resolve().parents[2] / "tools"
    if not pages:
        return
    results = _run([_graph(page, direction) for page in pages], tools_dir)
    for page, result in zip(pages, results, strict=True):
        _apply(page, result)


def _apply(page: Page, result: dict[str, Any]) -> None:
    nodes = {n.id: n for n in page.nodes}
    groups = {g.id: g for g in page.groups}
    edges = {e.id: e for e in page.edges}
    absolute: dict[str, tuple[float, float]] = {"__root": (0.0, 0.0)}

    def walk(element: dict[str, Any], ox: float, oy: float) -> None:
        for child in element.get("children", []):
            x, y = ox + child.get("x", 0), oy + child.get("y", 0)
            absolute[child["id"]] = (x, y)
            cid = child["id"]
            target = groups.get(cid[len(GROUP_PREFIX):]) if cid.startswith(GROUP_PREFIX) else nodes.get(cid)
            if target is not None:
                target.x, target.y = x, y
                target.w, target.h = child.get("width", target.w), child.get("height", target.h)
            walk(child, x, y)

    def walk_edges(element: dict[str, Any]) -> None:
        for item in element.get("edges", []):
            # elkjs reports edge coordinates relative to the edge's container
            ox, oy = absolute.get(item.get("container", element["id"]), absolute.get(element["id"], (0.0, 0.0)))
            edge = edges.get(item["id"])
            sections = item.get("sections") or []
            if edge is None or not sections:
                continue
            points: list[tuple[float, float]] = []
            for section in sections:
                chain = [section["startPoint"], *section.get("bendPoints", []), section["endPoint"]]
                points += [(ox + p["x"], oy + p["y"]) for p in chain]
            edge.points = points
        for child in element.get("children", []):
            walk_edges(child)

    walk(result, 0.0, 0.0)
    walk_edges(result)
    page.width = result.get("width", page.width)
    page.height = result.get("height", page.height)
