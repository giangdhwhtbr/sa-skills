"""Step 04: context map, one arrow per relationship from upstream (U) to downstream (D)."""

from __future__ import annotations

import re
from typing import Any

from .. import elk
from ..model import Edge, Group, Node, Page
from . import BuildContext, register, text_width


def _words(*texts: str) -> set[str]:
    return {w.rstrip("s") for t in texts for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2}


def _context_for(external: dict[str, Any], subs: list[dict[str, Any]], degree: dict[str, int]) -> str:
    """The context an external system talks to: the one sharing most words with it, else the most connected."""
    ext_words = _words(external["id"], external["name"]) - {"provider", "system", "api", "service", "external"}

    def score(sub: dict[str, Any]) -> tuple[int, int]:
        sub_words = _words(sub["id"], sub["name"], sub["service"]["name"], sub.get("description", ""))
        return (len(ext_words & sub_words), degree.get(sub["id"], 0))

    return max(subs, key=score)["id"]


def build(ctx: BuildContext) -> list[Page]:
    subs = ctx.data["subdomains.yaml"]["subdomains"]
    data = ctx.data["context-map.yaml"]
    detail = ctx.options.get("context-map", {}).get("detail", "ud-only")
    page = Page("context-map", "Context map", [], [], [],
                notes=["U = upstream (provides the model or data), D = downstream (depends on it)."])
    for sub in subs:
        label = f"{sub['name']}\n({sub['service']['name']})"
        page.nodes.append(Node(sub["id"], label, sub["type"], w=text_width(label, 170), h=64))
    degree: dict[str, int] = {}
    for i, rel in enumerate(data.get("relationships", []), 1):
        degree[rel["upstream"]] = degree.get(rel["upstream"], 0) + 1
        degree[rel["downstream"]] = degree.get(rel["downstream"], 0) + 1
        label = rel.get("label", "") if detail == "ud-only" else rel["pattern"].replace("-", " ")
        kind = "async" if rel["pattern"] == "domain-events" else "sync"
        page.edges.append(Edge(f"rel-{i}", rel["upstream"], rel["downstream"], kind, label=label,
                               source_label="U", target_label="D"))
    externals = data.get("externals") or []
    if detail == "with-externals" and externals:
        page.groups.append(Group("externals", "External systems", "plain"))
        for ext in externals:
            page.nodes.append(Node(ext["id"], ext["name"], "external", w=text_width(ext["name"]), h=56,
                                   parent="externals"))
            context = _context_for(ext, subs, degree)
            source, target = (context, ext["id"]) if ext["direction"] == "outbound" else (ext["id"], context)
            page.edges.append(Edge(f"ext-{ext['id']}", source, target, "external", label="ACL"))
        page.notes.append("ACL = anti-corruption layer on our side of each external integration.")
    elk.layout(page, "DOWN")
    return [page]


register("context-map", build)
