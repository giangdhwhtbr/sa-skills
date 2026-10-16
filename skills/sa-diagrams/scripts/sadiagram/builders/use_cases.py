"""Step 06: use cases, one page per actor group (split further when a page would exceed 40 nodes)."""

from __future__ import annotations

from typing import Any

from .. import elk
from ..model import Edge, Group, Node, Page
from . import BuildContext, register, text_width

MAX_NODES = 40


def _page(title: str, name: str, cases: list[dict[str, Any]], actors: dict[str, dict[str, Any]],
          system: str) -> Page:
    page = Page(name, title, [], [Group("system", system, "plain")], [],
                notes=["People use the system on the left; external systems it calls are on the right."],
                legend_labels={"step": "Use case"})
    shown = {c["id"] for c in cases}
    for case in cases:
        page.nodes.append(Node(case["id"], case["name"], "step", w=text_width(case["name"], 160), h=60,
                               shape="ellipse", parent="system"))
    used: list[str] = []
    for case in cases:
        for actor_id in case["actor_ids"]:
            if actor_id not in used:
                used.append(actor_id)
    for actor_id in used:
        actor = actors.get(actor_id, {"id": actor_id, "name": actor_id, "kind": "person"})
        if actor["kind"] == "person":
            page.nodes.append(Node(actor_id, actor["name"], "actor", w=text_width(actor["name"], 90, 160), h=70,
                                   shape="actor"))
        else:
            page.nodes.append(Node(actor_id, actor["name"], "external", w=text_width(actor["name"]), h=56))
    n = 0
    for case in cases:
        for actor_id in case["actor_ids"]:
            n += 1
            person = actors.get(actor_id, {}).get("kind", "person") == "person"
            source, target = (actor_id, case["id"]) if person else (case["id"], actor_id)
            page.edges.append(Edge(f"use-{n}", source, target, "use"))
        for kind, targets in (("include", case.get("includes") or []), ("extend", case.get("extends") or [])):
            for target in targets:
                if target in shown:
                    n += 1
                    page.edges.append(Edge(f"{kind}-{n}", case["id"], target, "include", label=f"«{kind}»"))
    return page


def _chunks(cases: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = [[]]
    actors: set[str] = set()
    for case in cases:
        new_actors = actors | set(case["actor_ids"])
        if chunks[-1] and len(chunks[-1]) + 1 + len(new_actors) > MAX_NODES:
            chunks.append([])
            new_actors = set(case["actor_ids"])
        chunks[-1].append(case)
        actors = new_actors
    return chunks


def build(ctx: BuildContext) -> list[Page]:
    brief = ctx.data.get("brief.yaml") or {}
    system = brief.get("system", {}).get("name", "System")
    actors = {a["id"]: a for a in brief.get("actors", [])}
    cases = ctx.data["use-cases.yaml"]["use_cases"]
    by_id = {c["id"]: c for c in cases}
    pages: list[Page] = []
    placed: set[str] = set()
    groups = ctx.data["functions.yaml"]["groups"]
    for group in groups:
        mine = [c for c in cases if set(c["actor_ids"]) & set(group["actor_ids"])]
        for c in list(mine):  # included / extended use cases appear next to the ones that need them
            for target in [*(c.get("includes") or []), *(c.get("extends") or [])]:
                if target in by_id and by_id[target] not in mine:
                    mine.append(by_id[target])
        if not mine:
            continue
        placed |= {c["id"] for c in mine}
        chunks = _chunks(mine)
        for i, chunk in enumerate(chunks, 1):
            suffix = f" ({i}/{len(chunks)})" if len(chunks) > 1 else ""
            pages.append(_page(f"Use cases: {group['name']}{suffix}", f"{group['id']}-{i}", chunk, actors, system))
    rest = [c for c in cases if c["id"] not in placed]
    for i, chunk in enumerate(_chunks(rest) if rest else [], 1):
        pages.append(_page(f"Use cases: other actors ({i})", f"other-{i}", chunk, actors, system))
    elk.layout_many(pages, "RIGHT")
    return pages


register("use-cases", build)
