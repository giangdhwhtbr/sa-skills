"""Orthogonal connector routing for pages with fixed node positions (bands, skeleton).

Candidate lines run just outside every node and through every port; a shortest path search over their
crossings, with a penalty per bend and per reused segment, finds a route that never enters a node."""

from __future__ import annotations

import heapq
from bisect import bisect_left
from itertools import count

from ..model import Node, Page

CLEAR = 8         # obstacles are inflated by this much
STUB = 16         # first and last leg, straight out of the node
BEND = 120        # cost of one bend, in pixels
REUSE = 0.6       # extra cost per pixel on a segment another edge already uses
PORT_STEP = 14    # spacing of edges leaving the same side of a node

Point = tuple[float, float]
Rect = tuple[float, float, float, float]


def _inflate(node: Node) -> Rect:
    return (node.x - CLEAR, node.y - CLEAR, node.x + node.w + CLEAR, node.y + node.h + CLEAR)


def _side(a: Node, b: Node) -> str:
    """Side of a that faces b."""
    dx = (b.x + b.w / 2) - (a.x + a.w / 2)
    dy = (b.y + b.h / 2) - (a.y + a.h / 2)
    gap_x = max(b.x - (a.x + a.w), a.x - (b.x + b.w))
    gap_y = max(b.y - (a.y + a.h), a.y - (b.y + b.h))
    if gap_y >= gap_x:
        return "bottom" if dy > 0 else "top"
    return "right" if dx > 0 else "left"


class _Ports:
    def __init__(self) -> None:
        self.used: dict[tuple[str, str], int] = {}

    def take(self, node: Node, side: str) -> tuple[Point, Point]:
        """(point on the border, end of the stub) for the next edge on that side."""
        n = self.used.get((node.id, side), 0)
        self.used[(node.id, side)] = n + 1
        offset = ((n + 1) // 2) * PORT_STEP * (1 if n % 2 else -1)
        if side in ("top", "bottom"):
            x = node.x + node.w / 2 + max(-(node.w / 2 - 10), min(node.w / 2 - 10, offset))
            y = node.y if side == "top" else node.y + node.h
            return (x, y), (x, y - STUB if side == "top" else y + STUB)
        y = node.y + node.h / 2 + max(-(node.h / 2 - 8), min(node.h / 2 - 8, offset))
        x = node.x if side == "left" else node.x + node.w
        return (x, y), (x - STUB if side == "left" else x + STUB, y)


def _simplify(points: list[Point]) -> list[Point]:
    out: list[Point] = []
    for p in points:
        if out and p == out[-1]:
            continue
        if len(out) >= 2 and (out[-2][0] == out[-1][0] == p[0] or out[-2][1] == out[-1][1] == p[1]):
            out[-1] = p
        else:
            out.append(p)
    return out


class _Grid:
    """Candidate lines and, precomputed once, which crossings and unit segments are free of obstacles."""

    def __init__(self, obstacles: list[Rect], xs: set[float], ys: set[float]) -> None:
        self.xs = sorted(xs)
        self.ys = sorted(ys)
        self.x_index = {x: i for i, x in enumerate(self.xs)}
        self.y_index = {y: i for i, y in enumerate(self.ys)}
        nx, ny = len(self.xs), len(self.ys)
        self.blocked_point = [[False] * ny for _ in range(nx)]
        self.blocked_h = [[False] * ny for _ in range(max(nx - 1, 0))]   # (x_i, y) - (x_i+1, y)
        self.blocked_v = [[False] * max(ny - 1, 0) for _ in range(nx)]   # (x, y_j) - (x, y_j+1)
        for x0, y0, x1, y1 in obstacles:
            xi0, xi1 = bisect_left(self.xs, x0), bisect_left(self.xs, x1)
            yi0, yi1 = bisect_left(self.ys, y0), bisect_left(self.ys, y1)
            inner_x = [i for i in range(xi0, min(xi1 + 1, nx)) if x0 < self.xs[i] < x1]
            inner_y = [j for j in range(yi0, min(yi1 + 1, ny)) if y0 < self.ys[j] < y1]
            for i in inner_x:
                for j in inner_y:
                    self.blocked_point[i][j] = True
            for j in inner_y:  # horizontal unit segments crossing the rectangle at row j
                for i in range(max(xi0 - 1, 0), min(xi1 + 1, nx - 1)):
                    if self.xs[i] < x1 and self.xs[i + 1] > x0:
                        self.blocked_h[i][j] = True
            for i in inner_x:
                for j in range(max(yi0 - 1, 0), min(yi1 + 1, ny - 1)):
                    if self.ys[j] < y1 and self.ys[j + 1] > y0:
                        self.blocked_v[i][j] = True

    def free_point(self, p: Point) -> bool:
        return not self.blocked_point[self.x_index[p[0]]][self.y_index[p[1]]]

    def neighbours(self, p: Point) -> list[tuple[Point, str]]:
        i, j = self.x_index[p[0]], self.y_index[p[1]]
        out = []
        if i > 0 and not self.blocked_h[i - 1][j] and not self.blocked_point[i - 1][j]:
            out.append(((self.xs[i - 1], p[1]), "h"))
        if i + 1 < len(self.xs) and not self.blocked_h[i][j] and not self.blocked_point[i + 1][j]:
            out.append(((self.xs[i + 1], p[1]), "h"))
        if j > 0 and not self.blocked_v[i][j - 1] and not self.blocked_point[i][j - 1]:
            out.append(((p[0], self.ys[j - 1]), "v"))
        if j + 1 < len(self.ys) and not self.blocked_v[i][j] and not self.blocked_point[i][j + 1]:
            out.append(((p[0], self.ys[j + 1]), "v"))
        return out


def _search(grid: _Grid, start: Point, goal: Point, start_dir: str,
            used: dict[tuple[Point, Point], int]) -> list[Point] | None:
    tie = count()
    queue = [(0.0, next(tie), start, start_dir, None)]
    best: dict[tuple[Point, str], float] = {(start, start_dir): 0.0}
    parent: dict[tuple[Point, str], tuple[Point, str] | None] = {(start, start_dir): None}
    while queue:
        cost, _, p, d, _ = heapq.heappop(queue)
        if p == goal:
            path, key = [], (p, d)
            while key is not None:
                path.append(key[0])
                key = parent[key]
            return path[::-1]
        if cost > best.get((p, d), float("inf")):
            continue
        for q, nd in grid.neighbours(p):
            length = abs(q[0] - p[0]) + abs(q[1] - p[1])
            seg = (min(p, q), max(p, q))
            step = length + (BEND if nd != d else 0) + REUSE * length * used.get(seg, 0)
            key = (q, nd)
            if cost + step < best.get(key, float("inf")):
                best[key] = cost + step
                parent[key] = (p, d)
                heapq.heappush(queue, (cost + step, next(tie), q, nd, None))
    return None


def route(page: Page) -> None:
    """Give every edge between two different nodes an orthogonal path that enters no other node."""
    nodes = {n.id: n for n in page.nodes}
    obstacles = [_inflate(n) for n in page.nodes]
    ports = _Ports()
    plans = []
    xs: set[float] = set()
    ys: set[float] = set()
    for r in obstacles:
        xs |= {r[0] - 1, r[2] + 1}
        ys |= {r[1] - 1, r[3] + 1}
    for edge in page.edges:
        a, b = nodes.get(edge.source), nodes.get(edge.target)
        if a is None or b is None or a is b:
            continue
        side_a, side_b = _side(a, b), _side(b, a)
        (pa, sa), (pb, sb) = ports.take(a, side_a), ports.take(b, side_b)
        xs |= {pa[0], sa[0], pb[0], sb[0]}
        ys |= {pa[1], sa[1], pb[1], sb[1]}
        plans.append((edge, a, b, pa, sa, pb, sb, side_a))
    grid = _Grid(obstacles, xs, ys)
    used: dict[tuple[Point, Point], int] = {}
    for edge, _a, _b, pa, sa, pb, sb, side_a in plans:
        start_dir = "v" if side_a in ("top", "bottom") else "h"
        path = None
        if grid.free_point(sa) and grid.free_point(sb):
            path = _search(grid, sa, sb, start_dir, used)
        for p, q in zip(path or [], (path or [])[1:], strict=False):
            seg = (min(p, q), max(p, q))
            used[seg] = used.get(seg, 0) + 1
        edge.points = _simplify([pa, *(path or [sa, (sa[0], sb[1]), sb]), pb])
