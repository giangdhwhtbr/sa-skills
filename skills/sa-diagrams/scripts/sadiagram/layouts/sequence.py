"""Saga sequence pages: lifelines left to right, numbered messages top to bottom."""

from __future__ import annotations

from ..model import Edge, Group, Node, Page

LIFELINE_W = 160
LIFELINE_GAP = 70
HEAD = 40
FIRST = 90     # y of the first message
STEP = 50      # between messages
LOOP_W = 40
LOOP_H = 22
TAIL = 40


def layout(page: Page, participants: list[Node], messages: list[Edge]) -> None:
    """Turn participants into lifelines and messages into horizontal arrows at increasing y.
    A message to itself is a small loop; runs of compensation messages sit on a red band."""
    height = FIRST + len(messages) * STEP + TAIL
    centres: dict[str, float] = {}
    for i, node in enumerate(participants):
        node.shape = "lifeline"
        node.x, node.y, node.w, node.h = i * (LIFELINE_W + LIFELINE_GAP), 0, LIFELINE_W, height
        centres[node.id] = node.x + LIFELINE_W / 2
        if node not in page.nodes:
            page.nodes.append(node)

    run: list[Edge] = []
    for i, edge in enumerate(messages):
        y = FIRST + i * STEP
        sx, tx = centres[edge.source], centres[edge.target]
        if edge.source == edge.target:
            edge.points = [(sx, y), (sx + LOOP_W, y), (sx + LOOP_W, y + LOOP_H), (sx, y + LOOP_H)]
        else:
            edge.points = [(sx, y), (tx, y)]
        if edge not in page.edges:
            page.edges.append(edge)
        if edge.kind == "compensate":
            run.append(edge)
        if run and (edge.kind != "compensate" or i == len(messages) - 1):
            _band(page, run, len([g for g in page.groups if g.kind == "compensation"]))
            run = []

    page.width = max(page.width, max((n.x + n.w for n in page.nodes), default=0))
    page.height = max(page.height, height)


def _band(page: Page, run: list[Edge], index: int) -> None:
    xs = [x for e in run for x, _ in e.points]
    ys = [y for e in run for _, y in e.points]
    page.groups.append(Group(f"compensation-{index + 1}", "", "compensation", x=min(xs) - 20, y=min(ys) - 20,
                             w=max(xs) - min(xs) + 40, h=max(ys) - min(ys) + 34))
