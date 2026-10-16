"""Mechanical checks of a design folder: completeness, schemas, script rules and cross-step consistency."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog, config, schemas
from .model import Finding

STATE_FILE = "design-state.yaml"
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20,
}
_COUNT = re.compile(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:micro)?services\b", re.IGNORECASE)
MAPPED_KINDS = ("gateway", "identity-provider", "broker", "datastore")

Hit = tuple[str, str, str]  # (file, item, message)


@dataclass(frozen=True)
class Context:
    """Everything a rule needs: loaded data files, Markdown, configuration and catalogue."""

    design_dir: Path
    refs: Path
    cfg: config.EffectiveConfig
    data: dict[str, Any]
    markdown: dict[str, str]
    steps: list[catalog.StepSpec]
    state: dict[str, Any]

    def get(self, name: str) -> Any:
        """A loaded data file, or None when it is missing or invalid."""
        return self.data.get(name)


# ---------- helpers ----------

def _ids(items: Iterable[dict[str, Any]] | None, key: str = "id") -> list[str]:
    return [i[key] for i in (items or [])]


def _service_ids(ctx: Context) -> set[str]:
    return {s["service"]["id"] for s in (ctx.get("subdomains.yaml") or {}).get("subdomains", [])}


def _subdomain_ids(ctx: Context) -> set[str]:
    return set(_ids((ctx.get("subdomains.yaml") or {}).get("subdomains")))


def _components(ctx: Context) -> list[dict[str, Any]]:
    return [c for layer in (ctx.get("logical.yaml") or {}).get("layers", []) for c in layer["components"]]


def _actor_ids(ctx: Context) -> set[str]:
    return set(_ids((ctx.get("brief.yaml") or {}).get("actors")))


def _function_ids(ctx: Context) -> set[str]:
    groups = (ctx.get("functions.yaml") or {}).get("groups", [])
    return {f["id"] for g in groups for f in g["functions"]}


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _vendor_hit(text: str, terms: list[str]) -> str | None:
    lowered = text.lower()
    for term in terms:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered):
            return term
    return None


# ---------- script rules (one function per rule ID) ----------

def rule_br_01(ctx: Context) -> list[Hit]:
    brief = ctx.get("brief.yaml")
    if brief is None:
        return []
    seen: set[str] = set()
    hits = []
    for key in ("pain_points", "actors", "nfrs"):
        for item_id in _ids(brief.get(key)):
            if item_id in seen:
                hits.append(("brief.yaml", item_id, f"duplicate ID '{item_id}'"))
            seen.add(item_id)
    return hits


def rule_fn_02(ctx: Context) -> list[Hit]:
    functions = ctx.get("functions.yaml")
    if functions is None:
        return []
    actors = _actor_ids(ctx)
    return [
        ("functions.yaml", g["id"], "group names no actor from brief.yaml")
        for g in functions.get("groups", []) if not any(a in actors for a in g["actor_ids"])
    ]


def rule_sd_01(ctx: Context) -> list[Hit]:
    subdomains = ctx.get("subdomains.yaml")
    if subdomains is None or any(s["type"] == "core" for s in subdomains.get("subdomains", [])):
        return []
    return [("subdomains.yaml", "subdomains", "no subdomain is classified as core")]


def rule_sd_02(ctx: Context) -> list[Hit]:
    subdomains = (ctx.get("subdomains.yaml") or {}).get("subdomains", [])
    seen: dict[str, str] = {}
    hits = []
    for s in subdomains:
        service_id = s["service"]["id"]
        if service_id in seen:
            hits.append(("subdomains.yaml", s["id"], f"service '{service_id}' is also used by '{seen[service_id]}'"))
        seen.setdefault(service_id, s["id"])
    return hits


def rule_cm_01(ctx: Context) -> list[Hit]:
    externals = (ctx.get("context-map.yaml") or {}).get("externals") or []
    return [("context-map.yaml", e["id"], "external system on a ud-only context map") for e in externals]


def rule_cm_02(ctx: Context) -> list[Hit]:
    cmap = ctx.get("context-map.yaml")
    if cmap is None:
        return []
    known = _subdomain_ids(ctx)
    hits = []
    for r in cmap.get("relationships", []):
        item = f"{r['upstream']}->{r['downstream']}"
        unknown = [end for end in (r["upstream"], r["downstream"]) if end not in known]
        if unknown:
            hits.append(("context-map.yaml", item, f"unknown context(s): {', '.join(unknown)}"))
        elif r["upstream"] == r["downstream"]:
            hits.append(("context-map.yaml", item, "upstream and downstream are the same context"))
    return hits


def rule_cm_03(ctx: Context) -> list[Hit]:
    cmap = ctx.get("context-map.yaml")
    if cmap is None:
        return []
    used = {end for r in cmap.get("relationships", []) for end in (r["upstream"], r["downstream"])}
    return [("context-map.yaml", s, "context appears in no relationship") for s in sorted(_subdomain_ids(ctx) - used)]


def rule_ag_01(ctx: Context) -> list[Hit]:
    aggregates = (ctx.get("aggregates.yaml") or {}).get("aggregates", [])
    return [
        ("aggregates.yaml", a["id"], "entities, value objects or events listed under roots-only")
        for a in aggregates if a["entities"] or a["value_objects"] or a["events"]
    ]


def rule_ag_02(ctx: Context) -> list[Hit]:
    data = ctx.get("aggregates.yaml")
    if data is None:
        return []
    known_subdomains = _subdomain_ids(ctx)
    known = set(_ids(data.get("aggregates")))
    hits = [
        ("aggregates.yaml", a["id"], f"unknown subdomain '{a['subdomain_id']}'")
        for a in data.get("aggregates", []) if a["subdomain_id"] not in known_subdomains
    ]
    for ref in data.get("references", []):
        item = f"{ref['from']}->{ref['to']}"
        if ref["from"] not in known or ref["to"] not in known:
            hits.append(("aggregates.yaml", item, "reference joins an unknown aggregate"))
        elif not ref["via"]:
            hits.append(("aggregates.yaml", item, "reference has no ID field (via)"))
    return hits


def rule_ag_03(ctx: Context) -> list[Hit]:
    data = ctx.get("aggregates.yaml")
    if data is None:
        return []
    covered = {a["subdomain_id"] for a in data.get("aggregates", [])}
    covered |= {n["subdomain_id"] for n in data.get("no_aggregate", [])}
    return [
        ("aggregates.yaml", s, "subdomain has no aggregate and no no_aggregate entry")
        for s in sorted(_subdomain_ids(ctx) - covered)
    ]


def rule_uc_01(ctx: Context) -> list[Hit]:
    data = ctx.get("use-cases.yaml")
    if data is None:
        return []
    actors, functions = _actor_ids(ctx), _function_ids(ctx)
    hits = []
    for uc in data.get("use_cases", []):
        bad_actors = [a for a in uc["actor_ids"] if a not in actors]
        bad_functions = [f for f in uc["function_ids"] if f not in functions]
        if not uc["actor_ids"] or bad_actors:
            hits.append(("use-cases.yaml", uc["id"], f"unknown or missing actor(s): {', '.join(bad_actors) or 'none'}"))
        if bad_functions:
            hits.append(("use-cases.yaml", uc["id"], f"unknown function(s): {', '.join(bad_functions)}"))
    return hits


def rule_lv_01(ctx: Context) -> list[Hit]:
    terms = catalog.load_vendor_terms(ctx.refs)
    hits = []
    logical = ctx.get("logical.yaml")
    if logical is not None:
        for layer in logical.get("layers", []):
            for item in [layer, *layer["components"]]:
                term = _vendor_hit(item["name"], terms)
                if term:
                    hits.append(("logical.yaml", item["id"], f"names '{term}'"))
        for flow in logical.get("flows", []):
            term = _vendor_hit(flow.get("label", ""), terms)
            if term:
                hits.append(("logical.yaml", f"{flow['from']}->{flow['to']}", f"names '{term}'"))
    md = ctx.markdown.get("07-logical-view.md")
    if md is not None:
        term = _vendor_hit(md, terms)
        if term:
            hits.append(("07-logical-view.md", term, f"names '{term}'"))
    return hits


def rule_lv_02(ctx: Context) -> list[Hit]:
    if ctx.get("logical.yaml") is None:
        return []
    present = {c.get("service_id") for c in _components(ctx) if c["kind"] == "service"}
    return [
        ("logical.yaml", s, "service has no service component in the logical view")
        for s in sorted(_service_ids(ctx) - present)
    ]


def rule_sg_01(ctx: Context) -> list[Hit]:
    saga = ctx.get("saga.yaml")
    if saga is None:
        return []
    kinds = [s["kind"] for s in saga.get("scenarios", [])]
    needed = int(ctx.cfg.options.get("saga", {}).get("failure-scenarios", 2))
    if "happy" in kinds and kinds.count("failure") >= needed:
        return []
    return [("saga.yaml", saga["flow"]["id"],
             f"needs a happy scenario and {needed} failure scenarios; has {kinds.count('failure')}")]


def rule_sg_02(ctx: Context) -> list[Hit]:
    saga = ctx.get("saga.yaml")
    if saga is None:
        return []
    return [
        ("saga.yaml", s["id"], "failure scenario has no compensate step")
        for s in saga.get("scenarios", [])
        if s["kind"] == "failure" and not any(step["kind"] == "compensate" for step in s["steps"])
    ]


def rule_sg_03(ctx: Context) -> list[Hit]:
    """Role check: the orchestrator is one of our services; participants are services or external systems.
    Unknown IDs are reported by XS-01."""
    saga = ctx.get("saga.yaml")
    if saga is None:
        return []
    services = _service_ids(ctx)
    externals = {c["id"] for c in _components(ctx) if c["kind"] == "external"}
    externals |= set(_ids((ctx.get("context-map.yaml") or {}).get("externals")))
    externals |= {a["id"] for a in (ctx.get("brief.yaml") or {}).get("actors", []) if a["kind"] == "system"}
    hits = []
    orchestrator = saga["flow"]["orchestrator"]
    if orchestrator not in services:
        hits.append(("saga.yaml", orchestrator, "the orchestrator must be one of our services"))
    component_ids = {c["id"] for c in _components(ctx)}
    for p in saga.get("participants", []):
        if p in component_ids and p not in services and p not in externals:
            hits.append(("saga.yaml", p, "participant is neither a service nor an external system"))
    return hits


def rule_pt_01(ctx: Context) -> list[Hit]:
    patterns = ctx.get("patterns.yaml")
    if patterns is None:
        return []
    present = set(_ids(patterns.get("patterns")))
    return [("patterns.yaml", p, "pattern is not described") for p in ("security", "observability", "resilience")
            if p not in present]


def rule_ar_01(ctx: Context) -> list[Hit]:
    arch = ctx.get("architecture.yaml")
    if arch is None:
        return []
    mapped = {m["logical_id"] for m in arch.get("mapping", [])}
    return [
        ("architecture.yaml", c["id"], f"{c['kind']} component has no cloud mapping")
        for c in _components(ctx) if c["kind"] in MAPPED_KINDS and c["id"] not in mapped
    ]


def rule_ar_02(ctx: Context) -> list[Hit]:
    arch = ctx.get("architecture.yaml")
    if arch is None or arch["high_level"]["groups"] == arch["physical"]["groups"]:
        return []
    return [("architecture.yaml", "groups", "high-level and physical groups differ (names or order)")]


def rule_ar_03(ctx: Context) -> list[Hit]:
    arch = ctx.get("architecture.yaml")
    if arch is None:
        return []
    return [
        ("architecture.yaml", t["id"], "the data tier has an internet route")
        for t in arch["physical"].get("tiers", []) if "data" in (t["id"], t["name"]) and t["internet_route"]
    ]


def rule_st_01(ctx: Context) -> list[Hit]:
    stack = ctx.get("stack.yaml")
    if stack is None:
        return []
    return [("stack.yaml", layer["id"], "layer needs a choice and a reason")
            for layer in stack.get("layers", []) if not layer["choice"].strip() or not layer["reason"].strip()]


def rule_ad_01(ctx: Context) -> list[Hit]:
    adrs = ctx.get("adrs.yaml")
    if adrs is None:
        return []
    return [("adrs.yaml", a["id"], "ADR needs at least one alternative and a trade-off")
            for a in adrs.get("adrs", []) if not a["alternatives"] or not a["tradeoff"].strip()]


def rule_tr_01(ctx: Context) -> list[Hit]:
    brief, adrs = ctx.get("brief.yaml"), ctx.get("adrs.yaml")
    if brief is None or adrs is None:
        return []
    covered = {p for a in adrs.get("adrs", []) for p in a["pain_points"]}
    descriptions = " ".join(s["description"] for s in (ctx.get("subdomains.yaml") or {}).get("subdomains", []))
    return [("brief.yaml", p["id"], "pain point is not addressed by any ADR or subdomain")
            for p in brief.get("pain_points", []) if p["id"] not in covered and p["id"] not in descriptions]


def rule_xs_01(ctx: Context) -> list[Hit]:
    """Generic ID references. Context-map ends, aggregate references, use-case actors and functions and
    function-group actors are covered by CM-02, AG-02, UC-01 and FN-02."""
    hits: list[Hit] = []

    def check(file: str, refs: Iterable[str], known: set[str], what: str) -> None:
        for ref in refs:
            if ref not in known:
                hits.append((file, ref, f"unknown {what} '{ref}'"))

    components = {c["id"] for c in _components(ctx)}
    services = _service_ids(ctx)
    if (sub := ctx.get("subdomains.yaml")) is not None and ctx.get("functions.yaml") is not None:
        check("subdomains.yaml", [f for s in sub.get("subdomains", []) for f in s["function_ids"]],
              _function_ids(ctx), "function")
    if (logical := ctx.get("logical.yaml")) is not None:
        check("logical.yaml", [c["service_id"] for c in _components(ctx) if "service_id" in c], services, "service")
        check("logical.yaml", [e for f in logical.get("flows", []) for e in (f["from"], f["to"])], components,
              "component")
    if (uc := ctx.get("use-cases.yaml")) is not None:
        known_uc = set(_ids(uc.get("use_cases")))
        check("use-cases.yaml", [r for u in uc.get("use_cases", []) for r in u["includes"] + u["extends"]],
              known_uc, "use case")
    externals = set(_ids((ctx.get("context-map.yaml") or {}).get("externals")))
    saga_known = services | components | _actor_ids(ctx) | externals
    if (saga := ctx.get("saga.yaml")) is not None:
        refs = [saga["flow"]["orchestrator"], *saga.get("participants", [])]
        refs += [e for s in saga.get("scenarios", []) for step in s["steps"] for e in (step["from"], step["to"])]
        check("saga.yaml", list(dict.fromkeys(refs)), saga_known, "participant")
    if (patterns := ctx.get("patterns.yaml")) is not None:
        refs = [e for p in patterns.get("patterns", []) for step in p["steps"] for e in (step["from"], step["to"])]
        check("patterns.yaml", list(dict.fromkeys(refs)), components | services, "component")
    if (arch := ctx.get("architecture.yaml")) is not None:
        check("architecture.yaml", [m["logical_id"] for m in arch.get("mapping", [])], components, "logical component")
    if (adrs := ctx.get("adrs.yaml")) is not None and ctx.get("brief.yaml") is not None:
        known_pp = set(_ids(ctx.get("brief.yaml").get("pain_points")))
        check("adrs.yaml", [p for a in adrs.get("adrs", []) for p in a["pain_points"]], known_pp, "pain point")
    return hits


def rule_xs_02(ctx: Context) -> list[Hit]:
    if ctx.get("subdomains.yaml") is None:
        return []
    count = len(_service_ids(ctx))
    hits = []
    for name, text in sorted(ctx.markdown.items()):
        for match in _COUNT.finditer(text):
            word = match.group(1).lower()
            stated = int(word) if word.isdigit() else NUMBER_WORDS[word]
            if stated != count:
                hits.append((name, match.group(0), f"states {stated} services; subdomains.yaml has {count}"))
    return hits


# ---------- diagrams (local copy of sadiagram.stamp, kept identical by tests/test_checks.py) ----------

DIAGRAMS_DIR = "diagrams"
STAMP_ATTRIBUTE = "sa-source-hash"
DRAWN: dict[str, tuple[int, list[str], list[tuple[str, str]]]] = {
    "functions": (2, ["brief.yaml", "functions.yaml"], []),
    "subdomains": (3, ["subdomains.yaml"], []),
    "context-map": (4, ["subdomains.yaml", "context-map.yaml"], [("context-map", "detail")]),
    "aggregates": (5, ["subdomains.yaml", "aggregates.yaml"], [("aggregates", "detail")]),
    "use-cases": (6, ["brief.yaml", "functions.yaml", "use-cases.yaml"], []),
    "logical-view": (7, ["logical.yaml"], [("logical-view", "vendors")]),
    "saga": (8, ["subdomains.yaml", "logical.yaml", "saga.yaml"], []),
    "patterns": (9, ["logical.yaml", "patterns.yaml"], [("patterns", "split")]),
    "architecture": (10, ["subdomains.yaml", "logical.yaml", "architecture.yaml"], [("architecture", "shared-layout")]),
}


def diagram_hash(design_dir: Path, key: str, options: dict[str, dict[str, Any]], cloud: str) -> str:
    """Same value as sadiagram.stamp.step_hash: the data files and options a step's diagram is drawn from."""
    _, inputs, option_deps = DRAWN[key]
    picked: dict[str, Any] = {f"{step}.{name}": options.get(step, {}).get(name) for step, name in option_deps}
    if key == "architecture":
        picked["cloud"] = cloud
    digest = hashlib.sha256()
    for name in inputs:
        path = design_dir / name
        digest.update(name.encode() + b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
        digest.update(b"\0")
    digest.update(json.dumps(picked, sort_keys=True).encode())
    return digest.hexdigest()


def rule_dg_01(ctx: Context) -> list[Hit]:
    folder = ctx.design_dir / DIAGRAMS_DIR
    hits = []
    for key, (number, _, _) in DRAWN.items():
        path = folder / f"{number:02d}-{key}.drawio"
        if not path.exists():
            continue
        try:
            recorded = ET.parse(path).getroot().get(STAMP_ATTRIBUTE)
        except ET.ParseError:
            recorded = None
        if recorded != diagram_hash(ctx.design_dir, key, ctx.cfg.options, ctx.cfg.cloud):
            hits.append((f"{DIAGRAMS_DIR}/{path.name}", path.name,
                         "diagram is out of date with its data; run /sa-diagrams to redraw it"))
    return hits


# ---------- deck (local copy of sadeck.stamp, kept identical by tests/test_checks.py) ----------

DECK_STEP_NUMBERS = {key: number for key, (number, _, _) in DRAWN.items()}


def _deck_page(design_dir: Path, step: str, page: int) -> bytes:
    path = design_dir / DIAGRAMS_DIR / f"{DECK_STEP_NUMBERS.get(step, 0):02d}-{step}.drawio"
    try:
        pages = ET.parse(path).getroot().findall("diagram")
    except (OSError, ET.ParseError):
        return b"<missing>"
    if not 1 <= page <= len(pages):
        return b"<missing>"
    return ET.tostring(pages[page - 1])


def deck_hash(design_dir: Path) -> str:
    """Same value as sadeck.stamp.deck_hash: deck.yaml, its image and logo files, and the diagram pages it shows."""
    deck_dir = design_dir / "deck"
    source = (deck_dir / "deck.yaml").read_bytes()
    digest = hashlib.sha256(source)
    try:
        data = schemas.parse(source.decode()) or {}
    except (UnicodeDecodeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    files = [(data.get("theme") or {}).get("logo")]
    refs: list[tuple[str, int]] = []
    for section in data.get("sections") or []:
        for slide in section.get("slides") or []:
            block = slide.get("block") or {}
            if block.get("type") == "image":
                files.append(block.get("file"))
            if block.get("type") == "diagrams":
                sides = [block.get(side) for side in ("left", "right")]
                refs += [(side["step"], side["page"]) for side in sides if isinstance(side, dict)]
            elif "step" in block and "page" in block:
                refs.append((block["step"], block["page"]))
    for name in files:
        if name:
            path = deck_dir / name
            digest.update(name.encode() + b"\0" + (path.read_bytes() if path.is_file() else b"<missing>"))
    for step, page in refs:
        digest.update(f"{step}:{page}".encode() + b"\0" + _deck_page(design_dir, step, page))
    return digest.hexdigest()


def rule_dk_01(ctx: Context) -> list[Hit]:
    stamp_file = ctx.design_dir / "deck" / ".deck-stamp.json"
    if not stamp_file.exists() or not (ctx.design_dir / "deck" / "deck.yaml").exists():
        return []
    try:
        recorded = json.loads(stamp_file.read_text()).get("hash")
    except (OSError, ValueError, AttributeError):
        recorded = None
    if recorded == deck_hash(ctx.design_dir):
        return []
    message = "deck is out of date with deck.yaml or its diagrams; run /sa-deck to rebuild it"
    return [("deck/deck.html", "deck.html", message)]


RULES: dict[str, Callable[[Context], list[Hit]]] = {
    "BR-01": rule_br_01, "FN-02": rule_fn_02, "SD-01": rule_sd_01, "SD-02": rule_sd_02,
    "CM-01": rule_cm_01, "CM-02": rule_cm_02, "CM-03": rule_cm_03,
    "AG-01": rule_ag_01, "AG-02": rule_ag_02, "AG-03": rule_ag_03, "UC-01": rule_uc_01,
    "LV-01": rule_lv_01, "LV-02": rule_lv_02, "SG-01": rule_sg_01, "SG-02": rule_sg_02, "SG-03": rule_sg_03,
    "PT-01": rule_pt_01, "AR-01": rule_ar_01, "AR-02": rule_ar_02, "AR-03": rule_ar_03, "ST-01": rule_st_01,
    "AD-01": rule_ad_01, "TR-01": rule_tr_01, "XS-01": rule_xs_01, "XS-02": rule_xs_02,
    "DG-01": rule_dg_01, "DK-01": rule_dk_01,
}


# ---------- orchestration ----------

def load_state(design_dir: Path) -> dict[str, Any]:
    """Read design-state.yaml (validated by the caller through schemas)."""
    return schemas.parse((design_dir / STATE_FILE).read_text()) or {"version": 1, "steps": []}


def dependents(step_key: str, steps: list[catalog.StepSpec]) -> list[str]:
    """Steps that read the step's data file, directly or transitively, in step order."""
    by_key = {s.key: s for s in steps}
    found: set[str] = set()
    frontier = [by_key[step_key].data]
    while frontier:
        data_file = frontier.pop()
        for s in steps:
            if data_file in s.inputs and s.key not in found:
                found.add(s.key)
                frontier.append(s.data)
    return [s.key for s in steps if s.key in found]


def changed_files(design_dir: Path) -> list[str]:
    """Files whose content no longer matches the hash recorded in design-state.yaml."""
    changed = []
    for step in load_state(design_dir).get("steps", []):
        for name, digest in (step.get("files") or {}).items():
            path = design_dir / name
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                changed.append(name)
    return sorted(changed)


def run(design_dir: Path, refs: Path, step: str | None = None) -> tuple[
        config.EffectiveConfig, list[Finding], list[dict[str, str]]]:
    """Run the checks. Returns the effective configuration, the findings that are not accepted exceptions,
    and every recorded exception."""
    cfg = config.effective(design_dir, refs)
    steps = catalog.load_steps(refs)
    by_key = {s.key: s for s in steps}
    rules = catalog.load_rules(refs)
    findings: list[Finding] = list(cfg.problems)

    findings += schemas.validate(design_dir / STATE_FILE, refs / "schema" / "design-state.schema.yaml")
    state = load_state(design_dir)
    status = {s["key"]: s["status"] for s in state.get("steps", [])}
    if step is not None and step not in by_key:
        raise ValueError(f"unknown step '{step}'")
    checked = [step] if step else [k for k in catalog.STEP_KEYS if status.get(k) == "done" and k in by_key]

    data: dict[str, Any] = {}
    markdown: dict[str, str] = {}
    for key in (k for k in catalog.STEP_KEYS if k in by_key and (status.get(k) == "done" or k == step)):
        spec = by_key[key]
        for name in (spec.data, spec.markdown):
            if not (design_dir / name).exists() and key in checked:
                findings.append(Finding("MISSING", "error", name, key, f"step '{key}' is done but {name} is missing"))
        if (design_dir / spec.markdown).exists():
            markdown[spec.markdown] = (design_dir / spec.markdown).read_text()
        if (design_dir / spec.data).exists():
            parsed, problem = schemas.load_yaml(design_dir / spec.data)
            schema = schemas.schema_for(spec, refs)
            problems = [problem] if problem else schemas.validate_data(parsed, spec.data, schema)
            if key in checked:
                findings += problems
            if not problems:
                data[spec.data] = parsed

    ctx = Context(design_dir, refs, cfg, data, markdown, steps, state)
    for rule_id, function in RULES.items():
        rule = rules[rule_id]
        in_scope = rule.step in checked or (rule.step == "all" and step is None)
        if not in_scope or not config.rule_active(rule, cfg):
            continue
        severity = cfg.severities[rule_id]
        for file, item, message in function(ctx):
            findings.append(Finding(rule_id, "error" if severity == "error" else "warn", file, item, message))

    exceptions = [
        {"step": s["key"], "rule": e["rule"], "reason": e["reason"]}
        for s in state.get("steps", []) for e in (s.get("exceptions") or [])
    ]
    accepted = {(e["step"], e["rule"]) for e in exceptions}
    kept = [f for f in findings if not _accepted(f, rules, accepted)]
    return cfg, kept, exceptions


def _accepted(finding: Finding, rules: dict[str, catalog.RuleSpec], accepted: set[tuple[str, str]]) -> bool:
    rule = rules.get(finding.rule)
    if rule is None:
        return False
    return any(r == finding.rule and (rule.step == "all" or step == rule.step) for step, r in accepted)
