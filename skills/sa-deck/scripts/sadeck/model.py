"""Render model shared by the checks and both renderers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiagramRef:
    step: str          # sadiagram.stamp.DRAWN key
    page: int          # 1-based


@dataclass
class Block:
    kind: str          # bullets | table | diagram | diagrams | diagram-text | agenda | image
    items: list[str] = field(default_factory=list)
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    widths: list[float] = field(default_factory=list)
    diagrams: list[DiagramRef] = field(default_factory=list)
    file: str | None = None


@dataclass
class Slide:
    number: int        # 1-based, the cover is 1
    kind: str          # cover | content
    section: str
    title: str
    message: str
    block: Block | None
    notes: str
    seconds: int


@dataclass
class Theme:
    primary: str
    accent: str
    text: str
    muted: str
    font: str
    logo: str | None = None
    footer: str = ""


@dataclass
class Deck:
    title: str
    subtitle: str
    presenter: str
    date: str
    minutes: int
    theme: Theme
    slides: list[Slide]          # cover first, then every section's slides in order
    sections: list[str]          # section titles in order (for the agenda)

    @property
    def seconds(self) -> int:
        return sum(s.seconds for s in self.slides)
