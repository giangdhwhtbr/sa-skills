"""Python layouts: bands, the shared architecture skeleton and saga sequences (Track 2 of sad-qwi)."""

import pytest
from sadiagram import geometry
from sadiagram.layouts import bands, sequence, skeleton
from sadiagram.model import Edge, Group, Node, Page


def band_page(sizes: list[int]) -> tuple[Page, list[tuple[Group, list[Node]]]]:
    page = Page("p", "Bands", [], [], [])
    spec = []
    for b, size in enumerate(sizes):
        group = Group(f"band{b}", f"Band {b}", "band-core")
        spec.append((group, [Node(f"n{b}-{i}", f"Node {b}.{i}", "core") for i in range(size)]))
    return page, spec


# REQ-DIAGRAMS-009
def test_bands_equal_width_no_overlap() -> None:
    page, spec = band_page([10, 6, 5])
    bands.layout(page, spec, columns=4)
    widths = {g.w for g in page.groups}
    assert len(widths) == 1
    assert len(page.nodes) == 21
    assert geometry.overlaps(page) == []
    assert geometry.outside_parent(page) == []
    assert all(n.parent == f"band{n.id[1]}" for n in page.nodes)
    tops = [g.y for g in page.groups]
    assert tops == sorted(tops)
    assert page.width >= max(g.x + g.w for g in page.groups)


# REQ-DIAGRAMS-009
def test_bands_as_columns() -> None:
    page, spec = band_page([3, 5])
    bands.layout(page, spec, columns=1, direction="columns")
    assert len({g.y for g in page.groups}) == 1
    assert len({g.h for g in page.groups}) == 1
    assert geometry.overlaps(page) == [] and geometry.outside_parent(page) == []


# REQ-DIAGRAMS-007
@pytest.mark.parametrize("services", [3, 8, 15])
def test_skeleton_same_for_both_views(services: int) -> None:
    first = skeleton.compute(services, 4, 2, ["Messaging", "Security"])
    second = skeleton.compute(services, 4, 2, ["Messaging", "Security"])
    assert first.boxes == second.boxes
    slots = [first.service_slot(i) for i in range(services)]
    assert slots == [second.service_slot(i) for i in range(services)]
    for i, a in enumerate(slots):
        assert geometry.inside(a, first.boxes["microservices"])
        for b in slots[i + 1:]:
            assert not geometry.intersects(a, b)
    for name in ("clients", "edge", "backend", "microservices", "data", "managed", "platform", "external"):
        assert name in first.boxes
    for name in ("microservices", "data", "managed", "platform"):
        assert geometry.inside(first.boxes[name], first.boxes["backend"])


# REQ-DIAGRAMS-007
def test_skeleton_slots_inside_their_boxes() -> None:
    sk = skeleton.compute(8, 5, 3, ["Messaging", "Security", "Storage"], clients=3)
    for i in range(5):
        assert geometry.inside(sk.data_slot(i), sk.boxes["data"])
    for i in range(3):
        assert geometry.inside(sk.external_slot(i), sk.boxes["external"])
        assert geometry.inside(sk.client_slot(i), sk.boxes["clients"])
    for i in range(2):
        assert geometry.inside(sk.edge_slot(i), sk.boxes["edge"])
    for name in ("Messaging", "Security", "Storage"):
        assert geometry.inside(sk.managed_box(name), sk.boxes["managed"])
    boxes = [sk.managed_box(n) for n in ("Messaging", "Security", "Storage")]
    assert not any(geometry.intersects(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:])


# REQ-DIAGRAMS-007
def test_skeleton_grows_with_services() -> None:
    small = skeleton.compute(3, 4, 2, ["Messaging"])
    large = skeleton.compute(15, 4, 2, ["Messaging"])
    grow = large.boxes["microservices"][3] - small.boxes["microservices"][3]
    assert grow > 0
    for name in ("data", "managed", "platform"):
        assert large.boxes[name][1] - small.boxes[name][1] == grow
    assert large.boxes["microservices"][:3] == small.boxes["microservices"][:3]


# REQ-DIAGRAMS-009
def test_sequence_order() -> None:
    page = Page("s", "Saga", [], [], [])
    parts = [Node("o", "Orchestrator", "core"), Node("a", "A", "supporting"), Node("b", "B", "generic")]
    msgs = [Edge("m1", "o", "a", "sync", "1. reserve"), Edge("m2", "a", "a", "sync", "2. self"),
            Edge("m3", "b", "o", "async", "3. done"), Edge("m4", "o", "a", "compensate", "4. undo"),
            Edge("m5", "o", "b", "compensate", "5. undo")]
    sequence.layout(page, parts, msgs)
    centres = {n.id: n.x + n.w / 2 for n in page.nodes}
    assert all(n.shape == "lifeline" for n in page.nodes)
    assert sorted(centres.values()) == [centres["o"], centres["a"], centres["b"]]
    ys = [m.points[0][1] for m in msgs]
    assert ys == sorted(ys) and len(set(ys)) == len(ys)
    for m in msgs:
        assert m.points[0][0] == centres[m.source] and m.points[-1][0] == centres[m.target]
        lifeline = next(n for n in page.nodes if n.id == m.source)
        assert lifeline.y < m.points[0][1] < lifeline.y + lifeline.h
    assert len(msgs[1].points) == 4 and msgs[1].points[1][0] > centres["a"]
    assert len([g for g in page.groups if g.kind == "compensation"]) == 1
    assert geometry.overlaps(page) == []


# REQ-DIAGRAMS-009
def test_split_large_page() -> None:
    page, spec = band_page([20, 18, 12])
    bands.layout(page, spec, columns=5)
    page.edges = [Edge("e1", "n0-0", "n0-1", "sync"), Edge("e2", "n0-0", "n2-0", "sync")]
    pages = bands.split(page, max_nodes=40)
    assert [len(p.nodes) for p in pages] == [38, 12]
    assert [p.title for p in pages] == ["Bands (1/2)", "Bands (2/2)"]
    assert [e.id for e in pages[0].edges] == ["e1"]
    assert min(g.y for g in pages[1].groups) == min(g.y for g in pages[0].groups)
    assert bands.split(pages[1], max_nodes=40) == [pages[1]]


# REQ-DIAGRAMS-009
def test_route_avoids_nodes() -> None:
    page, spec = band_page([8, 8, 4])
    bands.layout(page, spec, columns=4, gap=56, band_gap=36)
    pairs = [("n0-0", "n2-3"), ("n0-3", "n1-0"), ("n0-1", "n0-3"), ("n0-1", "n0-2"), ("n2-0", "n0-2"),
             ("n1-5", "n1-1"), ("n0-0", "n2-0"), ("n1-2", "n1-2")]
    page.edges = [Edge(f"e{i}", a, b, "sync") for i, (a, b) in enumerate(pairs)]
    bands.route(page)
    assert geometry.edge_crossings(page) == []
    nodes = {n.id: n for n in page.nodes}
    for edge in page.edges[:-1]:
        assert len(edge.points) >= 2
        for (x1, y1), (x2, y2) in zip(edge.points, edge.points[1:], strict=False):
            assert x1 == x2 or y1 == y2  # orthogonal
        for (x, y), node in ((edge.points[0], nodes[edge.source]), (edge.points[-1], nodes[edge.target])):
            assert node.x <= x <= node.x + node.w and node.y <= y <= node.y + node.h
    assert page.edges[-1].points == []  # self loop left to draw.io
