"""Step 02: main business functions, one band per actor group."""

from __future__ import annotations

from ..layouts import bands
from ..model import Group, Node, Page
from . import SUBDOMAIN_TYPES, BuildContext, register

BAND_KINDS = {"core": "band-core", "supporting": "band-supporting", "generic": "band-generic"}


def build(ctx: BuildContext) -> list[Page]:
    actors = {a["id"]: a["name"] for a in (ctx.data.get("brief.yaml") or {}).get("actors", [])}
    page = Page("functions", "Main business functions", [], [], [],
                notes=["Functions are grouped by the actor who uses them; colours mark the groups."])
    spec = []
    names: dict[str, list[str]] = {}
    for i, group in enumerate(ctx.data["functions.yaml"]["groups"]):
        kind = SUBDOMAIN_TYPES[i % len(SUBDOMAIN_TYPES)]
        names.setdefault(kind, []).append(group["name"])
        who = ", ".join(actors.get(a, a) for a in group["actor_ids"])
        band = Group(group["id"], f"{group['name']} ({who})" if who else group["name"], BAND_KINDS[kind])
        spec.append((band, [Node(f["id"], f["name"], kind, w=180, h=56) for f in group["functions"]]))
    bands.layout(page, spec, columns=4)
    page.legend_labels = {kind: " / ".join(group_names) for kind, group_names in names.items()}
    return bands.split(page)


register("functions", build)
