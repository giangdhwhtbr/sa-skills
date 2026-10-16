"""DiagramSet -> draw.io mxfile XML (uncompressed, one <diagram> per page) and the consolidated file."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import geometry, legend, stamp, style
from .model import DiagramSet, Edge, Group, Node, Page

HOST = "sa-design-kit"
TITLE_H = 40


def _label(text: str) -> str:
    """Cells use html=1, so labels are escaped and newlines become line breaks."""
    return html.escape(text, quote=False).replace("\n", "<br>")


def _fmt(value: float) -> str:
    return f"{value:g}"


def _geometry(parent: ET.Element, x: float, y: float, w: float, h: float) -> None:
    ET.SubElement(parent, "mxGeometry", x=_fmt(x), y=_fmt(y), width=_fmt(w), height=_fmt(h), **{"as": "geometry"})


def _frac(value: float, start: float, size: float) -> float:
    return round(min(1.0, max(0.0, (value - start) / size)), 4) if size else 0.5


def _page_xml(page: Page, prefix: str) -> ET.Element:
    """One <mxGraphModel>. Child geometry is converted to coordinates relative to the parent group."""
    legend_nodes, legend_edges = legend.block(page)
    nodes = [*page.nodes, *legend_nodes]
    edges = [*page.edges, *legend_edges]
    groups = {g.id: g for g in page.groups}
    node_by_id = {n.id: n for n in nodes}

    def cid(item_id: str) -> str:
        return f"{prefix}-{item_id}"

    def gid(group_id: str) -> str:  # groups get their own namespace: an aggregate and its root share an ID
        return f"{prefix}-group-{group_id}"

    def origin(parent: str | None) -> tuple[float, float]:
        group = groups.get(parent) if parent else None
        return (group.x, group.y) if group else (0.0, 0.0)

    x0, y0, width, height = geometry.bounds(Page(page.name, page.title, nodes, page.groups, edges))
    model = ET.Element("mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10", guides="1", tooltips="1",
                       connect="1", arrows="1", fold="1", page="1", pageScale="1",
                       pageWidth=_fmt(max(page.width, width + 80)), pageHeight=_fmt(max(page.height, height + 120)),
                       math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id=cid("0"))
    ET.SubElement(root, "mxCell", id=cid("1"), parent=cid("0"))
    title = ET.SubElement(root, "mxCell", id=cid("title"), value=_label(page.title), style=style.title_style(),
                          vertex="1", parent=cid("1"))
    _geometry(title, x0, y0 - TITLE_H - 10, max(width, 400), TITLE_H)

    for group in _parents_first(page.groups):
        ox, oy = origin(group.parent)
        cell = ET.SubElement(root, "mxCell", id=gid(group.id), value=_label(group.label),
                             style=style.group_style(group.kind), vertex="1",
                             parent=gid(group.parent) if group.parent in groups else cid("1"))
        _geometry(cell, group.x - ox, group.y - oy, group.w, group.h)

    for node in nodes:
        _node(root, node, cid, gid, origin, groups)

    for edge in edges:
        _edge(root, edge, cid, node_by_id)
    return model


def _parents_first(groups: list[Group]) -> list[Group]:
    """Groups ordered so that every parent is written before its children."""
    by_id = {g.id: g for g in groups}

    def depth(group: Group) -> int:
        d, seen = 0, set()
        while group.parent in by_id and group.parent not in seen:
            seen.add(group.parent)
            group = by_id[group.parent]
            d += 1
        return d

    return sorted(groups, key=depth)


def _node(root: ET.Element, node: Node, cid, gid, origin, groups: dict[str, Group]) -> None:
    ox, oy = origin(node.parent)
    node_style = style.icon_style(node.kind, node.icon) if node.icon else style.node_style(node.kind, node.shape)
    cell = ET.SubElement(root, "mxCell", id=cid(node.id), value=_label(node.label), style=node_style, vertex="1",
                         parent=gid(node.parent) if node.parent in groups else cid("1"))
    _geometry(cell, node.x - ox, node.y - oy, node.w, node.h)


def _edge(root: ET.Element, edge: Edge, cid, node_by_id: dict[str, Node]) -> None:
    edge_style = style.edge_style(edge.kind)
    source = node_by_id.get(edge.source)
    target = node_by_id.get(edge.target)
    if edge.points and source and target:
        (sx, sy), (tx, ty) = edge.points[0], edge.points[-1]
        edge_style += (f"exitX={_frac(sx, source.x, source.w)};exitY={_frac(sy, source.y, source.h)};exitDx=0;exitDy=0;"
                       f"entryX={_frac(tx, target.x, target.w)};entryY={_frac(ty, target.y, target.h)};"
                       "entryDx=0;entryDy=0;")
    elif not edge.points:
        edge_style += "edgeStyle=orthogonalEdgeStyle;"
    attrs = {"id": cid(edge.id), "value": _label(edge.label), "style": edge_style, "edge": "1", "parent": cid("1")}
    if source:
        attrs["source"] = cid(edge.source)
    if target:
        attrs["target"] = cid(edge.target)
    cell = ET.SubElement(root, "mxCell", **attrs)
    geo_attrs = {"relative": "1", "as": "geometry"}
    if edge.label_at is not None:
        geo_attrs["x"] = _fmt(round(edge.label_at * 2 - 1, 4))
    geo = ET.SubElement(cell, "mxGeometry", **geo_attrs)
    if edge.points and not (source and target):
        ET.SubElement(geo, "mxPoint", x=_fmt(edge.points[0][0]), y=_fmt(edge.points[0][1]), **{"as": "sourcePoint"})
        ET.SubElement(geo, "mxPoint", x=_fmt(edge.points[-1][0]), y=_fmt(edge.points[-1][1]), **{"as": "targetPoint"})
    inner = edge.points[1:-1]
    if inner:
        array = ET.SubElement(geo, "Array", **{"as": "points"})
        for x, y in inner:
            ET.SubElement(array, "mxPoint", x=_fmt(x), y=_fmt(y))
    for suffix, text, position in (("src", edge.source_label, "-0.85"), ("tgt", edge.target_label, "0.85")):
        if text:
            end = ET.SubElement(root, "mxCell", id=cid(f"{edge.id}-{suffix}"), value=_label(text),
                                style=style.end_label_style(edge.kind), vertex="1", connectable="0",
                                parent=cid(edge.id))
            end_geo = ET.SubElement(end, "mxGeometry", x=position, relative="1", **{"as": "geometry"})
            ET.SubElement(end_geo, "mxPoint", **{"as": "offset"})


def _mxfile(diagrams: list[ET.Element], source_hash: str | None) -> ET.Element:
    mxfile = ET.Element("mxfile", host=HOST, type="device")
    if source_hash is not None:
        mxfile.set(stamp.ATTRIBUTE, source_hash)
    mxfile.extend(diagrams)
    return mxfile


def _serialise(mxfile: ET.Element) -> str:
    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode") + "\n"


def render(ds: DiagramSet) -> str:
    """The step's .drawio file: one <diagram> per page, stamped with the source hash."""
    diagrams = []
    for i, page in enumerate(ds.pages, 1):
        page_id = f"{ds.key}-{i}"
        diagram = ET.Element("diagram", id=page_id, name=page.title)
        diagram.append(_page_xml(page, page_id))
        diagrams.append(diagram)
    return _serialise(_mxfile(diagrams, ds.source_hash))


def page_xml(drawio_text: str) -> list[str]:
    """Each page of a .drawio file as a standalone single-page mxfile (used for PNG export and caching)."""
    root = ET.fromstring(drawio_text)
    return [_serialise(_mxfile([diagram], None)) for diagram in root.findall("diagram")]


_NUMBER = re.compile(r"^(\d{2})-")


def merge(files: list[Path]) -> str:
    """All pages of the given step files, in the given order, renamed '<NN> <title>'."""
    diagrams = []
    for path in files:
        match = _NUMBER.match(path.name)
        number = match.group(1) if match else ""
        for diagram in ET.parse(path).getroot().findall("diagram"):
            diagram.set("name", f"{number} {diagram.get('name', '')}".strip())
            diagrams.append(diagram)
    return _serialise(_mxfile(diagrams, None))
