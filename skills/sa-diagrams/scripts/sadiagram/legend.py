"""Legend and notes block: placed below the page content, listing only the styles used on the page."""

from __future__ import annotations

from . import geometry, style
from .model import Edge, Node, Page

ENTRY_W = 200
ROW_H = 28
GAP = 40


def entries(page: Page) -> list[tuple[str, str]]:
    """(category, kind) for each node kind and then each edge kind used, in order of first use."""
    found: list[tuple[str, str]] = []
    for node in page.nodes:
        entry = ("node", node.kind)
        if node.kind != "note" and node.shape != "text" and entry not in found:
            found.append(entry)
    for edge in page.edges:
        entry = ("edge", edge.kind)
        if entry not in found:
            found.append(entry)
    return found


def block(page: Page) -> tuple[list[Node], list[Edge]]:
    """Legend swatches, labels and one notes box, positioned under the content."""
    x0, y0, width, height = geometry.bounds(page)
    top = y0 + height + GAP
    per_row = max(3, int(max(width, ENTRY_W * 3) // ENTRY_W))
    nodes = [Node("legend-title", "Legend", "note", x=x0, y=top, w=ENTRY_W, h=20, shape="text")]
    edges: list[Edge] = []
    for i, (category, kind) in enumerate(entries(page)):
        x = x0 + (i % per_row) * ENTRY_W
        y = top + 24 + (i // per_row) * ROW_H
        if category == "node":
            nodes.append(Node(f"legend-{i}-swatch", "", kind, x=x, y=y + 4, w=30, h=16))
        else:
            edges.append(Edge(f"legend-{i}-line", "", "", kind, points=[(x, y + 12), (x + 30, y + 12)]))
        labels = style.NODE_LABELS if category == "node" else style.EDGE_LABELS
        label = page.legend_labels.get(kind) or labels.get(kind, kind)
        nodes.append(Node(f"legend-{i}-label", label, "note", x=x + 38, y=y, w=ENTRY_W - 44, h=24, shape="text"))
    bottom = max(n.y + n.h for n in nodes)
    if page.notes:
        lines = len(page.notes)
        nodes.append(Node("legend-notes", "\n".join(page.notes), "note", x=x0, y=bottom + 16,
                          w=max(width, ENTRY_W * 3), h=24 + 18 * lines, shape="note"))
    return nodes, edges
