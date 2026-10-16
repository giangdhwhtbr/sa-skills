"""The shared architecture skeleton: one set of boxes and slots, sized from the data, used by both the
high-level and the physical view so that they line up for any number of services.

    clients | edge | backend: microservices grid / data stores / managed services / platform | external
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

Rect = tuple[float, float, float, float]

MARGIN = 80     # room around everything for the physical view's region / VPC / zone frames
SLOT_W = 170
SLOT_H = 70
GAP = 30
PAD = 24
HEADER = 34
COL_W = 210     # clients, edge and external columns
COL_GAP = 70
ROW_GAP = 24
ITEM_H = 48     # managed and platform items


def _rows(count: int, columns: int) -> int:
    return max(1, math.ceil(count / columns))


def _grid_h(rows: int, item_h: float) -> float:
    return HEADER + rows * (item_h + GAP) - GAP + PAD


@dataclass(frozen=True)
class Skeleton:
    columns: int
    managed_groups: tuple[str, ...]
    boxes: dict[str, Rect] = field(default_factory=dict)

    def _grid_slot(self, box: str, i: int) -> Rect:
        x, y, _, _ = self.boxes[box]
        row, col = divmod(i, self.columns)
        return (x + PAD + col * (SLOT_W + GAP), y + HEADER + row * (SLOT_H + GAP), SLOT_W, SLOT_H)

    def _stack_slot(self, box: str, i: int) -> Rect:
        x, y, w, _ = self.boxes[box]
        return (x + PAD, y + HEADER + i * (SLOT_H + GAP), w - 2 * PAD, SLOT_H)

    def service_slot(self, i: int) -> Rect:
        """Slot of the i-th service, row-major in the microservices box."""
        return self._grid_slot("microservices", i)

    def data_slot(self, i: int) -> Rect:
        return self._grid_slot("data", i)

    def client_slot(self, i: int) -> Rect:
        return self._stack_slot("clients", i)

    def edge_slot(self, i: int) -> Rect:
        return self._stack_slot("edge", i)

    def external_slot(self, i: int) -> Rect:
        return self._stack_slot("external", i)

    def managed_box(self, name: str) -> Rect:
        """Sub-box of one managed-service group, side by side inside the managed row."""
        x, y, w, h = self.boxes["managed"]
        n = len(self.managed_groups)
        i = self.managed_groups.index(name)
        inner_w = (w - 2 * PAD - (n - 1) * GAP) / n
        return (x + PAD + i * (inner_w + GAP), y + HEADER, inner_w, h - HEADER - PAD)

    def managed_slot(self, name: str, i: int) -> Rect:
        x, y, w, _ = self.managed_box(name)
        return (x + 10, y + HEADER + i * (ITEM_H + 10), w - 20, ITEM_H)

    def platform_slot(self, i: int, count: int) -> Rect:
        x, y, w, _ = self.boxes["platform"]
        n = max(1, count)
        item_w = (w - 2 * PAD - (n - 1) * GAP) / n
        return (x + PAD + i * (item_w + GAP), y + HEADER, item_w, ITEM_H)


def compute(services: int, data_stores: int, externals: int, managed_groups: list[str], columns: int = 4,
            clients: int = 2, managed_items: int = 2, edge_items: int = 2) -> Skeleton:
    """Boxes for clients, edge, backend (holding microservices, data, managed, platform) and external."""
    cols = max(1, columns)
    inner_w = cols * SLOT_W + (cols - 1) * GAP + 2 * PAD
    top = MARGIN
    backend_x = MARGIN + 2 * (COL_W + COL_GAP)
    inner_x = backend_x + PAD

    ms = (inner_x, top + HEADER, inner_w, _grid_h(_rows(services, cols), SLOT_H))
    data = (inner_x, ms[1] + ms[3] + ROW_GAP, inner_w, _grid_h(_rows(data_stores, cols), SLOT_H))
    managed_h = HEADER + HEADER + max(1, managed_items) * (ITEM_H + 10) - 10 + PAD + PAD if managed_groups else 0
    managed = (inner_x, data[1] + data[3] + ROW_GAP, inner_w, managed_h)
    platform = (inner_x, managed[1] + managed[3] + ROW_GAP, inner_w, HEADER + ITEM_H + PAD)

    stacked = max(clients, edge_items, 2, externals)
    stack_h = HEADER + stacked * (SLOT_H + GAP) - GAP + PAD
    backend_h = max(platform[1] + platform[3] + PAD - top, stack_h)
    backend = (backend_x, top, inner_w + 2 * PAD, backend_h)
    boxes = {
        "clients": (MARGIN, top, COL_W, backend_h),
        "edge": (MARGIN + COL_W + COL_GAP, top, COL_W, backend_h),
        "backend": backend,
        "microservices": ms,
        "data": data,
        "managed": managed,
        "platform": platform,
        "external": (backend_x + backend[2] + COL_GAP, top, COL_W, backend_h),
    }
    return Skeleton(cols, tuple(managed_groups), boxes)
