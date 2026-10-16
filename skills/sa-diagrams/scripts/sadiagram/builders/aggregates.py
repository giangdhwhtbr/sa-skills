"""Step 05: aggregate roots and the ID references between them (internals under detail = full)."""

from __future__ import annotations

from .. import elk
from ..model import Edge, Group, Node, Page
from . import BuildContext, register, text_width

INTERNALS = (("entities", "entity", "Entity"), ("value_objects", "value-object", "Value object"),
             ("events", "event", "Event"))


def build(ctx: BuildContext) -> list[Page]:
    data = ctx.data["aggregates.yaml"]
    subs = {s["id"]: s for s in ctx.data["subdomains.yaml"]["subdomains"]}
    full = ctx.options.get("aggregates", {}).get("detail", "roots-only") == "full"
    page = Page("aggregates", "Aggregate roots and references", [], [], [],
                notes=["Aggregates refer to each other by ID only; labels give the ID field and multiplicity."])
    for agg in data["aggregates"]:
        sub = subs.get(agg["subdomain_id"], {"name": agg["subdomain_id"], "type": "core"})
        parent = None
        if full:
            page.groups.append(Group(agg["id"], f"{agg['root']} aggregate ({sub['name']})", "aggregate"))
            parent = agg["id"]
        root_label = agg["root"] if full else f"{agg['root']}\n({sub['name']})"
        page.nodes.append(Node(agg["id"], root_label, "aggregate-root", w=text_width(root_label, 150), h=56,
                               parent=parent))
        if full:
            for field, kind, _ in INTERNALS:
                for name in agg.get(field) or []:
                    page.nodes.append(Node(f"{agg['id']}--{kind}--{name}", name, kind, w=text_width(name, 120),
                                           h=40, parent=agg["id"]))
    for i, ref in enumerate(data.get("references", []), 1):
        page.edges.append(Edge(f"ref-{i}", ref["from"], ref["to"], "reference",
                               label=f"{ref['via']}  {ref['multiplicity']}"))
    for item in data.get("no_aggregate") or []:
        name = subs.get(item["subdomain_id"], {}).get("name", item["subdomain_id"])
        page.notes.append(f"{name}: no aggregate. {item['reason']}")
    elk.layout(page, "RIGHT")
    return [page]


register("aggregates", build)
