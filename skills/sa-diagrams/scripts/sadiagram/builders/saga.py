"""Step 08: the core flow as a saga, one sequence page per scenario."""

from __future__ import annotations

from ..layouts import sequence
from ..model import Edge, Node, Page
from . import BuildContext, component_kind, components, register, service_types

KINDS = {"sync": "sync", "async": "async", "compensate": "compensate", "self": "sync"}


def build(ctx: BuildContext) -> list[Page]:
    saga = ctx.data["saga.yaml"]
    comps = components(ctx)
    types = service_types(ctx)
    names = {s["service"]["id"]: s["service"]["name"] for s in ctx.data["subdomains.yaml"]["subdomains"]}
    order = [saga["flow"]["orchestrator"], *(p for p in saga["participants"] if p != saga["flow"]["orchestrator"])]
    pages = []
    for scenario in saga["scenarios"]:
        participants = []
        for pid in order:
            comp = comps.get(pid)
            label = comp["name"] if comp else names.get(pid, pid)
            kind = component_kind(comp, types) if comp else types.get(pid, "external")
            participants.append(Node(pid, label, kind))
        messages = [Edge(f"step-{step['n']}", step["from"], step["to"], KINDS[step["kind"]],
                         label=f"{step['n']}. {step['message']}") for step in scenario["steps"]]
        what = "failure scenario" if scenario["kind"] == "failure" else "main scenario"
        page = Page(scenario["id"], f"Saga: {saga['flow']['name']}: {scenario['name']}", [], [], [],
                    notes=[f"{scenario['name']} ({what}); orchestrated by {participants[0].label}.",
                           "Numbers give the order. Red messages are compensations."])
        sequence.layout(page, participants, messages)
        pages.append(page)
    return pages


register("saga", build)
