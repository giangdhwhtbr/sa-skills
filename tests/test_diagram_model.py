"""Drawing model, style, legend, writers and stamps (Track 1 of sad-qwi)."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from sadiagram import drawio, geometry, legend, mermaid, stamp
from sadiagram.model import DiagramSet, Edge, Group, Node, Page


def flow_page(name: str = "p1") -> Page:
    nodes = [
        Node("a", "Alpha", "core", x=0, y=0),
        Node("b", "Beta", "core", x=300, y=0),
        Node("c", "Gamma", "core", x=0, y=200, parent="g"),
    ]
    groups = [Group("g", "Group", "band-core", x=-20, y=180, w=400, h=100)]
    edges = [
        Edge("e1", "a", "b", "sync", label="calls", source_label="U", target_label="D"),
        Edge("e2", "b", "c", "async", label="events"),
    ]
    return Page(name, f"Title {name}", nodes, groups, edges, notes=["One note."])


def sequence_page() -> Page:
    nodes = [Node("o", "Orchestrator", "core", shape="lifeline", x=0, y=0, w=120, h=300),
             Node("s", "Service", "supporting", shape="lifeline", x=200, y=0, w=120, h=300)]
    edges = [Edge("m1", "o", "s", "sync", label="1. reserve", points=[(60, 80), (260, 80)]),
             Edge("m2", "s", "o", "compensate", label="2. release", points=[(260, 130), (60, 130)])]
    return Page("seq", "Saga", nodes, [], edges)


def cells(xml: str) -> list[ET.Element]:
    return list(ET.fromstring(xml).iter("mxCell"))


# REQ-DIAGRAMS-004
def test_drawio_is_valid() -> None:
    xml = drawio.render(DiagramSet(2, "functions", [flow_page("p1"), flow_page("p2")], "h"))
    root = ET.fromstring(xml)
    assert root.tag == "mxfile"
    assert len(root.findall("diagram")) == 2
    ids = [c.get("id") for c in cells(xml)]
    assert len(ids) == len(set(ids))
    for cell in cells(xml):
        if cell.get("edge") == "1":
            for end in ("source", "target"):
                if cell.get(end) is not None:
                    assert cell.get(end) in ids


# REQ-DIAGRAMS-004
def test_child_geometry_is_relative_to_group() -> None:
    xml = drawio.render(DiagramSet(2, "functions", [flow_page()], "h"))
    by_id = {c.get("id"): c for c in cells(xml)}
    child = next(c for i, c in by_id.items() if i.endswith("-c"))
    assert child.get("parent").endswith("-g")
    geo = child.find("mxGeometry")
    assert (float(geo.get("x")), float(geo.get("y"))) == (20.0, 20.0)


# REQ-DIAGRAMS-012
def test_stamp_round_trip(tmp_path: Path) -> None:
    out = tmp_path / "02-functions.drawio"
    out.write_text(drawio.render(DiagramSet(2, "functions", [flow_page()], "abc")))
    assert stamp.read(out) == "abc"
    assert stamp.read(tmp_path / "missing.drawio") is None


# REQ-DIAGRAMS-012
def test_source_hash_changes_with_input_or_option(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text("x: 1\n")
    (tmp_path / "b.yaml").write_text("y: 1\n")
    base = stamp.source_hash(tmp_path, ["a.yaml", "b.yaml"], {"context-map": {"detail": "ud-only"}})
    assert base == stamp.source_hash(tmp_path, ["a.yaml", "b.yaml"], {"context-map": {"detail": "ud-only"}})
    assert base != stamp.source_hash(tmp_path, ["a.yaml", "b.yaml"], {"context-map": {"detail": "with-externals"}})
    (tmp_path / "b.yaml").write_text("y: 2\n")
    assert base != stamp.source_hash(tmp_path, ["a.yaml", "b.yaml"], {"context-map": {"detail": "ud-only"}})


# REQ-DIAGRAMS-008
def test_legend_lists_only_used_styles() -> None:
    page = flow_page()
    assert legend.entries(page) == [("node", "core"), ("edge", "sync"), ("edge", "async")]
    nodes, edges = legend.block(page)
    assert {n.label for n in nodes} >= {"Core subdomain", "Sync call", "Async event"}
    assert all(n.y > 280 for n in nodes)  # below the content
    assert len(edges) == 2


# REQ-DIAGRAMS-008
def test_legend_label_override() -> None:
    page = flow_page()
    page.legend_labels = {"core": "Patients"}
    assert any(n.label == "Patients" for n in legend.block(page)[0])


# REQ-DIAGRAMS-008
def test_same_kind_same_style() -> None:
    xml = drawio.render(DiagramSet(2, "functions", [flow_page()], "h"))
    fills = set()
    for cell in cells(xml):
        style = cell.get("style") or ""
        if cell.get("vertex") == "1" and cell.get("value") in {"Alpha", "Beta", "Gamma"}:
            fills.add(re.search(r"fillColor=([^;]+)", style).group(1))
        if cell.get("edge") == "1" and cell.get("value") == "events":
            assert "dashed=1" in style
    assert fills == {"#dae8fc"}


# REQ-DIAGRAMS-004
def test_merge_orders_pages(tmp_path: Path) -> None:
    first = tmp_path / "02-functions.drawio"
    second = tmp_path / "03-subdomains.drawio"
    first.write_text(drawio.render(DiagramSet(2, "functions", [flow_page("a")], "h")))
    second.write_text(drawio.render(DiagramSet(3, "subdomains", [flow_page("b"), flow_page("c")], "h")))
    root = ET.fromstring(drawio.merge([first, second]))
    assert [d.get("name") for d in root.findall("diagram")] == ["02 Title a", "03 Title b", "03 Title c"]
    ids = [c.get("id") for c in root.iter("mxCell")]
    assert len(ids) == len(set(ids))


# REQ-DIAGRAMS-013
def test_mermaid_blocks() -> None:
    text = mermaid.render(DiagramSet(8, "saga", [flow_page("a"), flow_page("b"), sequence_page()], "h"))
    blocks = re.findall(r"```mermaid\n(.*?)```", text, re.DOTALL)
    assert len(blocks) == 3
    assert blocks[0].startswith("flowchart")
    assert blocks[2].startswith("sequenceDiagram")
    for block, page in zip(blocks, [flow_page("a"), flow_page("b"), sequence_page()], strict=True):
        for node in page.nodes:
            assert mermaid.safe_id(node.id) in block
    assert "1. reserve" in blocks[2]


def test_geometry_checks() -> None:
    page = flow_page()
    assert geometry.overlaps(page) == []
    assert geometry.outside_parent(page) == []
    page.nodes.append(Node("d", "Delta", "core", x=10, y=10))
    page.nodes.append(Node("e", "Eps", "core", x=900, y=900, parent="g"))
    assert ("a", "d") in geometry.overlaps(page)
    assert geometry.outside_parent(page) == ["e"]
