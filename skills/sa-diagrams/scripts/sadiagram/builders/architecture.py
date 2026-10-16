"""Step 10: high-level architecture and physical / network view, laid out on one shared skeleton."""

from __future__ import annotations

from typing import Any

from ..layouts import bands, skeleton
from ..layouts.skeleton import Skeleton
from ..model import Edge, Group, Node, Page
from . import BuildContext, component_kind, components, register, service_types

# Skeleton box for a group name, checked in this order (e.g. "Managed services" before "Microservices").
BOX_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("external", ("external", "third")),
    ("managed", ("managed",)),
    ("clients", ("client", "channel")),
    ("edge", ("edge", "gateway")),
    ("platform", ("platform", "observ", "operation")),
    ("data", ("data", "storage")),
    ("microservices", ("micro", "service", "application")),
]
TIER_BOXES: list[tuple[str, tuple[str, ...]]] = [
    ("edge", ("public", "dmz", "edge")),
    ("data", ("data", "db", "database", "storage")),
    ("microservices", ("app", "application", "private", "service", "compute")),
]
MANAGED_GROUPS = {"broker": "Messaging"}
AWS_ICONS: list[tuple[str, str]] = [
    ("api gateway", "api_gateway"), ("cognito", "cognito"), ("eventbridge", "eventbridge"), ("sns", "sns"),
    ("sqs", "sqs"), ("msk", "managed_streaming_for_kafka"), ("kinesis", "kinesis"), ("aurora", "aurora"),
    ("dynamodb", "dynamodb"), ("documentdb", "documentdb_with_mongodb_compatibility"), ("rds", "rds"),
    ("elasticache", "elasticache"), ("opensearch", "elasticsearch_service"),
    ("elasticsearch", "elasticsearch_service"), ("s3", "simple_storage_service"), ("cloudfront", "cloudfront"),
    ("waf", "waf"), ("load balanc", "elastic_load_balancing"), ("lambda", "lambda"), ("fargate", "fargate"),
    ("eks", "eks"), ("ecs", "ecs"),
]


def _match(name: str, table: list[tuple[str, tuple[str, ...]]], taken: set[str]) -> str | None:
    lowered = name.lower()
    for key, words in table:
        if key not in taken and any(w in lowered for w in words):
            return key
    return None


def _boxes_for(groups: list[str]) -> tuple[dict[str, str], list[str]]:
    """Skeleton box -> group name, and the group names that fit no box."""
    found: dict[str, str] = {}
    unplaced = []
    for name in groups:
        key = _match(name, BOX_KEYWORDS, set(found))
        if key is None:
            unplaced.append(name)
        else:
            found[key] = name
    return found, unplaced


def _icon(cloud_service: str) -> str | None:
    lowered = cloud_service.lower()
    return next((icon for word, icon in AWS_ICONS if word in lowered), None)


class _Content:
    """What goes into the skeleton, read once from the data."""

    def __init__(self, ctx: BuildContext) -> None:
        self.types = service_types(ctx)
        self.services = [s["service"] for s in ctx.data["subdomains.yaml"]["subdomains"]]
        comps = list(components(ctx).values())
        self.clients = [c for c in comps if c["kind"] == "client"]
        self.edge = [c for c in comps if c["kind"] in ("gateway", "identity-provider")]
        self.stores = [c for c in comps if c["kind"] == "datastore"]
        self.externals = [c for c in comps if c["kind"] == "external"]
        self.managed: dict[str, list[dict[str, Any]]] = {}
        for c in comps:
            if c["kind"] in MANAGED_GROUPS:
                self.managed.setdefault(MANAGED_GROUPS[c["kind"]], []).append(c)
        arch = ctx.data["architecture.yaml"]
        self.mapping = {m["logical_id"]: m for m in arch.get("mapping", [])}
        self.cloud = arch.get("cloud", "")
        self.flows = (ctx.data.get("logical.yaml") or {}).get("flows", [])
        self.node_id = {c["id"]: c.get("service_id", c["id"]) if c["kind"] == "service" else c["id"] for c in comps}

    def skeleton(self) -> Skeleton:
        return skeleton.compute(len(self.services), len(self.stores), len(self.externals), list(self.managed),
                                clients=len(self.clients), edge_items=len(self.edge),
                                managed_items=max((len(v) for v in self.managed.values()), default=1))


def _box_groups(sk: Skeleton, names: dict[str, str], content: _Content, kinds: dict[str, str],
                labels: dict[str, str]) -> list[Group]:
    groups = []
    inner = {"microservices", "data", "managed", "platform"}
    for key in ("clients", "edge", "backend", "microservices", "data", "managed", "platform", "external"):
        if key == "managed" and not content.managed:
            continue
        if key == "platform" and key not in names:
            continue
        x, y, w, h = sk.boxes[key]
        label = labels.get(key) or names.get(key) or {"backend": "Backend"}.get(key, key.capitalize())
        groups.append(Group(key, label, kinds.get(key, "plain"), x, y, w, h,
                            parent="backend" if key in inner else None))
    for name in content.managed:
        x, y, w, h = sk.managed_box(name)
        groups.append(Group(f"managed-{name}", name, "plain", x, y, w, h, parent="managed"))
    return groups


def _place(page: Page, comp: dict[str, Any], kind: str, slot: tuple[float, float, float, float], parent: str,
           content: _Content, physical: bool, shape: str = "box") -> None:
    x, y, w, h = slot
    mapped = content.mapping.get(comp["id"])
    icon = _icon(mapped["cloud_service"]) if physical and mapped and content.cloud == "aws" else None
    label = f"{mapped['cloud_service']}\n({comp['name']})" if physical and mapped else comp["name"]
    page.nodes.append(Node(comp["id"], label, kind, x=x, y=y, w=w, h=h, shape=shape, parent=parent, icon=icon))


def _page(name: str, title: str, sk: Skeleton, content: _Content, groups: list[Group], physical: bool) -> Page:
    page = Page(name, title, [], list(groups), [])
    for i, svc in enumerate(content.services):
        x, y, w, h = sk.service_slot(i)
        page.nodes.append(Node(svc["id"], svc["name"], content.types.get(svc["id"], "supporting"),
                               x=x, y=y, w=w, h=h, shape="hexagon", parent="microservices"))
    for i, comp in enumerate(content.clients):
        _place(page, comp, "client", sk.client_slot(i), "clients", content, physical)
    for i, comp in enumerate(content.edge):
        _place(page, comp, component_kind(comp, content.types), sk.edge_slot(i), "edge", content, physical)
    for i, comp in enumerate(content.stores):
        _place(page, comp, "datastore", sk.data_slot(i), "data", content, physical, shape="cylinder")
    for name, items in content.managed.items():
        for i, comp in enumerate(items):
            _place(page, comp, component_kind(comp, content.types), sk.managed_slot(name, i), f"managed-{name}",
                   content, physical)
    for i, comp in enumerate(content.externals):
        _place(page, comp, "external", sk.external_slot(i), "external", content, physical)
    ids = {n.id for n in page.nodes}
    for i, flow in enumerate(content.flows, 1):
        source, target = content.node_id.get(flow["from"], flow["from"]), content.node_id.get(flow["to"], flow["to"])
        if source in ids and target in ids:
            page.edges.append(Edge(f"flow-{i}", source, target, flow["kind"], label=flow.get("label", "")))
    bands.route(page)
    page.width = max(x + w for x, _, w, _ in sk.boxes.values()) + skeleton.MARGIN
    return page


def build(ctx: BuildContext) -> list[Page]:
    content = _Content(ctx)
    arch = ctx.data["architecture.yaml"]
    shared = ctx.options.get("architecture", {}).get("shared-layout", True)
    high_names, high_rest = _boxes_for(arch["high_level"]["groups"])
    physical_spec = arch["physical"]
    phys_names, phys_rest = _boxes_for(physical_spec["groups"])

    sk_high = content.skeleton()
    sk_phys = sk_high if shared else content.skeleton()  # computed separately when the views need not align

    high_groups = _box_groups(sk_high, high_names, content, {"microservices": "layer", "data": "layer",
                                                              "managed": "layer", "platform": "layer"}, {})
    high = _page("high-level", "High-level architecture", sk_high, content, high_groups, physical=False)
    high.notes = ["Services follow the subdomain order; the physical view uses the same layout."]
    high.notes += [f"Group '{name}' has no place in the layout." for name in high_rest]

    tier_labels: dict[str, str] = {}
    tier_kinds: dict[str, str] = {}
    tier_notes = []
    taken: set[str] = set()
    for tier in physical_spec.get("tiers", []):
        box = _match(f"{tier['id']} {tier['name']}", TIER_BOXES, taken)
        route = "internet route" if tier.get("internet_route") else "no internet route"
        text = f"{tier['name']} subnet {tier.get('cidr', '')} ({route})".replace("  ", " ")
        if box is None:
            tier_notes.append(f"Tier {text}.")
            continue
        taken.add(box)
        tier_labels[box] = f"{phys_names.get(box, box.capitalize())}: {text}"
        tier_kinds[box] = {"edge": "subnet-public", "data": "subnet-data"}.get(box, "subnet-app")
    zones = physical_spec.get("availability_zones", 1)
    regions = physical_spec.get("regions", 1)
    tier_labels["backend"] = f"Private application network ({zones} availability zones)"
    phys_groups = _box_groups(sk_phys, phys_names, content, {**tier_kinds, "managed": "layer", "platform": "layer"},
                              tier_labels)
    ex, ey, _, eh = sk_phys.boxes["edge"]
    bx, _, bw, _ = sk_phys.boxes["backend"]
    vpc = Group("vpc", f"VPC across {zones} availability zones", "vpc", ex - 20, ey - 34, bx + bw + 20 - (ex - 20),
                eh + 54)
    cloud = content.cloud.upper() if content.cloud else "Cloud"
    region = Group("region", f"{cloud} region" + (f" (x{regions})" if regions > 1 else ""), "region",
                   vpc.x - 25, vpc.y - 34, vpc.w + 50, vpc.h + 59)
    physical = _page("physical", "Physical view and network", sk_phys, content, [region, vpc, *phys_groups],
                     physical=True)
    physical.notes = [*physical_spec.get("security_rules", []), *tier_notes]
    physical.notes += [f"Group '{name}' has no place in the layout." for name in phys_rest]
    return [high, physical]


register("architecture", build)
