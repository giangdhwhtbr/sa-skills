"""Layout sanity checks used by tests and by the CLI summary."""

from __future__ import annotations

from .model import Group, Node, Page

Rect = tuple[float, float, float, float]


def rect(item: Node | Group) -> Rect:
    return (item.x, item.y, item.w, item.h)


def intersects(a: Rect, b: Rect) -> bool:
    """True when two rectangles share area (touching edges do not count)."""
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def inside(inner: Rect, outer: Rect) -> bool:
    return (inner[0] >= outer[0] and inner[1] >= outer[1]
            and inner[0] + inner[2] <= outer[0] + outer[2] and inner[1] + inner[3] <= outer[1] + outer[3])


def overlaps(page: Page) -> list[tuple[str, str]]:
    """Pairs of node IDs whose boxes overlap."""
    found = []
    for i, a in enumerate(page.nodes):
        for b in page.nodes[i + 1:]:
            if intersects(rect(a), rect(b)):
                found.append((a.id, b.id))
    return found


def outside_parent(page: Page) -> list[str]:
    """IDs of nodes and groups that are not fully inside their parent group."""
    groups = {g.id: g for g in page.groups}
    return [item.id for item in [*page.groups, *page.nodes]
            if item.parent and item.parent in groups and not inside(rect(item), rect(groups[item.parent]))]


def bounds(page: Page) -> Rect:
    """Bounding box of every node and group on the page (0, 0, 0, 0 when empty)."""
    items = [rect(i) for i in [*page.nodes, *page.groups]]
    for edge in page.edges:
        items += [(x, y, 0, 0) for x, y in edge.points]
    if not items:
        return (0, 0, 0, 0)
    x0 = min(r[0] for r in items)
    y0 = min(r[1] for r in items)
    x1 = max(r[0] + r[2] for r in items)
    y1 = max(r[1] + r[3] for r in items)
    return (x0, y0, x1 - x0, y1 - y0)
