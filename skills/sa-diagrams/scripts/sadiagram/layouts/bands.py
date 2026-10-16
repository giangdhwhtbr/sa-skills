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
           x0: float = 0, y0: float = 0, gap: float = GAP, band_gap: float = BAND_GAP) -> None:
    """Place every band and its nodes. Bands get equal widths (rows) or equal heights (columns).
    Nodes and groups not yet on the page are added to it."""
    if direction not in ("rows", "columns"):
        raise ValueError(f"unknown direction '{direction}'")
    node_w = max((n.w for _, nodes in bands for n in nodes), default=160)
    node_h = max((n.h for _, nodes in bands for n in nodes), default=56)
    cols = max(1, columns)
    inner_w = cols * node_w + (cols - 1) * gap
    band_w = inner_w + 2 * PAD
    heights = [HEADER + PAD + _grid_size(len(nodes), cols) * (node_h + gap) - gap + PAD for _, nodes in bands]
    band_h = max(heights, default=0)

    x, y = x0, y0
    for (group, nodes), height in zip(bands, heights, strict=True):
        h = height if direction == "rows" else band_h
        group.x, group.y, group.w, group.h = x, y, band_w, h
        for i, node in enumerate(nodes):
            row, col = divmod(i, cols)
            node.parent = group.id
            node.x = x + PAD + col * (node_w + gap) + (node_w - node.w) / 2
            node.y = y + HEADER + row * (node_h + gap) + (node_h - node.h) / 2
        if direction == "rows":
            y += h + band_gap
        else:
            x += band_w + band_gap
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


# ---------- gutter routing ----------

def _clusters(values: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Merge (start, end) intervals that overlap into sorted, disjoint intervals."""
    merged: list[list[float]] = []
    for start, end in sorted(values):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def _index(intervals: list[tuple[float, float]], value: float) -> int:
    return next(i for i, (a, b) in enumerate(intervals) if a <= value <= b)


class _Lanes:
    """Spreads lines that share a gutter or a node side: 0, +s, -s, +2s, -2s ... within a limit."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.used: dict[object, int] = {}

    def take(self, key: object, limit: float) -> float:
        n = self.used.get(key, 0)
        self.used[key] = n + 1
        offset = ((n + 1) // 2) * self.step * (1 if n % 2 else -1)
        return max(-limit, min(limit, offset))


def route(page: Page) -> None:
    """Route every edge between different nodes through the gaps between node rows and columns, so that no
    edge runs through a node. Works for any band layout whose bands share one column grid."""
    nodes = {n.id: n for n in page.nodes}
    groups = {g.id: g for g in page.groups}
    if not nodes:
        return
    rows = _clusters([(n.y, n.y + n.h) for n in page.nodes])
    cols = _clusters([(n.x, n.x + n.w) for n in page.nodes])
    row_of = {n.id: _index(rows, n.y) for n in page.nodes}
    col_of = {n.id: _index(cols, n.x) for n in page.nodes}
    band_of_row: dict[int, Group | None] = {}
    for n in page.nodes:
        band_of_row.setdefault(row_of[n.id], groups.get(n.parent) if n.parent else None)

    def h_gutter(r: int) -> tuple[float, float]:
        """Free y range between row r and row r + 1 (below the last row: the bottom padding of its band)."""
        band = band_of_row.get(r)
        if r + 1 < len(rows):
            nxt = band_of_row.get(r + 1)
            if band is not None and nxt is not None and band is not nxt:
                return (band.y + band.h, nxt.y)
            return (rows[r][1], rows[r + 1][0])
        if band is not None and band.y + band.h - rows[r][1] >= 12:
            return (rows[r][1], band.y + band.h)
        return (rows[r][1], rows[r][1] + BAND_GAP)

    def v_gutter(c: int) -> tuple[float, float]:
        """Free x range left of column c (c == len(cols): right of the last column)."""
        left = cols[c - 1][1] if c > 0 else cols[0][0] - PAD
        right = cols[c][0] if c < len(cols) else cols[-1][1] + PAD
        return (left, right)

    lanes, ports = _Lanes(10), _Lanes(14)
    labels_on: dict[float, int] = {}  # labels already placed per horizontal line

    def lane_y(r: int) -> float:
        a, b = h_gutter(r)
        return (a + b) / 2 + lanes.take(("h", r), max(0.0, (b - a) / 2 - 3))

    def lane_x(c: int) -> float:
        a, b = v_gutter(c)
        return (a + b) / 2 + lanes.take(("v", c), max(0.0, (b - a) / 2 - 3))

    def port(node: Node, side: str) -> float:
        return node.x + node.w / 2 + ports.take((node.id, side), node.w / 2 - 12)

    def best_gutter(ax: float, bx: float) -> int:
        def cost(c: int) -> float:
            a, b = v_gutter(c)
            mid = (a + b) / 2
            outer = 1000 if c in (0, len(cols)) and len(cols) > 1 else 0
            return abs(mid - ax) + abs(mid - bx) + outer
        return min(range(len(cols) + 1), key=cost)

    for edge in page.edges:
        a, b = nodes.get(edge.source), nodes.get(edge.target)
        if a is None or b is None or a is b:
            continue
        ra, rb = row_of[a.id], row_of[b.id]
        if ra == rb:
            if abs(col_of[a.id] - col_of[b.id]) == 1:
                y = a.y + a.h / 2
                ax, bx = (a.x + a.w, b.x) if a.x < b.x else (a.x, b.x + b.w)
                edge.points = [(ax, y), (bx, y)]
                continue
            ax, bx, y = port(a, "bottom"), port(b, "bottom"), lane_y(ra)
            edge.points = [(ax, a.y + a.h), (ax, y), (bx, y), (bx, b.y + b.h)]
            continue
        down = rb > ra
        ax = port(a, "bottom" if down else "top")
        bx = port(b, "top" if down else "bottom")
        a_end, b_end = (a.y + a.h, b.y) if down else (a.y, b.y + b.h)
        first = lane_y(ra if down else ra - 1)
        if abs(rb - ra) == 1:
            points = [(ax, a_end), (ax, first), (bx, first), (bx, b_end)]
        else:
            last = lane_y(rb - 1 if down else rb)
            vx = lane_x(best_gutter(ax, bx))
            points = [(ax, a_end), (ax, first), (vx, first), (vx, last), (bx, last), (bx, b_end)]
        edge.points = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
        edge.label_at = label_position(edge.points, labels_on)


SPREAD = (0.5, 0.25, 0.75, 0.15, 0.85)


def label_position(points: list[tuple[float, float]], labels_on: dict[float, int] | None = None) -> float | None:
    """Fraction of the path length on its longest horizontal segment (labels read best on horizontal runs,
    which lie in the gutters between rows). Labels sharing a horizontal line are spread along it."""
    lengths = [abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(points, points[1:], strict=False)]
    total = sum(lengths)
    horizontal = [i for i, (p, q) in enumerate(zip(points, points[1:], strict=False)) if p[1] == q[1] and p[0] != q[0]]
    if not total or not horizontal:
        return None
    best = max(horizontal, key=lambda i: lengths[i])
    used = labels_on if labels_on is not None else {}
    line = round(points[best][1] / 30)
    share = SPREAD[used.get(line, 0) % len(SPREAD)]
    used[line] = used.get(line, 0) + 1
    return round((sum(lengths[:best]) + lengths[best] * share) / total, 4)
