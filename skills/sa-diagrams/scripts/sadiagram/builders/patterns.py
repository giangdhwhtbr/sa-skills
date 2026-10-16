"""Step 09: core patterns (security, observability, resilience) with numbered steps."""

from __future__ import annotations

from typing import Any

from ..layouts import bands
from ..model import Edge, Group, Node, Page
from . import BuildContext, component_kind, component_shape, components, register, service_types

TITLES = {"security": "Security pattern", "observability": "Observability pattern",
          "resilience": "Resilience pattern"}


def _flow_kinds(ctx: BuildContext) -> dict[tuple[str, str], str]:
    return {(f["from"], f["to"]): f["kind"] for f in (ctx.data.get("logical.yaml") or {}).get("flows", [])}


def _nodes(ctx: BuildContext, pattern: dict[str, Any], prefix: str = "") -> list[Node]:
    comps = components(ctx)
    types = service_types(ctx)
    ids: list[str] = []
    for step in pattern["steps"]:
        for item in (step["from"], step["to"]):
            if item not in ids:
                ids.append(item)
    nodes = []
    for item in ids:
        comp = comps.get(item, {"id": item, "name": item, "kind": "external"})
        nodes.append(Node(prefix + item, comp["name"], component_kind(comp, types), w=170, h=60,
                          shape=component_shape(comp)))
    return nodes


def _edges(ctx: BuildContext, pattern: dict[str, Any], prefix: str = "") -> tuple[list[Edge], list[str]]:
    letter = pattern["id"][0].upper()
    kinds = _flow_kinds(ctx)
    edges, notes = [], []
    for step in pattern["steps"]:
        label = f"{letter}{step['n']}"
        kind = kinds.get((step["from"], step["to"]), "sync")
        edges.append(Edge(f"{prefix}{label}", prefix + step["from"], prefix + step["to"], kind, label=label))
        notes.append(f"{label}. {step['text']}")
    return edges, notes


def build(ctx: BuildContext) -> list[Page]:
    patterns = ctx.data["patterns.yaml"]["patterns"]
    if ctx.options.get("patterns", {}).get("split", "one-per-pattern") == "one-per-pattern":
        pages = []
        for pattern in patterns:
            page = Page(pattern["id"], TITLES.get(pattern["id"], pattern["id"]), [], [], [])
            band = Group(f"{pattern['id']}-band", pattern["summary"], "plain")
            bands.layout(page, [(band, _nodes(ctx, pattern))], columns=3, gap=80)
            page.edges, notes = _edges(ctx, pattern)
            bands.route(page)
            page.notes = notes
            pages.append(page)
        return pages
    page = Page("patterns", "Core patterns", [], [], [])
    spec = []
    for pattern in patterns:
        prefix = f"{pattern['id']}-"
        spec.append((Group(f"{pattern['id']}-band", f"{TITLES.get(pattern['id'], pattern['id'])}: "
                           f"{pattern['summary']}", "plain"), _nodes(ctx, pattern, prefix)))
        edges, notes = _edges(ctx, pattern, prefix)
        page.edges += edges
        page.notes += notes
    bands.layout(page, spec, columns=3, gap=80, band_gap=36)
    bands.route(page)
    return [page]


register("patterns", build)
