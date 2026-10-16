"""Shared drawing model. Geometry is absolute (page coordinates) for every node, group and edge point."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    """One shape on a page."""

    id: str
    label: str
    kind: str                  # style.NODE_KINDS key
    x: float = 0
    y: float = 0
    w: float = 160
    h: float = 56
    shape: str = "box"         # box | ellipse | hexagon | cylinder | actor | lifeline | note | text
    parent: str | None = None  # group id
    icon: str | None = None    # AWS resource icon name, physical view only


@dataclass
class Group:
    """A container drawn behind its children (band, layer, aggregate boundary, network tier...)."""

    id: str
    label: str
    kind: str = "plain"        # style.GROUP_KINDS key
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    parent: str | None = None


@dataclass
class Edge:
    """An arrow. When points are given, the first and last are the attachment points on source and target."""

    id: str
    source: str
    target: str
    kind: str                  # style.EDGE_KINDS key
    label: str = ""
    points: list[tuple[float, float]] = field(default_factory=list)
    source_label: str = ""     # e.g. "U"
    target_label: str = ""     # e.g. "D"


@dataclass
class Page:
    """One diagram page."""

    name: str
    title: str
    nodes: list[Node]
    groups: list[Group]
    edges: list[Edge]
    notes: list[str] = field(default_factory=list)
    width: float = 0
    height: float = 0
    legend_labels: dict[str, str] = field(default_factory=dict)  # kind -> legend text, overrides style.NODE_LABELS


@dataclass
class DiagramSet:
    """All pages drawn for one design step."""

    number: int
    key: str
    pages: list[Page]
    source_hash: str

    @property
    def stem(self) -> str:
        return f"{self.number:02d}-{self.key}"
