# Plan: SA diagrams (/sa-diagrams)

Epic: sad-qwi
Spec: `docs/changes/sad-qwi-sa-diagrams/` (proposal.md, spec-delta.md, design.md, tests.md); ADR `docs/adr/0002-hybrid-diagram-layout.md`

## Objective

A third skill, `/sa-diagrams`, with a CLI `skills/sa-diagrams/scripts/diagrams.py` that turns a valid design folder into editable draw.io diagrams and Mermaid twins for steps 02-10, in one shared style, with a shared architecture skeleton, incremental redraws and optional PNG export; plus rule DG-01 in `/sa-review` and generated diagrams for the example design sets. Done when every REQ in spec-delta.md has a passing test or a recorded manual check, `pytest` and `ruff check .` pass, and the examples' diagrams are up to date.

## Model Guidance
- `default_model_class`: `standard_impl`
- `phase_guidance`:
  - `brainstorm`: `high_reasoning`
  - `design`: `high_reasoning`
  - `plan`: `standard_impl`
  - `implement`: `standard_impl`
  - `verify`: `standard_impl`
  - `review`: `high_reasoning`
  - `docs`: `cheap_simple`
- `override_rule`: Use `high_reasoning` for planning only when execution boundaries, dependency sequencing, or major tradeoffs are still unresolved.

## Requirement Analysis
- Problem statement: reviewers understand an architecture through diagrams; drawing them by hand is slow, drifts from the design data and breaks the review rules the design follows.
- Success criteria (copied from proposal.md):
  - `/sa-diagrams` generates the diagrams of steps 02-10 for `examples/clinic-booking` and of steps 02-05 for `examples/food-delivery/design` and `design-detailed`; they are committed with the examples.
  - The `detailed` food-delivery set shows external systems on the context map and entities inside the aggregates; the `high-level` set shows neither.
  - The high-level and physical views of clinic-booking use the same groups in the same order and the same service grid.
  - Every generated draw.io file is valid and every ID of the source data appears on its diagram.
  - `pytest` and `ruff check .` pass, and the plugin still names no real client, course, organisation or past project.
- Global Constraints (copied from the spec):
  - REQ-DIAGRAMS-001: the CLI writes only into `DESIGN_DIR/diagrams/` and modifies no other file of the design folder.
  - REQ-DIAGRAMS-002: no diagram is drawn from data with error findings.
  - REQ-DIAGRAMS-010: Node and elkjs are needed only when a graph diagram (steps 04, 05, 06) is drawn.
  - REQ-QUALITY-005 (existing): no real client, course, organisation or past project names in `skills/` or `examples/`.
  - Python 3.10+ with PyYAML and jsonschema; Node 18+ with elkjs for graph layout; draw.io desktop only for `--png`.
- Non-goals (copied from proposal.md):
  - Slide decks, speaker notes, HTML or PPTX output; that is sub-project 2b.
  - Diagrams for step 01 (brief), step 11 (stack) and step 12 (ADRs), which are tables, not diagrams.
  - Editing design data from a diagram (diagrams are output only).
  - Image formats other than PNG, and themes other than the one shared style.
  - Cloud icon sets other than AWS for the physical view.

## Approach Options
### Option 1: Hybrid layout by diagram kind (selected, ADR 0002)
- Summary: elkjs for graphs; bands and grids in Python; one shared architecture skeleton; a sequence renderer.
- Pros: each kind reads best; architecture views aligned at any size.
- Cons: three layout techniques to maintain.

### Option 2: elkjs for everything
- Summary: one engine including nested groups.
- Pros: less code.
- Cons: no aligned architecture skeleton; bands become arbitrary boxes.

### Recommended Approach
- Selected option: Option 1.
- Reasoning: confirmed in discuss; keeps the alignment the review rules require.

## Scope
- In scope: drawing model, style, legend, draw.io and Mermaid writers, source-hash stamps, bands/skeleton/sequence layouts, elkjs bridge and Node tool, builders for steps 02-10, CLI with checks-first, step selection, incremental runs, consolidated file and PNG export, SKILL.md, rule DG-01, example diagrams, README section.
- Out of scope: everything under Non-goals.

## Execution Strategy

```yaml
execution_strategy:
  mode: direct
  workers:
    mode: sequential
  rationale: Single provider mode; all tracks share one drawing model and style, so one agent working track by track avoids interface drift.
```

## Shared definitions

### Files

```
skills/sa-diagrams/SKILL.md
skills/sa-diagrams/scripts/diagrams.py
skills/sa-diagrams/scripts/sadiagram/__init__.py
skills/sa-diagrams/scripts/sadiagram/model.py
skills/sa-diagrams/scripts/sadiagram/style.py
skills/sa-diagrams/scripts/sadiagram/legend.py
skills/sa-diagrams/scripts/sadiagram/stamp.py
skills/sa-diagrams/scripts/sadiagram/drawio.py
skills/sa-diagrams/scripts/sadiagram/mermaid.py
skills/sa-diagrams/scripts/sadiagram/geometry.py
skills/sa-diagrams/scripts/sadiagram/layouts/__init__.py
skills/sa-diagrams/scripts/sadiagram/layouts/bands.py
skills/sa-diagrams/scripts/sadiagram/layouts/skeleton.py
skills/sa-diagrams/scripts/sadiagram/layouts/sequence.py
skills/sa-diagrams/scripts/sadiagram/elk.py
skills/sa-diagrams/scripts/sadiagram/builders/__init__.py      # BUILDERS registry
skills/sa-diagrams/scripts/sadiagram/builders/functions.py     # step 02
skills/sa-diagrams/scripts/sadiagram/builders/subdomains.py    # step 03
skills/sa-diagrams/scripts/sadiagram/builders/context_map.py   # step 04
skills/sa-diagrams/scripts/sadiagram/builders/aggregates.py    # step 05
skills/sa-diagrams/scripts/sadiagram/builders/use_cases.py     # step 06
skills/sa-diagrams/scripts/sadiagram/builders/logical.py       # step 07
skills/sa-diagrams/scripts/sadiagram/builders/saga.py          # step 08
skills/sa-diagrams/scripts/sadiagram/builders/patterns.py      # step 09
skills/sa-diagrams/scripts/sadiagram/builders/architecture.py  # step 10
skills/sa-diagrams/scripts/sadiagram/export.py
skills/sa-diagrams/scripts/sadiagram/run.py                    # orchestration used by diagrams.py
skills/sa-diagrams/tools/layout.js
skills/sa-diagrams/tools/package.json
tests/test_diagram_model.py, test_diagram_layouts.py, test_diagram_elk.py, test_diagram_builders.py,
tests/test_diagram_cli.py, tests/test_examples.py (extended), tests/test_checks.py (extended)
```

`pyproject.toml` `pythonpath` gains `skills/sa-diagrams/scripts`. `sadiagram` imports `sacheck` (sa-review) for configuration, data loading and checks; `diagrams.py` adds both script folders to `sys.path`.

### Drawing model (`model.py`, exact)

```python
@dataclass
class Node:
    id: str
    label: str
    kind: str                 # style.NODE_KINDS key
    x: float = 0; y: float = 0; w: float = 160; h: float = 56
    shape: str = "box"        # box | ellipse | hexagon | cylinder | actor | lifeline | note | text
    parent: str | None = None # group id
    icon: str | None = None   # AWS resource icon name, physical view only

@dataclass
class Group:
    id: str
    label: str
    kind: str = "plain"       # style.GROUP_KINDS key
    x: float = 0; y: float = 0; w: float = 0; h: float = 0
    parent: str | None = None

@dataclass
class Edge:
    id: str
    source: str
    target: str
    kind: str                 # style.EDGE_KINDS key
    label: str = ""
    points: list[tuple[float, float]] = field(default_factory=list)
    source_label: str = ""    # e.g. "U"
    target_label: str = ""    # e.g. "D"

@dataclass
class Page:
    name: str
    title: str
    nodes: list[Node]; groups: list[Group]; edges: list[Edge]
    notes: list[str] = field(default_factory=list)
    width: float = 0; height: float = 0

@dataclass
class DiagramSet:
    number: int; key: str; pages: list[Page]; source_hash: str
```

### Style (`style.py`, exact keys)

- `NODE_KINDS`: `core`, `supporting`, `generic`, `scheduled` (supporting fill, black 3px outline), `bff-route`, `gateway`, `identity-provider`, `broker`, `datastore`, `client`, `external`, `actor`, `aggregate-root`, `entity`, `value-object`, `event`, `note`, `step`.
- `EDGE_KINDS`: `sync`, `async`, `auth`, `data`, `external`, `reference`, `compensate`, `use`, `include`.
- `GROUP_KINDS`: `plain`, `band-core`, `band-supporting`, `band-generic`, `layer`, `aggregate`, `region`, `vpc`, `zone`, `subnet-public`, `subnet-app`, `subnet-data`.
- Fills: core `#dae8fc`, supporting `#d5e8d4`, generic `#e1d5e7`, identity-provider `#f8cecc`, managed (gateway, broker, datastore) `#ffe6cc`, external/client `#f5f5f5`.
- Arrow colours: sync `#1A73E8`, async `#E8A400` dashed, auth `#7B1FA2`, data `#00897B`, external `#7F7F7F` dashed, reference `#333333` dashed open arrow, compensate `#D32F2F` dashed, use `#333333` open, include `#333333` dashed open.
- `node_style(kind, shape) -> str`, `edge_style(kind) -> str`, `group_style(kind) -> str` return draw.io style strings.

### Stamps (`stamp.py`)

- `source_hash(design_dir: Path, inputs: list[str]) -> str`: sha256 over the bytes of each listed data file in order plus the effective options JSON of the step's dependencies (so an option change redraws).
- The hash is stored as attribute `sa-source-hash` on the `<mxfile>` element; `read(drawio_file: Path) -> str | None`.

### Inputs per drawn step (used for stamps and DG-01)

| # | key | data files read |
|---|---|---|
| 02 | functions | brief.yaml, functions.yaml |
| 03 | subdomains | subdomains.yaml |
| 04 | context-map | subdomains.yaml, context-map.yaml |
| 05 | aggregates | subdomains.yaml, aggregates.yaml |
| 06 | use-cases | brief.yaml, functions.yaml, use-cases.yaml |
| 07 | logical-view | logical.yaml |
| 08 | saga | subdomains.yaml, logical.yaml, saga.yaml |
| 09 | patterns | logical.yaml, patterns.yaml |
| 10 | architecture | subdomains.yaml, logical.yaml, architecture.yaml |

Option dependencies: 04 `context-map.detail`, 05 `aggregates.detail`, 07 `logical-view.vendors`, 09 `patterns.split`, 10 `architecture.shared-layout`.

### Builder interface (`builders/__init__.py`)

```python
@dataclass(frozen=True)
class BuildContext:
    data: dict[str, Any]          # data file name -> parsed YAML (only valid files)
    options: dict[str, dict[str, Any]]
    vendor_terms: list[str]

Builder = Callable[[BuildContext], list[Page]]
BUILDERS: dict[str, tuple[int, list[str], Builder]]   # key -> (number, inputs, build)
NEEDS_ELK = {"context-map", "aggregates", "use-cases"}
```

### CLI (`diagrams.py`)

```
python3 skills/sa-diagrams/scripts/diagrams.py DESIGN_DIR [--only KEY ...] [--png] [--force]
exit 0 written (or nothing to do); 1 design error findings; 2 usage error or missing Node/elkjs for a needed graph diagram
```
Summary lines: `wrote 04-context-map.drawio (1 page)`, `unchanged 03-subdomains.drawio`, `skipped 06-use-cases (todo)`, `png: 12 exported, 3 cached` or `png: draw.io CLI not found; skipped`.

## Tasks

### Track 1: Drawing model, style, legend, writers and stamps
- **Dependencies**: none
- **Requirements**: REQ-DIAGRAMS-004, REQ-DIAGRAMS-008, REQ-DIAGRAMS-012, REQ-DIAGRAMS-013
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `model.py`, `style.py`, `legend.py`, `stamp.py`, `drawio.py`, `mermaid.py`, `geometry.py`, `sadiagram/__init__.py`; modify `pyproject.toml` (pythonpath); create `tests/test_diagram_model.py`.
- **Interfaces produced**: model classes above; `legend.block(page: Page) -> tuple[list[Node], list[Edge]]` (legend entries only for kinds used on the page, placed below the content); `drawio.render(ds: DiagramSet) -> str`; `drawio.merge(files: list[Path]) -> str` (pages renamed `NN <title>`); `mermaid.render(ds: DiagramSet) -> str`; `geometry.overlaps(page) -> list[tuple[str, str]]`, `geometry.outside_parent(page) -> list[str]`.
- **Steps**:
  1. `test_drawio_is_valid` (REQ-DIAGRAMS-004): a two-page DiagramSet renders to XML that parses, has two `<diagram>` elements, unique cell IDs, and every edge's `source`/`target` is a cell ID. Fail → implement `drawio.render` → pass.
  2. `test_stamp_round_trip` (REQ-DIAGRAMS-012): render with `source_hash="abc"`, write, `stamp.read` returns `"abc"`; `source_hash` changes when one input file or one option changes.
  3. `test_legend_lists_only_used_styles` (REQ-DIAGRAMS-008): page with sync and async edges and core nodes → legend has exactly those three entries.
  4. `test_same_kind_same_style` (REQ-DIAGRAMS-008): every node of kind `core` in the output has the same `fillColor`, and every `async` edge is dashed.
  5. `test_merge_orders_pages` (REQ-DIAGRAMS-004): merging 02 then 03 files gives pages `02 …` then `03 …`.
  6. `test_mermaid_blocks` (REQ-DIAGRAMS-013): a set with two flowchart pages and one sequence page renders three ```` ```mermaid ```` blocks, the third starting with `sequenceDiagram`; every node ID appears in its block.
  7. `test_geometry_checks`: overlapping nodes and a child outside its group are reported.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 2: Python layouts (bands, skeleton, sequence)
- **Dependencies**: Track 1
- **Requirements**: REQ-DIAGRAMS-007, REQ-DIAGRAMS-009
- **Provider role**: `backend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**: create `layouts/bands.py`, `layouts/skeleton.py`, `layouts/sequence.py`; create `tests/test_diagram_layouts.py`.
- **Interfaces produced**:
  - `bands.layout(page: Page, bands: list[tuple[Group, list[Node]]], columns: int, direction: str = "rows") -> None`: places each band as a full-width row (or column), its nodes in a grid of `columns`, bands of equal width, and sets page size.
  - `skeleton.compute(services: int, data_stores: int, externals: int, managed_groups: list[str], columns: int = 4) -> Skeleton` with `Skeleton.boxes: dict[str, tuple[x, y, w, h]]` for groups `clients`, `edge`, `backend`, `microservices`, `data`, `managed`, `platform`, `external`, and `Skeleton.service_slot(i) -> (x, y, w, h)` in row-major order; the same Skeleton instance is used for the high-level and the physical view.
  - `sequence.layout(page: Page, participants: list[Node], messages: list[Edge]) -> None`: lifelines left to right, messages top to bottom 50 px apart, self-messages as loops, `compensate` messages on a red band.
- **Steps**:
  1. `test_bands_equal_width_no_overlap` (REQ-DIAGRAMS-009): three bands with 10, 6 and 5 nodes → equal band widths, no overlaps, all nodes inside their band.
  2. `test_skeleton_same_for_both_views` (REQ-DIAGRAMS-007): for 3, 8 and 15 services, two calls with the same counts give identical boxes and slots; slots never overlap; the microservices box contains every slot.
  3. `test_skeleton_grows_with_services` (REQ-DIAGRAMS-007): 15 services make the microservices box taller than 3, and the data, managed and platform rows move down by the same amount.
  4. `test_sequence_order` (REQ-DIAGRAMS-009): messages are placed at increasing y in list order; each message starts and ends on its participants' lifelines; a self-message is a loop on one lifeline.
  5. `test_split_large_page` (REQ-DIAGRAMS-009): `bands.split(page, max_nodes=40)` splits a 50-node page into pages by band.
- **Acceptance criteria**: tests pass without Node; ruff clean.

### Track 3: elkjs bridge and Node tool
- **Dependencies**: Track 1
- **Requirements**: REQ-DIAGRAMS-010, REQ-DIAGRAMS-009
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `skills/sa-diagrams/tools/package.json` (`{"name": "sa-diagrams-tools", "private": true, "dependencies": {"elkjs": "^0.9.3"}}`), `tools/layout.js` (reads ELK JSON from argv[2], writes the laid-out graph to argv[3], exit 1 with the error on failure), `sadiagram/elk.py`; add `skills/sa-diagrams/tools/node_modules/` to `.gitignore`; create `tests/test_diagram_elk.py`.
- **Interfaces produced**: `elk.available(tools_dir: Path) -> str | None` (None when ready, else the install hint `npm install --prefix <tools_dir>`); `elk.layout(page: Page, direction: str = "RIGHT", tools_dir: Path) -> None` (nested groups via `elk.hierarchyHandling=INCLUDE_CHILDREN`, orthogonal routing, edge label sizes, writes node/group geometry and edge points back).
- **Steps**:
  1. `test_available_reports_missing` (REQ-DIAGRAMS-010): with a tools dir without `node_modules`, `available` returns a hint containing `npm install`; with `PATH` cleared, the hint names Node.
  2. `test_layout_no_overlap` (REQ-DIAGRAMS-009, skipped when `available` is not None): a page of 8 nodes in 2 groups and 10 edges lays out with no overlaps, children inside groups, and every edge with at least two points.
  3. Run `npm install --prefix skills/sa-diagrams/tools` locally for the tests.
- **Acceptance criteria**: tests pass (elk layout test runs locally); ruff clean.

### Track 4: Band builders (steps 02, 03, 07, 09)
- **Dependencies**: Track 2
- **Requirements**: REQ-DIAGRAMS-005, REQ-DIAGRAMS-006, REQ-DIAGRAMS-008
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `builders/__init__.py` (BuildContext, BUILDERS, NEEDS_ELK), `builders/functions.py`, `subdomains.py`, `logical.py`, `patterns.py`; create `tests/test_diagram_builders.py`.
- **Content**:
  - 02: one band per function group (label = group name and its actors), one box per function of kind `step`; the fill follows the band order: first band `#dae8fc`, second `#d5e8d4`, third `#e1d5e7`, then repeating; the legend names each band's colour after its group.
  - 03: three bands (core, supporting, generic) inside one domain group; one ellipse per subdomain service labelled `Subdomain: <name>` above `<service name>`; scheduling-like subdomains are not special-cased (kind from `type`).
  - 07: one band per layer in layer order; component kind from `kind` (`service` -> subdomain type colour via `service_id`); flows as edges with their labels; under `vendors = none` the builder asserts no vendor term in any label (defensive: data already checked).
  - 09: one page per pattern (security, observability, resilience) under `split = one-per-pattern`, else one page with three bands; nodes = distinct `from`/`to` ids in step order, edges numbered `S1`, `O1`, `R1`…
- **Steps**:
  1. `test_functions_complete` (REQ-DIAGRAMS-005): clinic-booking functions → every function id is a node, one band per group.
  2. `test_subdomains_bands` (REQ-DIAGRAMS-005): every subdomain id appears in the band of its type.
  3. `test_logical_complete_and_neutral` (REQ-DIAGRAMS-005, REQ-DIAGRAMS-006): every component and flow appears; no vendor term in labels under `vendors = none`.
  4. `test_patterns_pages` (REQ-DIAGRAMS-005): three pages under `one-per-pattern`, one under `combined`; every step is a numbered edge.
  5. `test_band_pages_readable` (REQ-DIAGRAMS-009): no overlaps on any generated page.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 5: Graph builders (steps 04, 05, 06)
- **Dependencies**: Track 3, Track 4
- **Requirements**: REQ-DIAGRAMS-005, REQ-DIAGRAMS-006, REQ-DIAGRAMS-009
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `builders/context_map.py`, `aggregates.py`, `use_cases.py`; extend `tests/test_diagram_builders.py`.
- **Content**:
  - 04: one node per context (kind from subdomain type); one edge per relationship upstream -> downstream, kind `async` for `domain-events`, else `sync`, label = pattern name unless `detail = ud-only` (label = relationship label), `source_label="U"`, `target_label="D"`; under `with-externals` an `External systems` group with one node per external and an `external` edge from each external to the most connected context that its direction implies (outbound: context -> external, labelled `ACL`).
  - 05: one group per aggregate (kind `aggregate`) with its root node; under `full` the entities, value objects and events as nodes inside the group; one `reference` edge per reference labelled `<via>  <multiplicity>`; `no_aggregate` subdomains as a note.
  - 06: one page per actor group derived from functions groups (use cases whose actors include a group actor); actor nodes (`shape="actor"`), use-case ellipses inside a system boundary group, `use` edges actor -> use case, `include` edges for includes/extends, external-system actors as boxes; split when a page exceeds 40 nodes.
- **Steps** (elk-dependent tests skip when Node is missing):
  1. `test_context_map_ud` (REQ-DIAGRAMS-005): clinic-booking → 8 edges, each with `U`/`D` labels, direction upstream -> downstream.
  2. `test_context_map_externals_only_when_configured` (REQ-DIAGRAMS-006): no external nodes under `ud-only`; food-delivery detailed → 2 external nodes.
  3. `test_aggregates_detail` (REQ-DIAGRAMS-006): roots only under `roots-only`; entities inside their aggregate group under `full`.
  4. `test_use_cases_pages` (REQ-DIAGRAMS-005, REQ-DIAGRAMS-009): clinic-booking → 3 pages; every use case appears at least once; no overlaps.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 6: Saga and architecture builders (steps 08, 10)
- **Dependencies**: Track 2, Track 4
- **Requirements**: REQ-DIAGRAMS-005, REQ-DIAGRAMS-007
- **Provider role**: `backend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**: create `builders/saga.py`, `builders/architecture.py`; extend `tests/test_diagram_builders.py`.
- **Content**:
  - 08: one page per scenario; participants in `participants` order (orchestrator first), steps as numbered messages (`n. message`), kind `sync`/`async`/`compensate`, `self` as a loop; page notes: "Numbers give the order. Red messages are compensations."
  - 10: two pages, `High-level architecture` and `Physical view and network`, both from one `skeleton.compute(...)` call: clients from logical `client` components, edge column (gateway, identity provider), services in the microservices box in `subdomains.yaml` order (hexagon, fill by type), data stores, managed services from `mapping` grouped by kind, externals; the physical page adds region, VPC, two zones and subnet tiers from `physical.tiers` around the same boxes, AWS icons from the mapping's service names when `cloud = aws`, and the security rules as notes; under `shared-layout = false` each page computes its own skeleton.
- **Steps**:
  1. `test_saga_pages` (REQ-DIAGRAMS-005): clinic-booking → 3 pages; page 1 has 11 messages numbered 1..11; compensations are kind `compensate`.
  2. `test_architecture_complete` (REQ-DIAGRAMS-005): every service, data store, external and tier appears on the right page.
  3. `test_architecture_shared_skeleton` (REQ-DIAGRAMS-007): group boxes and service positions identical on both pages for clinic-booking and for generated designs with 3 and 15 services.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 7: CLI, orchestration, PNG export and skill
- **Dependencies**: Track 5, Track 6
- **Requirements**: REQ-DIAGRAMS-001, REQ-DIAGRAMS-002, REQ-DIAGRAMS-003, REQ-DIAGRAMS-004, REQ-DIAGRAMS-010, REQ-DIAGRAMS-011, REQ-DIAGRAMS-012
- **Provider role**: `backend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**: create `run.py`, `export.py`, `scripts/diagrams.py`, `skills/sa-diagrams/SKILL.md`; create `tests/test_diagram_cli.py`; extend `tests/test_plugin.py` (three skills).
- **Interfaces produced**: `run.run(design_dir, refs, only, png, force, tools_dir, drawio_cmd) -> RunResult(written, unchanged, skipped, png_exported, png_cached, warnings, exit_code)`; `export.find_drawio() -> str | None` (`DRAWIO` env var, then `/Applications/draw.io.app/Contents/MacOS/draw.io`, then `drawio` / `draw.io` on PATH); `export.png(page_xml: str, out: Path, cmd: str, cache_dir: Path) -> bool` (timeout 120 s, 2 retries, cache key = sha256 of page XML).
- **SKILL.md sections**: `## Before drawing` (needs a design from `/sa-design`; Node + elkjs install hint; draw.io optional), `## Draw` (`diagrams.py <design> [--only] [--png]`), `## Read the result` (summary, what each file is, open `all-diagrams.drawio`), `## Never` (never edit design data; never draw from data with errors).
- **Steps**:
  1. `test_writes_only_diagrams` (REQ-DIAGRAMS-001): run on a copy of clinic-booking; files outside `design/diagrams/` unchanged (sha256 before/after).
  2. `test_errors_stop_drawing` (REQ-DIAGRAMS-002): broken saga reference → exit 1, no `diagrams/` folder, output names `saga`.
  3. `test_partial_design` (REQ-DIAGRAMS-003): food-delivery → 02-05 written, 06-10 listed as skipped.
  4. `test_consolidated_file` (REQ-DIAGRAMS-004): `all-diagrams.drawio` pages are in step order.
  5. `test_incremental` (REQ-DIAGRAMS-012): second run → all `unchanged`; edit `context-map.yaml` → only 04 rewritten; `--force` rewrites all.
  6. `test_node_missing` (REQ-DIAGRAMS-010): with `PATH` lacking node → exit 2 with `npm install`; `--only functions subdomains` → exit 0.
  7. `test_png_without_drawio` (REQ-DIAGRAMS-011): `DRAWIO=/nonexistent` and `--png` → files written, warning, exit 0.
  8. `test_png_cache` (REQ-DIAGRAMS-011, skipped without draw.io): two runs; the second reports all pages cached.
- **Acceptance criteria**: tests pass; ruff clean; `claude plugin validate .` passes.

### Track 8: Rule DG-01 in /sa-review
- **Dependencies**: Track 1
- **Requirements**: REQ-REVIEW-007
- **Provider role**: `backend`
- **Reasoning**: `low`
- **Model class**: `cheap_simple`
- **Estimated complexity**: low
- **Files**: modify `skills/sa-design/references/rules.yaml` (add `{id: DG-01, step: all, severity: warn, condition: null, check: script, statement: "Every diagram in design/diagrams is up to date with its data"}`); modify `skills/sa-review/scripts/sacheck/checks.py` (`rule_dg_01`: for each `design/diagrams/NN-<key>.drawio`, compare `stamp.read` with the current source hash computed from the inputs table; `sacheck` reads the stamp attribute directly with ElementTree and computes the hash with the same function, imported from `sadiagram.stamp` when available, else a local copy kept identical by a test); update `tests/test_catalog.py` expected IDs; add DG-01 negative and positive cases to `tests/test_checks.py`.
- **Steps**:
  1. `test_dg01_out_of_date` (REQ-REVIEW-007): fixture with a drawn diagram, then edit `subdomains.yaml` → one DG-01 warning on `03-subdomains.drawio`; untouched → none; no `diagrams/` folder → none.
  2. `test_hash_functions_identical`: sacheck's hash equals sadiagram's for the same inputs.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 9: Example diagrams, README and manual checks
- **Dependencies**: Track 7, Track 8
- **Requirements**: REQ-QUALITY-006, REQ-DIAGRAMS-006, REQ-DIAGRAMS-007
- **Provider role**: `general`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: generate `examples/clinic-booking/design/diagrams/`, `examples/food-delivery/design/diagrams/`, `examples/food-delivery/design-detailed/diagrams/` (draw.io, Mermaid, and PNG when draw.io is available); extend `tests/test_examples.py`; modify `README.md` (section "Draw the diagrams" with install of Node + elkjs and usage); record TC-01..TC-04 in `tests.md`.
- **Steps**:
  1. `test_example_diagrams_up_to_date` (REQ-QUALITY-006): every diagram's stamp equals its current source hash; clinic-booking has steps 02-10, food-delivery sets 02-05.
  2. `test_examples_still_neutral` (REQ-QUALITY-005): the existing neutral-content test covers `examples/**/diagrams`.
  3. Run `/sa-diagrams` (`diagrams.py ... --png`) on the three sets; open them in draw.io; record TC-01..TC-04.
- **Acceptance criteria**: tests pass; manual checks recorded; README updated.

## Requirement coverage

| REQ | Track |
|---|---|
| REQ-DIAGRAMS-001, 002, 003 | 7 |
| REQ-DIAGRAMS-004 | 1, 7 |
| REQ-DIAGRAMS-005 | 4, 5, 6 |
| REQ-DIAGRAMS-006 | 4, 5, 9 |
| REQ-DIAGRAMS-007 | 2, 6, 9 |
| REQ-DIAGRAMS-008 | 1, 4 |
| REQ-DIAGRAMS-009 | 2, 3, 4, 5 |
| REQ-DIAGRAMS-010 | 3, 7 |
| REQ-DIAGRAMS-011 | 7 |
| REQ-DIAGRAMS-012 | 1, 7 |
| REQ-DIAGRAMS-013 | 1 |
| REQ-REVIEW-007 | 8 |
| REQ-QUALITY-006 | 9 |

## Integration
- **Branch**: `feat/sa-diagrams`, created from `spec/sa-diagrams`.
- **Merge strategy**: sequential. Order: 1 → 2 → 3 → 8 → 4 → 5 → 6 → 7 → 9.
- Track beads close when their tests pass and the self-check review is done; the Parent Bead `sad-qwi` stays open until the user confirms the merge.

## Validation
- [ ] `pytest` passes
- [ ] `ruff check .` clean
- [ ] `diagrams.py` exits 0 on the three example sets and the second run reports every diagram unchanged
- [ ] `check.py` reports no DG-01 warning on the examples
- [ ] `gin-workflow specs lint --change sad-qwi` and `specs trace --change sad-qwi` clean
- [ ] Manual checks TC-01..TC-04 recorded

## Notes
- Model guidance is planning metadata, not Beads state.
- Provider roles are portable (`backend`, `general`); concrete models resolve from local configuration at orchestration.
- Every new test names its REQ-ID in the test name or a comment.
