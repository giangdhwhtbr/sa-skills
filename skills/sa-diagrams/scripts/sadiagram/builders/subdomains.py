"""Step 03: domain decomposition, core / supporting / generic bands with one service per subdomain."""

from __future__ import annotations

from ..layouts import bands
from ..model import Group, Node, Page
from . import SUBDOMAIN_TYPES, BuildContext, register, wrap

TITLES = {"core": "Core subdomains", "supporting": "Supporting subdomains", "generic": "Generic subdomains"}


def build(ctx: BuildContext) -> list[Page]:
    system = (ctx.data.get("brief.yaml") or {}).get("system", {}).get("name", "System")
    subs = ctx.data["subdomains.yaml"]["subdomains"]
    page = Page("subdomains", "Domain decomposition", [], [], [],
                notes=["Each subdomain is owned by one service, named under the subdomain."])
    spec = []
    for kind in SUBDOMAIN_TYPES:
        members = [s for s in subs if s["type"] == kind]
        if members:
            nodes = [Node(s["id"], f"Subdomain: {s['name']}\n{s['service']['name']}", kind, w=210, h=84,
                          shape="ellipse") for s in members]
            spec.append((Group(f"band-{kind}", TITLES[kind], f"band-{kind}"), nodes))
    bands.layout(page, spec, columns=4, x0=24, y0=40)
    wrap(page, Group("domain", f"{system} domain", "plain"), [g for g, _ in spec])
    return [page]


register("subdomains", build)
