"""Draft deck.yaml in 4+1 view order from the steps that are done, with seconds scaled to the talk length."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml
from sacheck import checks, config

from .stamp import NUMBERS

WEIGHTS = {"cover": 20, "agenda": 25, "table": 75, "diagram": 70, "title": 20}
MIN_SECONDS = 15
MAX_ROWS = 8
HEADER = """\
# Draft deck from /sa-deck --outline. Before rendering, fill every empty `message` (one-line key message)
# and `notes` (spoken script, about 130 words per minute of `seconds`), complete the empty table cells, and
# cut or reorder slides to fit the talk. The skill guide explains each slide: skills/sa-deck/references/outline.md
"""


def _pages(design_dir: Path, step: str) -> list[str]:
    """Page titles of a drawn step (empty when the step has not been drawn)."""
    path = design_dir / "diagrams" / f"{NUMBERS[step]:02d}-{step}.drawio"
    try:
        return [d.get("name", "") for d in ET.parse(path).getroot().findall("diagram")]
    except (OSError, ET.ParseError):
        return []


def _slide(title: str, block: dict[str, Any] | None, weight: str) -> dict[str, Any]:
    slide: dict[str, Any] = {"title": title, "message": ""}
    if block is not None:
        slide["block"] = block
    slide.update(notes="", seconds=WEIGHTS[weight])
    return slide


def _diagram(title: str, step: str, page: int = 1) -> dict[str, Any]:
    return _slide(title, {"type": "diagram", "step": step, "page": page}, "diagram")


def _tables(title: str, header: list[str], rows: list[list[str]]) -> list[dict[str, Any]]:
    """One table slide per 8 rows, numbered when the table continues."""
    chunks = [rows[i:i + MAX_ROWS] for i in range(0, len(rows), MAX_ROWS)] or [[[""] * len(header)]]
    return [_slide(f"{title} ({k}/{len(chunks)})" if len(chunks) > 1 else title,
                   {"type": "table", "header": header, "rows": chunk}, "table")
            for k, chunk in enumerate(chunks, 1)]


def _use_case_titles(design_dir: Path, data: dict[str, Any]) -> list[str]:
    drawn = _pages(design_dir, "use-cases")
    if drawn:
        return drawn
    cases = (data.get("use-cases.yaml") or {}).get("use_cases", [])
    groups = (data.get("functions.yaml") or {}).get("groups", [])
    return [f"Use cases: {g['name']}" for g in groups if any(set(c["actor_ids"]) & set(g["actor_ids"]) for c in cases)]


def _sections(design_dir: Path, done: set[str], data: dict[str, Any], options: dict[str, Any]) -> list[dict]:
    out: list[tuple[str, list[dict[str, Any]]]] = []
    brief = data.get("brief.yaml") or {}

    intro = []
    if "brief" in done:
        intro += _tables("Proposed solution", ["Problem", "Answer"],
                         [[p["text"], ""] for p in brief.get("pain_points", [])])
    if "functions" in done:
        intro.append(_diagram("Main business functions", "functions"))
    out.append(("Introduction", intro))

    domain = []
    domain_steps = (("subdomains", "Subdomains"), ("context-map", "Context map"), ("aggregates", "Aggregate roots"))
    for step, title in domain_steps:
        if step in done:
            domain.append(_diagram(title, step))
    out.append(("Domain design", domain))

    if "use-cases" in done:
        out.append(("Use case view", [_diagram(t, "use-cases", i) for i, t in
                                      enumerate(_use_case_titles(design_dir, data), 1)]))
    if "logical-view" in done:
        out.append(("Logical view", [_diagram("Logical view", "logical-view")]))
    if "saga" in done:
        saga = data.get("saga.yaml") or {}
        flow = saga.get("flow", {}).get("name", "Core flow")
        out.append(("Process view", [_diagram(f"Saga: {flow}: {s['name']}", "saga", i)
                                     for i, s in enumerate(saga.get("scenarios", []), 1)]))
    if "patterns" in done:
        patterns = (data.get("patterns.yaml") or {}).get("patterns", [])
        if options.get("patterns", {}).get("split", "one-per-pattern") == "one-per-pattern":
            slides = [_diagram(f"{p['id'].capitalize()} pattern", "patterns", i) for i, p in enumerate(patterns, 1)]
        else:
            slides = [_diagram("Core patterns", "patterns")]
        out.append(("Core patterns", slides))
    if "architecture" in done:
        out.append(("High-level and physical view", [_diagram("High-level architecture", "architecture", 1),
                                                     _diagram("Physical view and network", "architecture", 2)]))
    development = []
    if "stack" in done:
        development += _tables("Technology stack", ["Layer", "Choice", "Why"],
                               [[x["name"], x["choice"], x["reason"]] for x in (data.get("stack.yaml") or {})
                                .get("layers", [])])
    if "adrs" in done:
        development += _tables("Architecture decisions", ["Decision", "Alternatives", "Trade-off"],
                               [[a["title"], "; ".join(a.get("alternatives", [])), a.get("tradeoff", "")]
                                for a in (data.get("adrs.yaml") or {}).get("adrs", [])])
    out.append(("Development view", development))

    sections = [{"title": "Agenda", "slides": [_slide("Agenda", {"type": "agenda"}, "agenda")]}]
    sections += [{"title": title, "slides": slides} for title, slides in out if slides]
    sections.append({"title": "Q&A", "slides": [_slide("Questions", None, "title")]})
    return sections


def _fit(cover: dict[str, Any], slides: list[dict[str, Any]], budget: int) -> None:
    """Scale every slide's seconds down to the budget, in steps of 5 s and at least 15 s each."""
    items = [cover, *slides]
    total = sum(i["seconds"] for i in items)
    if total <= budget:
        return
    factor = budget / total
    for item in items:
        item["seconds"] = max(MIN_SECONDS, int(item["seconds"] * factor) // 5 * 5)
    while sum(i["seconds"] for i in items) > budget:
        longest = max(items, key=lambda i: i["seconds"])
        if longest["seconds"] <= MIN_SECONDS:
            break
        longest["seconds"] -= 5


def draft(design_dir: Path, sa_refs: Path, minutes: int) -> str:
    """YAML text of a draft deck.yaml for the design: structure, blocks and seconds; messages and notes empty."""
    status = {s["key"]: s["status"] for s in checks.load_state(design_dir).get("steps", [])}
    done = {k for k, v in status.items() if v == "done"}
    data = {p.name: yaml.safe_load(p.read_text()) for p in design_dir.glob("*.yaml")}
    options = config.effective(design_dir, sa_refs).options
    brief = data.get("brief.yaml") or {}
    system = brief.get("system", {}).get("name", "Solution design")
    sections = _sections(design_dir, done, data, options)
    cover = {"notes": "", "seconds": WEIGHTS["cover"]}
    _fit(cover, [s for sec in sections for s in sec["slides"]], minutes * 60)
    deck = {"meta": {"title": system, "subtitle": "Architecture design", "presenter": "", "date": "",
                     "minutes": minutes},
            "cover": cover, "sections": sections}
    return HEADER + yaml.safe_dump(deck, sort_keys=False, allow_unicode=True, width=120)
