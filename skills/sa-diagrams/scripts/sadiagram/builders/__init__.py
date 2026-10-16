"""One builder per drawn step: parsed YAML + effective options -> pages of the drawing model."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..model import Group, Page
from ..stamp import DRAWN


@dataclass(frozen=True)
class BuildContext:
    data: dict[str, Any]                 # data file name -> parsed YAML (only valid files)
    options: dict[str, dict[str, Any]]   # effective step options
    vendor_terms: list[str]


Builder = Callable[[BuildContext], list[Page]]

# Graph-shaped steps laid out with elkjs (need Node).
NEEDS_ELK = {"context-map", "aggregates", "use-cases"}

SUBDOMAIN_TYPES = ("core", "supporting", "generic")
COMPONENT_KINDS = {"client": "client", "gateway": "gateway", "identity-provider": "identity-provider",
                   "broker": "broker", "datastore": "datastore", "external": "external"}


def service_types(ctx: BuildContext) -> dict[str, str]:
    """Service ID -> subdomain type, so a service is coloured like its subdomain everywhere."""
    return {s["service"]["id"]: s["type"] for s in (ctx.data.get("subdomains.yaml") or {}).get("subdomains", [])}


def components(ctx: BuildContext) -> dict[str, dict[str, Any]]:
    """Logical component ID -> component, with its layer ID under '_layer'."""
    return {c["id"]: {**c, "_layer": layer["id"]}
            for layer in (ctx.data.get("logical.yaml") or {}).get("layers", []) for c in layer["components"]}


def component_kind(component: dict[str, Any], types: dict[str, str]) -> str:
    if component["kind"] == "service":
        return types.get(component.get("service_id", ""), "supporting")
    return COMPONENT_KINDS[component["kind"]]


def component_shape(component: dict[str, Any]) -> str:
    return {"datastore": "cylinder", "service": "hexagon"}.get(component["kind"], "box")


def vendor_hit(text: str, terms: list[str]) -> str | None:
    lowered = text.lower()
    return next((t for t in terms if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", lowered)), None)


def wrap(page: Page, group: Group, children: list[Group], pad: float = 24, header: float = 40) -> None:
    """Put an outer group around already placed child groups, shifting nothing."""
    x0 = min(c.x for c in children)
    y0 = min(c.y for c in children)
    x1 = max(c.x + c.w for c in children)
    y1 = max(c.y + c.h for c in children)
    group.x, group.y, group.w, group.h = x0 - pad, y0 - header, x1 - x0 + 2 * pad, y1 - y0 + header + pad
    for child in children:
        child.parent = group.id
    page.groups.insert(0, group)
    page.width = max(page.width, group.x + group.w)
    page.height = max(page.height, group.y + group.h)


BUILDERS: dict[str, tuple[int, list[str], Builder]] = {}


def register(key: str, build: Builder) -> None:
    number, inputs, _ = DRAWN[key]
    BUILDERS[key] = (number, inputs, build)


from . import functions, logical, patterns, subdomains  # noqa: E402  (modules register themselves)

__all__ = ["BUILDERS", "NEEDS_ELK", "BuildContext", "functions", "logical", "patterns", "subdomains"]
