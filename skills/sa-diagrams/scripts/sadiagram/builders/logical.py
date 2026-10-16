"""Step 07: layered logical view; services coloured by subdomain type, flows labelled."""

from __future__ import annotations

from ..layouts import bands
from ..model import Edge, Group, Node, Page
from . import BuildContext, component_kind, component_shape, register, service_types, vendor_hit


def build(ctx: BuildContext) -> list[Page]:
    data = ctx.data["logical.yaml"]
    types = service_types(ctx)
    neutral = ctx.options.get("logical-view", {}).get("vendors", "none") == "none"
    page = Page("logical", "Logical view", [], [], [],
                notes=["Layers from clients to external systems; arrows show the main interactions in order."])
    spec = []
    for layer in data["layers"]:
        nodes = [Node(c["id"], c["name"], component_kind(c, types), w=170, h=60, shape=component_shape(c))
                 for c in layer["components"]]
        spec.append((Group(layer["id"], layer["name"], "layer"), nodes))
    bands.layout(page, spec, columns=4, gap=56, band_gap=56)
    for i, flow in enumerate(data.get("flows", []), 1):
        page.edges.append(Edge(f"flow-{i}", flow["from"], flow["to"], flow["kind"], label=flow.get("label", "")))
    bands.route(page)
    if neutral:
        for text in [*(n.label for n in page.nodes), *(g.label for g in page.groups), *(e.label for e in page.edges)]:
            term = vendor_hit(text, ctx.vendor_terms)
            if term:
                raise ValueError(f"vendor name '{term}' in the logical view while logical-view.vendors = none")
    return [page]


register("logical-view", build)
