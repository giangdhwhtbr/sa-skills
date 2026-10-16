"""Builders for steps 02-10 (Tracks 4-6 of sad-qwi), run on the example design sets."""

import copy
import re
from pathlib import Path
from typing import Any

import pytest
from sacheck import catalog, config
from sadiagram import builders, geometry
from sadiagram.builders import BuildContext
from sadiagram.model import Page

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "sa-design" / "references"
CLINIC = ROOT / "examples" / "clinic-booking" / "design"
FOOD = ROOT / "examples" / "food-delivery" / "design"
FOOD_DETAILED = ROOT / "examples" / "food-delivery" / "design-detailed"


def context(design: Path, **overrides: dict[str, Any]) -> BuildContext:
    data = {p.name: catalog.parse_yaml(p.read_text()) for p in design.glob("*.yaml")}
    options = copy.deepcopy(config.effective(design, REFS).options)
    for step, values in overrides.items():
        options[step.replace("_", "-")].update(values)
    return BuildContext(data, options, catalog.load_vendor_terms(REFS))


def build(key: str, ctx: BuildContext) -> list[Page]:
    return builders.BUILDERS[key][2](ctx)


def node_ids(pages: list[Page]) -> set[str]:
    return {n.id for p in pages for n in p.nodes}


def readable(pages: list[Page]) -> None:
    for page in pages:
        assert geometry.overlaps(page) == [], page.title
        assert geometry.outside_parent(page) == [], page.title
        assert geometry.edge_crossings(page) == [], page.title
        assert len(page.nodes) <= 40, page.title


# ---------- Track 4: band builders ----------

# REQ-DIAGRAMS-005
def test_functions_complete() -> None:
    ctx = context(CLINIC)
    pages = build("functions", ctx)
    groups = ctx.data["functions.yaml"]["groups"]
    assert node_ids(pages) == {f["id"] for g in groups for f in g["functions"]}
    assert [g.id for g in pages[0].groups] == [g["id"] for g in groups]
    assert "Patient" in pages[0].groups[0].label
    kinds = [{n.kind for n in pages[0].nodes if n.parent == g["id"]} for g in groups]
    assert all(len(k) == 1 for k in kinds) and len({next(iter(k)) for k in kinds}) == min(3, len(groups))
    assert set(pages[0].legend_labels.values()) >= {groups[0]["name"]}


# REQ-DIAGRAMS-005
def test_subdomains_bands() -> None:
    ctx = context(CLINIC)
    pages = build("subdomains", ctx)
    page = pages[0]
    bands = {g.id: g for g in page.groups}
    for sub in ctx.data["subdomains.yaml"]["subdomains"]:
        node = next(n for n in page.nodes if n.id == sub["id"])
        assert node.parent == f"band-{sub['type']}"
        assert node.kind == sub["type"] and node.shape == "ellipse"
        assert sub["name"] in node.label and sub["service"]["name"] in node.label
    assert all(b.parent == "domain" for k, b in bands.items() if k.startswith("band-"))


# REQ-DIAGRAMS-005, REQ-DIAGRAMS-006
def test_logical_complete_and_neutral() -> None:
    ctx = context(CLINIC)
    pages = build("logical-view", ctx)
    data = ctx.data["logical.yaml"]
    assert node_ids(pages) == {c["id"] for layer in data["layers"] for c in layer["components"]}
    assert [g.id for g in pages[0].groups] == [layer["id"] for layer in data["layers"]]
    assert len(pages[0].edges) == len(data["flows"])
    assert [e.label for e in pages[0].edges] == [f.get("label", "") for f in data["flows"]]
    labels = " ".join(n.label for n in pages[0].nodes).lower()
    assert not [t for t in ctx.vendor_terms if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", labels)]
    service = next(n for n in pages[0].nodes if n.id == "scheduling-service")
    assert service.kind == "core"


# REQ-DIAGRAMS-006
def test_logical_rejects_vendor_names() -> None:
    ctx = context(CLINIC)
    ctx.data["logical.yaml"]["layers"][0]["components"][0]["name"] = f"Web on {ctx.vendor_terms[0]}"
    with pytest.raises(ValueError, match="vendor"):
        build("logical-view", ctx)
    ctx = context(CLINIC, logical_view={"vendors": "technology-hints"})
    ctx.data["logical.yaml"]["layers"][0]["components"][0]["name"] = f"Web on {ctx.vendor_terms[0]}"
    assert build("logical-view", ctx)


# REQ-DIAGRAMS-005
def test_patterns_pages() -> None:
    ctx = context(CLINIC)
    pages = build("patterns", ctx)
    patterns = ctx.data["patterns.yaml"]["patterns"]
    assert len(pages) == 3
    for page, pattern in zip(pages, patterns, strict=True):
        prefix = pattern["id"][0].upper()
        assert [e.label for e in page.edges] == [f"{prefix}{s['n']}" for s in pattern["steps"]]
        assert any(f"{prefix}1" in note for note in page.notes)
    combined = build("patterns", context(CLINIC, patterns={"split": "combined"}))
    assert len(combined) == 1
    assert len(combined[0].edges) == sum(len(p["steps"]) for p in patterns)
    assert len(combined[0].groups) >= 3


# REQ-DIAGRAMS-009
def test_band_pages_readable() -> None:
    for design in (CLINIC, FOOD, FOOD_DETAILED):
        ctx = context(design)
        for key in ("functions", "subdomains", "logical-view", "patterns"):
            if f"{key}.yaml" in ctx.data or builders.BUILDERS[key][1][-1] in ctx.data:
                readable(build(key, ctx))
