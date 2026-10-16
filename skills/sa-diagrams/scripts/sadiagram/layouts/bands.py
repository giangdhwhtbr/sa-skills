"""Bands: each group is a full-width row (or full-height column) holding its nodes in a grid."""

from __future__ import annotations

import math
from dataclasses import replace

from ..model import Group, Node, Page

GAP = 24       # between nodes
PAD = 20       # inside a band
HEADER = 32    # band label
BAND_GAP = 20  # between bands


def _grid_size(count: int, columns: int) -> int:
    return max(1, math.ceil(count / columns))


def layout(page: Page, bands: list[tuple[Group, list[Node]]], columns: int, direction: str = "rows",
           x0: float = 0, y0: float = 0) -> None:
    """Place every band and its nodes. Bands get equal widths (rows) or equal heights (columns).
    Nodes and groups not yet on the page are added to it."""
    if direction not in ("rows", "columns"):
        raise ValueError(f"unknown direction '{direction}'")
    node_w = max((n.w for _, nodes in bands for n in nodes), default=160)
    node_h = max((n.h for _, nodes in bands for n in nodes), default=56)
    cols = max(1, columns)
    inner_w = cols * node_w + (cols - 1) * GAP
    band_w = inner_w + 2 * PAD
    heights = [HEADER + PAD + _grid_size(len(nodes), cols) * (node_h + GAP) - GAP + PAD for _, nodes in bands]
    band_h = max(heights, default=0)

    x, y = x0, y0
    for (group, nodes), height in zip(bands, heights, strict=True):
        h = height if direction == "rows" else band_h
        group.x, group.y, group.w, group.h = x, y, band_w, h
        for i, node in enumerate(nodes):
            row, col = divmod(i, cols)
            node.parent = group.id
            node.x = x + PAD + col * (node_w + GAP) + (node_w - node.w) / 2
            node.y = y + HEADER + row * (node_h + GAP) + (node_h - node.h) / 2
        if direction == "rows":
            y += h + BAND_GAP
        else:
            x += band_w + BAND_GAP
        if group not in page.groups:
            page.groups.append(group)
        page.nodes.extend(n for n in nodes if n not in page.nodes)
    page.width = max(page.width, max((g.x + g.w for g in page.groups), default=0))
    page.height = max(page.height, max((g.y + g.h for g in page.groups), default=0))


def _top_group(item_parent: str | None, groups: dict[str, Group]) -> str | None:
    seen = set()
    while item_parent in groups and groups[item_parent].parent in groups and item_parent not in seen:
        seen.add(item_parent)
        item_parent = groups[item_parent].parent
    return item_parent


def split(page: Page, max_nodes: int = 40) -> list[Page]:
    """Split a page with more than max_nodes nodes into pages of whole bands (top-level groups), in order.
    Each later page is moved up so that it starts where the first one does. Edges stay with a page only
    when both ends are on it."""
    if len(page.nodes) <= max_nodes:
        return [page]
    groups = {g.id: g for g in page.groups}
    tops = [g for g in page.groups if g.parent not in groups]
    members = {g.id: [n for n in page.nodes if _top_group(n.parent, groups) == g.id] for g in tops}
    loose = [n for n in page.nodes if _top_group(n.parent, groups) not in members]

    chunks: list[list[Group]] = [[]]
    count = len(loose)
    for group in tops:
        size = len(members[group.id])
        if chunks[-1] and count + size > max_nodes:
            chunks.append([])
            count = 0
        chunks[-1].append(group)
        count += size

    start_y = min((g.y for g in tops), default=0)
    pages = []
    for i, chunk in enumerate(chunks, 1):
        ids = {g.id for g in chunk}
        sub_groups = [g for g in page.groups if _top_group(g.id, groups) in ids or g.id in ids]
        sub_nodes = [n for b in chunk for n in members[b.id]] + (loose if i == 1 else [])
        dy = start_y - min(g.y for g in chunk)
        sub_groups = [replace(g, y=g.y + dy) for g in sub_groups]
        sub_nodes = [replace(n, y=n.y + dy) for n in sub_nodes]
        node_ids = {n.id for n in sub_nodes}
        sub_edges = [replace(e, points=[(x, y + dy) for x, y in e.points]) for e in page.edges
                     if e.source in node_ids and e.target in node_ids]
        pages.append(Page(f"{page.name}-{i}", f"{page.title} ({i}/{len(chunks)})", sub_nodes, sub_groups, sub_edges,
                          notes=list(page.notes), width=page.width,
                          height=max(g.y + g.h for g in sub_groups), legend_labels=dict(page.legend_labels)))
    return pages
