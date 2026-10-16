"""elkjs bridge (Track 3 of sad-qwi). The layout test runs only where Node and elkjs are installed."""

import os
from pathlib import Path

import pytest
from sadiagram import elk, geometry
from sadiagram.model import Edge, Group, Node, Page

TOOLS = Path(__file__).resolve().parents[1] / "skills" / "sa-diagrams" / "tools"


# REQ-DIAGRAMS-010
def test_available_reports_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "layout.js").write_text("")
    hint = elk.available(tmp_path)
    assert hint is not None and f"npm install --prefix {tmp_path}" in hint
    monkeypatch.setenv("PATH", "")
    hint = elk.available(TOOLS)
    assert hint is not None and "Node" in hint and "npm install" in hint


def graph_page() -> Page:
    groups = [Group("g1", "Group one", "aggregate"), Group("g2", "Group two", "aggregate")]
    nodes = [Node(f"n{i}", f"Node number {i}", "core", parent="g1" if i < 4 else "g2") for i in range(8)]
    pairs = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (6, 7), (3, 7), (1, 5), (2, 6)]
    edges = [Edge(f"e{i}", f"n{a}", f"n{b}", "sync", label=f"edge {i}") for i, (a, b) in enumerate(pairs)]
    return Page("g", "Graph", nodes, groups, edges)


# REQ-DIAGRAMS-009
@pytest.mark.skipif(elk.available(TOOLS) is not None, reason="Node or elkjs not installed")
def test_layout_no_overlap() -> None:
    page = graph_page()
    elk.layout(page, "RIGHT", TOOLS)
    assert geometry.overlaps(page) == []
    assert geometry.outside_parent(page) == []
    assert all(g.w > 0 and g.h > 0 for g in page.groups)
    assert all(len(e.points) >= 2 for e in page.edges)
    x0, y0, w, h = geometry.bounds(page)
    for edge in page.edges:
        for x, y in edge.points:
            assert x0 - 1 <= x <= x0 + w + 1 and y0 - 1 <= y <= y0 + h + 1
    assert page.width > 0 and page.height > 0


# REQ-DIAGRAMS-009
@pytest.mark.skipif(elk.available(TOOLS) is not None, reason="Node or elkjs not installed")
def test_edge_ends_touch_their_nodes() -> None:
    page = graph_page()
    elk.layout(page, "DOWN", TOOLS)
    nodes = {n.id: n for n in page.nodes}
    for edge in page.edges:
        for (x, y), node in ((edge.points[0], nodes[edge.source]), (edge.points[-1], nodes[edge.target])):
            assert node.x - 2 <= x <= node.x + node.w + 2 and node.y - 2 <= y <= node.y + node.h + 2


def test_layout_error_is_reported(tmp_path: Path) -> None:
    if os.system("command -v node >/dev/null") != 0:
        pytest.skip("Node not installed")
    (tmp_path / "layout.js").write_text("process.exit(1)")
    with pytest.raises(elk.LayoutError):
        elk.layout(graph_page(), "RIGHT", tmp_path)
