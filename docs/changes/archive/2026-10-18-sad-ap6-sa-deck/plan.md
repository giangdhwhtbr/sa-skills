# Plan: SA deck (/sa-deck)

Epic: sad-ap6
Spec: `docs/changes/sad-ap6-sa-deck/` (proposal.md, spec-delta.md, design.md, tests.md); ADR `docs/adr/0003-one-deck-source-two-renderers.md`

## Objective

A fourth skill, `/sa-deck`. Claude drafts `design/deck/deck.yaml` from a proposed 4+1 outline, and a CLI `skills/sa-deck/scripts/deck.py` checks it and renders `deck.html` (self-contained, printable to PDF) and `deck.pptx` (editable, with speaker notes) from that one source. It also adds rule DK-01 to `/sa-review` and an example deck for clinic-booking.

Done when:
- every REQ in spec-delta.md has a passing test or a recorded manual check;
- `pytest` and `ruff check .` pass;
- the example deck is up to date.

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
- Problem statement: turning a finished design into a timed talk is slow manual work; PowerPoint and browser versions drift apart and slide facts drift from the data.
- Success criteria (copied from proposal.md):
  - `/sa-deck` produces a 20-minute deck for `examples/clinic-booking`, committed with the example:
    - `deck.html` presents with keyboard navigation and a notes panel, and prints one slide per PDF page;
    - `deck.pptx` opens in PowerPoint or Keynote with the same slides, titles and speaker notes.
  - For `examples/food-delivery` (steps 01-05 only), the proposed outline contains only slides for those steps.
  - A deck whose times exceed the budget gets a warning; a slide stating a different service count than `subdomains.yaml` is an error.
  - `pytest` and `ruff check .` pass, and the plugin still names no real client, course, organisation or past project.
- Global Constraints (copied from the spec):
  - REQ-DECK-001: the CLI writes only into `DESIGN_DIR/deck/` and never modifies `deck.yaml`.
  - REQ-DECK-007: no deck is rendered from a `deck.yaml` with error findings.
  - REQ-DECK-009: without Node or pptxgenjs the HTML deck is still written.
  - REQ-QUALITY-005 (existing): no real client, course, organisation or past project names in `skills/` or `examples/`.
  - Python 3.10+ with PyYAML and jsonschema; Node 18+ with pptxgenjs 3.12.0 for PPTX; draw.io desktop only to export diagram PNGs not already cached.
- Non-goals (copied from proposal.md): corporate PPTX templates; animations and transitions; languages other than English; topic-specific slides beyond the generic outline; live or zoomable diagrams in HTML; editing design data from the deck.

## Approach Options
### Option 1: One source, two renderers (selected, ADR 0003)
- Summary: `deck.yaml` → schema-checked render model → Python HTML renderer and Node pptxgenjs renderer from the same JSON.
- Pros: no scraping, checkable content, editable PPTX.
- Cons: layout implemented twice; guarded by a parity test.
### Option 2: HTML as source, PPTX extracted from it
- Cons: regex parsing of HTML; no checkable source.
### Option 3: python-pptx for PPTX
- Cons: new pip dependency and a rewrite of the proven pptxgenjs layout.
### Recommended Approach
- Selected option: Option 1 (confirmed in discuss).

## Scope
- In scope: render model, deck schema and default theme, outline, checks, slide images and legend chips, HTML renderer, PPTX renderer, CLI with incremental rebuild, SKILL.md, rule DK-01, example deck, README section, plugin spec update to four skills.
- Out of scope: everything under Non-goals.

## Execution Strategy

```yaml
execution_strategy:
  mode: direct
  workers:
    mode: sequential
  rationale: Single provider mode; tracks share one render model and layout grid, so one agent working track by track avoids interface drift.
```

## Shared definitions

### Files

```
skills/sa-deck/SKILL.md
skills/sa-deck/scripts/deck.py
skills/sa-deck/scripts/sadeck/__init__.py
skills/sa-deck/scripts/sadeck/model.py
skills/sa-deck/scripts/sadeck/schema.py
skills/sa-deck/scripts/sadeck/stamp.py
skills/sa-deck/scripts/sadeck/outline.py
skills/sa-deck/scripts/sadeck/checks.py
skills/sa-deck/scripts/sadeck/assets.py
skills/sa-deck/scripts/sadeck/html.py
skills/sa-deck/scripts/sadeck/pptx.py
skills/sa-deck/scripts/sadeck/run.py
skills/sa-deck/tools/package.json            # {"name": "sa-deck-tools", "private": true, "dependencies": {"pptxgenjs": "3.12.0"}}
skills/sa-deck/tools/pptx.js
skills/sa-deck/references/deck.schema.yaml
skills/sa-deck/references/theme.yaml
skills/sa-deck/references/outline.md
tests/test_deck_model.py, test_deck_outline.py, test_deck_checks.py, test_deck_assets.py,
tests/test_deck_html.py, test_deck_pptx.py, test_deck_cli.py, tests/test_checks.py (extended),
tests/test_examples.py (extended), tests/test_plugin.py (extended)
```

`pyproject.toml` `pythonpath` gains `skills/sa-deck/scripts`. `sadeck` imports `sacheck` (config, data, `NUMBER_WORDS`/`_COUNT`) and `sadiagram` (`drawio.page_xml`, `export`, `stamp.DRAWN`); `deck.py` adds the three script folders to `sys.path`. `.gitignore` gains `skills/sa-deck/tools/node_modules/` and `skills/sa-deck/tools/package-lock.json`.

### deck.yaml (shape validated by `deck.schema.yaml`)

```yaml
meta:
  title: Clinic booking platform        # required
  subtitle: Architecture design         # optional
  presenter: Jane Doe                   # optional
  date: 2026-10-16                      # optional, string
  minutes: 20                           # required, 1..120
theme:                                  # optional; omitted keys come from references/theme.yaml
  primary: "#1F3A68"
  accent: "#C2185B"
  text: "#222222"
  muted: "#5A6478"
  font: "Calibri"
  logo: logo.png                        # file inside design/deck/
  footer: "Architecture review"
cover: {notes: "...", seconds: 20}      # required
sections:                               # required, at least one
  - title: Domain design
    slides:
      - title: Context map               # required
        message: Eight contexts ...      # required (key message, one line, <= 140 chars)
        block: {type: diagram, step: context-map, page: 1}   # optional (title-only slide when omitted)
        notes: "Spoken script ..."       # required, non-empty
        seconds: 75                      # required, 5..600
```

Block types (`type` plus fields): `bullets {items: [str] 1..6}`; `table {header: [str] 1..5, rows: [[str]] 1..8, widths?: [number]}`; `diagram {step, page}`; `diagrams {left: {step, page}, right: {step, page}}`; `diagram-text {step, page, items: [str] 2..4}`; `agenda {}`; `image {file}`. `**text**` marks a bold run in any text field.

### Render model (`model.py`, exact)

```python
@dataclass(frozen=True)
class DiagramRef:
    step: str          # sadiagram.stamp.DRAWN key
    page: int          # 1-based

@dataclass
class Block:
    kind: str                                  # bullets | table | diagram | diagrams | diagram-text | agenda | image
    items: list[str] = field(default_factory=list)
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    widths: list[float] = field(default_factory=list)
    diagrams: list[DiagramRef] = field(default_factory=list)
    file: str | None = None

@dataclass
class Slide:
    number: int        # 1-based, cover is 1
    kind: str          # cover | content
    section: str
    title: str
    message: str
    block: Block | None
    notes: str
    seconds: int

@dataclass
class Theme:
    primary: str; accent: str; text: str; muted: str; font: str
    logo: str | None = None; footer: str = ""

@dataclass
class Deck:
    title: str; subtitle: str; presenter: str; date: str; minutes: int
    theme: Theme
    slides: list[Slide]               # cover first, then every section's slides in order
    sections: list[str]               # section titles in order (for the agenda)
```

Default theme (`references/theme.yaml`): primary `#1F3A68`, accent `#C2185B`, text `#222222`, muted `#5A6478`, font `Calibri`, no logo, empty footer.

### Layout grid (both renderers)

| Element | HTML px (1280×720) | PPTX in (13.333×7.5) |
|---|---|---|
| Title | x 34, y 18, w 1180, 32 px, primary, semibold | x 0.45, y 0.2, w 12.43, h 0.6, 28 pt |
| Message | x 34, y 62, w 1180, 16 px, muted | x 0.45, y 0.8, h 0.35, 15 pt |
| Body | x 34, y 100, w 1212, h 560 | x 0.45, y 1.3, w 12.43, h 5.6 |
| Legend chips | last 26 px of body | last 0.3 in of body, 10 pt |
| Footer / number | bottom 10, 11–12 px, muted | y 7.1, 10 pt |
| Cover | primary background; title 48 px at y 262; subtitle, presenter, date below; logo top centre; accent rule | same positions scaled ×(13.333/1280) |

### Interfaces

```python
# schema.py
class DeckError(ValueError): ...                       # .problems: list[str] ("slide 7: block.page: ...")
def load(design_dir: Path, refs: Path) -> Deck          # raises DeckError; refs = skills/sa-deck/references
# stamp.py
STAMP_FILE = ".deck-stamp.json"
def deck_hash(design_dir: Path) -> str                  # sha256: deck.yaml bytes, logo/image bytes, referenced diagram page XML
def read(design_dir: Path) -> str | None
def write(design_dir: Path, value: str) -> None
# outline.py
def draft(design_dir: Path, sa_refs: Path, minutes: int) -> str     # YAML text of a draft deck.yaml
# checks.py
@dataclass
class Finding: severity: str; slide: int; field: str; message: str  # severity error | warn
def run(deck: Deck, design_dir: Path) -> list[Finding]
# assets.py
@dataclass
class Chip: kind: str; label: str; fill: str; stroke: str; dashed: bool   # kind node | edge
@dataclass
class SlideImage: path: Path | None; width: int; height: int; chips: list[Chip]
def page_pages(design_dir: Path, step: str) -> int                  # number of pages in diagrams/NN-step.drawio (0 if missing)
def slide_image(design_dir: Path, ref: DiagramRef, drawio_cmd: str | None) -> SlideImage
# html.py
def render(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path) -> str
# pptx.py
class PptxError(RuntimeError): ...
def available(tools_dir: Path) -> str | None            # None or the install hint
def to_json(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path) -> dict
def render(deck: Deck, images: dict[DiagramRef, SlideImage], design_dir: Path, out: Path, tools_dir: Path) -> None
# run.py
@dataclass
class RunResult: written: list[str]; unchanged: bool; warnings: list[str]; errors: list[str]; exit_code: int; outline: str
def run(design_dir: Path, refs: Path, sa_refs: Path, outline: bool = False, minutes: int = 20, force: bool = False,
        tools_dir: Path | None = None, drawio_cmd: str | None = None) -> RunResult
```

### CLI (`deck.py`)

```
python3 skills/sa-deck/scripts/deck.py DESIGN_DIR [--outline] [--minutes N] [--force]
exit 0 written / unchanged / outline printed; 1 deck error findings (nothing written); 2 usage, missing deck.yaml, missing package, pptx render failure
```
Summary lines: `wrote deck.html (20 slides, 19:30 of 20:00)`, `wrote deck.pptx`, `unchanged deck`, `warning: slide 7: notes run about 95 s for 60 s`, `warning: pptx skipped: run npm install --prefix …`.

## Tasks

### Track 1: Render model, schema, theme and stamp
- **Dependencies**: none
- **Requirements**: REQ-DECK-003, REQ-DECK-010, REQ-DECK-011
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - create `sadeck/__init__.py`, `model.py`, `schema.py`, `stamp.py`, `references/deck.schema.yaml`, `references/theme.yaml`;
  - modify `pyproject.toml` (pythonpath) and `.gitignore`;
  - create `tests/test_deck_model.py` and the fixture `tests/fixtures/deck/deck.yaml`, a valid 6-slide deck for clinic-booking.
- **Interfaces produced**: model classes, `schema.load`, `DeckError`, `stamp.*` as above.
- **Steps**:
  1. `test_valid_deck_loads` (REQ-DECK-003): the fixture loads. The cover is slide 1 and numbering is contiguous; `sections` lists the titles in order; omitted theme keys equal `theme.yaml`.
  2. `test_schema_rejects` (REQ-DECK-003), parametrised. Each case raises `DeckError` whose problem names `slide N` and the field:
     - unknown block type `chart`;
     - 7 bullets;
     - 9 table rows;
     - `diagram-text` with 1 item;
     - empty notes;
     - `seconds: 0`;
     - missing `meta.minutes`.
  3. `test_custom_theme` (REQ-DECK-010): `theme.primary: "#0B5394"` gives `deck.theme.primary == "#0B5394"`. A logo path that escapes the folder (`../x.png`) is a `DeckError`.
  4. `test_deck_hash` (REQ-DECK-011): the hash is stable for the same inputs. It changes when any of these change: a byte of `deck.yaml`, the logo file, or the XML of a referenced diagram page. It does not change when an unreferenced diagram page changes.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 2: Outline
- **Dependencies**: Track 1
- **Requirements**: REQ-DECK-002
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `sadeck/outline.py`, `references/outline.md` (per default slide: source data, block, what the key message and script should say); create `tests/test_deck_outline.py`.
- **Content**: sections and slides, each included only when its step is `done`:
  - **Introduction:** a "Proposed solution" table (header `Problem`, `Answer`; one row per `brief.pain_points` text, with the answer cell left empty for Claude), then "Main business functions" (`diagram functions 1`).
  - **Domain design:** subdomains, context map, aggregates (one `diagram` each).
  - **Use case view:** one slide per page of `06-use-cases.drawio`. When the file is missing, the page count is the number of function groups that have use cases.
  - **Logical view:** one diagram slide.
  - **Process view:** one slide per saga scenario.
  - **Core patterns:** one slide per pattern page, or a single slide under `combined`.
  - **High-level and physical view:** two `diagram` slides.
  - **Development view:** a "Technology stack" table (`Layer`, `Choice`, `Why`, from `stack.yaml`) and an "Architecture decisions" table (`Decision`, `Alternatives`, `Trade-off`, from `adrs.yaml`, at most 8 rows per slide, continued on the next slide).
  - **Q&A:** a title-only slide.
  - **Agenda:** an `agenda` slide right after the cover.
  - **Weights (seconds):** cover 20, agenda 25, table 75, diagram 70, Q&A 20. When the sum exceeds `minutes × 60`, every slide is scaled down proportionally, rounded to 5 s with a minimum of 15.
  - **Draft text:** messages and notes are `""`; `draft` returns YAML with a header comment telling the author to fill them. An empty note fails the schema, so a draft cannot be rendered unfilled.
- **Steps**:
  1. `test_outline_clinic_full` (REQ-DECK-002): sections in the listed order; use-case slides = 3; saga slides = 3; pattern slides = 3; architecture slides = 2; development view has 2+ slides; the seconds total ≤ 1200 for `--minutes 20`.
  2. `test_outline_partial` (REQ-DECK-002): food-delivery `design` → section titles are exactly cover, Agenda, Introduction, Domain design, Q&A, and the seconds total ≤ 600 for 10 minutes.
  3. `test_outline_parses`: the draft is valid YAML. After filling every message and note with "x", it loads with `schema.load`.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 3: Deck checks
- **Dependencies**: Track 1
- **Requirements**: REQ-DECK-006, REQ-DECK-007
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `sadeck/checks.py`; create `tests/test_deck_checks.py`.
- **Content**:
  - **Budget:** warn `deck runs MM:SS against a MM:SS budget`.
  - **Script length:** words / (130/60) > seconds × 1.15 → warn `notes run about N s for S s`.
  - **Diagram references:** error when the step is not in `sadiagram.stamp.DRAWN`, the file is missing, or the page is greater than the page count (`_page_count(design_dir, step)` in `checks.py`, which counts `<diagram>` elements; Track 4 moves it to `assets.page_pages`).
  - **Images and logo:** error when the file is missing or outside `design/deck/`.
  - **Stated counts:** error when the `sacheck.checks._COUNT` matches in any title, message, item, cell or note differ from the number of services in `subdomains.yaml`.
- **Steps**:
  1. `test_over_budget_warns` (REQ-DECK-006): 1,320 s against 20 min → one warning that contains `22:00` and `20:00`, and no errors.
  2. `test_long_script_warns` (REQ-DECK-006): 300 words for 60 s → a warning on that slide; 100 words → none.
  3. `test_unknown_diagram_page` (REQ-DECK-007): `context-map` page 2 → an error naming the slide; step `brief` → an error.
  4. `test_wrong_service_count` (REQ-DECK-007): the message "Twelve services, one per subdomain" with 8 services → an error naming the slide; "8 services" → none.
  5. `test_image_outside_deck` (REQ-DECK-007): `file: ../brief.yaml` → an error.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 4: Slide images and legend chips
- **Dependencies**: Track 1
- **Requirements**: REQ-DECK-005
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - create `sadeck/assets.py`;
  - modify `skills/sa-diagrams/scripts/sadiagram/export.py`: `png(..., scale: float = 1)` passes `--scale`, and the cache key includes the scale (existing callers unchanged);
  - create `tests/test_deck_assets.py`.
- **Content**:
  - `slide_image` reads `diagrams/NN-step.drawio` and takes page `page`. It removes every cell whose id contains `-legend-` or ends in `-title`, and their children.
  - Chips come from the removed legend cells: `-swatch` gives a node chip (fill and stroke from its style), `-line` gives an edge chip (strokeColor, `dashed`), and `-label` gives the text.
  - The image is exported with `export.png(xml, deck/assets/NN-step-pP.png, cmd, deck/assets, scale=2)`. The size is read from the PNG header.
  - When `cmd` is None and no PNG exists, the result is `SlideImage(None, 0, 0, chips)`.
- **Steps**:
  1. `test_chips_from_legend` (REQ-DECK-005): the clinic-booking context map → chips are exactly `[node Core subdomain, node Supporting subdomain, node Generic subdomain, edge Sync call, edge Async event]`, with the async edge dashed.
  2. `test_stripped_page_has_no_legend` (REQ-DECK-005): the exported XML has no `-legend-` or `-title` cell, and every remaining edge source and target still exists.
  3. `test_placeholder_without_drawio` (REQ-DECK-005): with `cmd=None` and an empty assets folder, `path is None` and the chips are still present.
  4. `test_slide_png` (skipped without draw.io): a real PNG at roughly 2× the page size; a second call hits the cache.
  5. `test_export_scale_keeps_old_callers`: the existing `tests/test_diagram_cli.py` still passes. Run it.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 5: HTML renderer
- **Dependencies**: Track 4
- **Requirements**: REQ-DECK-004, REQ-DECK-008, REQ-DECK-010
- **Provider role**: `frontend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**: create `sadeck/html.py`; create `tests/test_deck_html.py`.
- **Content**:
  - **Structure:** one `<section class="slide" data-n>` per slide, holding the title, the message, the body and `<aside class="notes">`, using the layout grid.
  - **Blocks:**
    - `bullets`: a `<ul>`.
    - `table`: a `<table>`.
    - `diagram`: an `<img>` with a base64 data URI, fitted with `object-fit: contain`, plus the chips row.
    - `diagrams`: two half-width images.
    - `diagram-text`: the image at 62% width with the bullets beside it.
    - `agenda`: numbered circles with the section titles and their slide ranges.
    - `image`: an inlined file.
    - placeholder: a grey box reading "Diagram not exported: run /sa-diagrams --png".
  - **Theme:** CSS variables from the theme.
  - **Presenting:**
    - keyboard: ←/→/Space/PgUp/PgDn/Home/End;
    - `#n` jumps to a slide;
    - N toggles the notes panel;
    - the status bar shows `n / total` and the total time;
    - scale-to-fit on resize.
  - **Print:** `@media print` hides the bar and notes and puts one slide per page at `@page {size: 1280px 720px}`.
  - **Escaping and inlining:** all text is HTML-escaped before `**bold**` becomes `<b>`. Every asset is inlined, so there is no `http` URL.
- **Steps**:
  1. `test_one_section_per_slide` (REQ-DECK-008): section count = slide count; each has notes equal to the slide notes.
  2. `test_self_contained` (REQ-DECK-008): no `http://` or `https://`; every `<img src` starts with `data:image/`.
  3. `test_print_css` (REQ-DECK-008): there is a `@media print` rule with `page-break-after` and `@page`.
  4. `test_blocks_render` (REQ-DECK-004), parametrised over block types: the expected element is present (`<ul>` with N `<li>`, `<table>` with rows + 1 `<tr>`, 2 `<img>` for `diagrams`, chip count equal to the legend entries, the placeholder text when the path is None).
  5. `test_theme_applied` (REQ-DECK-010): `--primary:#0B5394` is in the CSS, and the logo is inlined on the cover.
  6. `test_escaping`: a title `A <b> & C` renders escaped; `**x**` becomes `<b>x</b>`.
- **Acceptance criteria**: tests pass; ruff clean; a manual look at the rendered fixture deck in the browser pane.

### Track 6: PPTX renderer
- **Dependencies**: Track 5
- **Requirements**: REQ-DECK-004, REQ-DECK-009, REQ-DECK-010
- **Provider role**: `frontend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**: create `skills/sa-deck/tools/package.json`, `tools/pptx.js` (reads deck.json, writes .pptx, exits 1 with the error), `sadeck/pptx.py`; create `tests/test_deck_pptx.py`.
- **Content**:
  - **Slide masters:** `pptx.js` defines a COVER master (primary background, accent rule) and a CONTENT master (title and message placeholders, slide number, footer), all on the layout grid.
  - **Blocks:**
    - `bullets`: a text box with bullet paragraphs and bold runs.
    - `table`: `addTable` with a primary-coloured header row and striped rows.
    - diagram blocks: `addImage`, fitted to the box with the aspect ratio kept, plus a chips row of small rectangles or lines with labels.
    - `agenda`: circles and text.
    - `image`: `addImage`.
    - placeholder: a grey rectangle with text.
  - **Notes:** `addNotes` on every slide.
  - **JSON hand-off:** `to_json` emits plain runs, `[[text, bold], ...]`, and absolute image paths.
  - **Availability:** `available` returns the hint `npm install --prefix <tools>` when `node` is missing or `node_modules/pptxgenjs` is absent.
- **Steps**:
  1. `test_available_reports_missing` (REQ-DECK-009): a tools dir without `node_modules` gives a hint containing `npm install`; with `PATH` cleared, the hint names Node.
  2. `test_pptx_structure` (REQ-DECK-009, skipped without pptxgenjs): render the fixture, then open it with `zipfile`. The count of `ppt/slides/slide*.xml` equals the slide count, every title is in its slide XML, and every note is in `ppt/notesSlides/`.
  3. `test_pptx_tables_are_tables` (REQ-DECK-004): a table slide has an `<a:tbl>` with rows + 1 `<a:tr>`.
  4. `test_html_pptx_parity` (REQ-DECK-009): the slide titles and notes from the HTML (parsed) equal those from the PPTX (parsed).
  5. `test_pptx_theme` (REQ-DECK-010): the primary colour `0B5394` appears in the title run properties.
- **Acceptance criteria**: tests pass locally after `npm install --prefix skills/sa-deck/tools`; ruff clean.

### Track 7: CLI, rebuilds and the skill
- **Dependencies**: Track 2, Track 3, Track 6
- **Requirements**: REQ-DECK-001, REQ-DECK-011, REQ-DECK-009, REQ-PLUGIN-001
- **Provider role**: `backend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**:
  - create `sadeck/run.py`, `scripts/deck.py`, `skills/sa-deck/SKILL.md`, `tests/test_deck_cli.py`;
  - modify `tests/test_plugin.py` (four skills, sa-deck sections), `.claude-plugin/plugin.json` (description, version 0.3.0), and `pyproject.toml` (version 0.3.0).
- **SKILL.md sections**:
  - `## Before building`: needs `/sa-design` data and up-to-date diagrams (offer `/sa-diagrams --png`); Node + pptxgenjs install hint.
  - `## Draft the deck`:
    1. ask the talk length, audience and presenter;
    2. run `--outline`;
    3. fill messages, tables and scripts from the design documents;
    4. ask cut and emphasis questions one at a time, with a recommendation;
    5. write `deck/deck.yaml`.
  - `## Render`: run `deck.py`, report the warnings, and fix budget or script warnings by editing `deck.yaml`.
  - `## Never`: never change design data; never invent facts that are not in the design; never hide a check error.
- **Steps**:
  1. `test_writes_only_deck` (REQ-DECK-001): on a copy of clinic-booking with the fixture `deck.yaml`, files outside `deck/` and `deck.yaml` itself are unchanged (sha256 before and after); `deck.html`, `deck.pptx` (when available) and `assets/` exist.
  2. `test_errors_write_nothing` (REQ-DECK-007): a wrong service count → exit 1, no `deck.html`, and the output names the slide.
  3. `test_missing_deck_yaml` → exit 2 with "--outline"; `--outline --minutes 20` → exit 0, and the YAML is printed with nothing written.
  4. `test_unchanged_and_force` (REQ-DECK-011): the second run reports `unchanged deck` and the mtimes are equal; `--force` rewrites; editing `deck.yaml` rewrites.
  5. `test_node_missing_keeps_html` (REQ-DECK-009): with `PATH` lacking node → exit 0, `deck.html` written, no `deck.pptx`, and a warning containing `npm install`.
  6. `test_manifest_names_four_skills` (REQ-PLUGIN-001) and `test_sa_deck_sections`.
- **Acceptance criteria**: tests pass; ruff clean; `claude plugin validate .` passes.

### Track 8: Rule DK-01 in /sa-review
- **Dependencies**: Track 1
- **Requirements**: REQ-REVIEW-008
- **Provider role**: `backend`
- **Reasoning**: `low`
- **Model class**: `cheap_simple`
- **Estimated complexity**: low
- **Files**:
  - modify `skills/sa-design/references/rules.yaml` to add `{id: DK-01, step: all, severity: warn, condition: null, check: script, statement: "The rendered deck is up to date with deck.yaml, its images and the diagram pages it shows"}`;
  - modify `skills/sa-review/scripts/sacheck/checks.py` to add `rule_dk_01`. It runs only when `deck/.deck-stamp.json` exists, and compares the stamp with `deck_hash` computed by a local copy, kept identical by a test;
  - update `tests/test_catalog.py` with the expected IDs;
  - add the cases to `tests/test_checks.py`.
- **Steps**:
  1. `test_dk01_out_of_date` (REQ-REVIEW-008): there is no warning without a stamp. With a matching stamp there is none either. After `deck.yaml` is edited, there is one DK-01 warning on `deck/deck.html`.
  2. `test_deck_hash_identical`: `sacheck`'s copy of the hash equals `sadeck.stamp.deck_hash` on the fixture.
- **Acceptance criteria**: tests pass; ruff clean.

### Track 9: Example deck, README and manual checks
- **Dependencies**: Track 7, Track 8
- **Requirements**: REQ-QUALITY-007, REQ-DECK-002, REQ-DECK-006, REQ-DECK-008, REQ-DECK-009
- **Provider role**: `general`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - author `examples/clinic-booking/design/deck/deck.yaml` (20 minutes, written by following SKILL.md from the outline) and render `deck.html`, `deck.pptx` and `assets/`;
  - extend `tests/test_examples.py`;
  - modify `README.md` with a "Build the deck" section (install, authoring flow, CLI, outputs, checks), troubleshooting rows and the repository layout;
  - record TC-01..TC-04 in `tests.md`.
- **Steps**:
  1. `test_example_deck_up_to_date` (REQ-QUALITY-007): the stamp equals `deck_hash`; `check.py` on the example reports no DK-01 or DG-01.
  2. `test_example_deck_fits` (REQ-DECK-006): the example deck has no budget or script warnings.
  3. `test_examples_still_neutral` (REQ-QUALITY-005): the neutral-content test also scans `.html` (and still skips `node_modules`).
  4. Manual checks:
     - present `deck.html` in the browser pane: keyboard, notes and `#n`;
     - print it to PDF with the draw.io-free method `chrome --headless --print-to-pdf`, or the browser pane print, and count the pages;
     - open `deck.pptx` (Keynote or PowerPoint where available) or convert it to PDF with `soffice` if present;
     - record TC-01..TC-04.
- **Acceptance criteria**: tests pass; manual checks recorded; README updated.

## Requirement coverage

| REQ | Track |
|---|---|
| REQ-DECK-001 | 7 |
| REQ-DECK-002 | 2, 9 |
| REQ-DECK-003 | 1 |
| REQ-DECK-004 | 5, 6 |
| REQ-DECK-005 | 4 |
| REQ-DECK-006 | 3, 9 |
| REQ-DECK-007 | 3, 7 |
| REQ-DECK-008 | 5, 9 |
| REQ-DECK-009 | 6, 7, 9 |
| REQ-DECK-010 | 1, 5, 6 |
| REQ-DECK-011 | 1, 7 |
| REQ-REVIEW-008 | 8 |
| REQ-QUALITY-007 | 9 |
| REQ-PLUGIN-001 (modified) | 7 |

## Integration
- **Branch**: `feat/sa-deck`, created from `spec/sa-deck`.
- **Merge strategy**: sequential. Order: 1 → 2 → 3 → 4 → 8 → 5 → 6 → 7 → 9.
- Track beads close when their tests pass and the self-check review is done; the Parent Bead `sad-ap6` stays open until the user confirms the merge.

## Validation
- [ ] `pytest` passes
- [ ] `ruff check .` clean
- [ ] `deck.py examples/clinic-booking/design` exits 0 and a second run reports `unchanged deck`
- [ ] `check.py` reports no DK-01 or DG-01 warning on the examples
- [ ] `gin-workflow specs lint --change sad-ap6` and `specs trace --change sad-ap6` clean
- [ ] Manual checks TC-01..TC-04 recorded

## Notes
- Model guidance is planning metadata, not Beads state.
- Provider roles are portable (`backend`, `frontend`, `general`); concrete models resolve from local configuration at orchestration.
- Every new test names its REQ-ID in the test name or a comment.
- Track 3 needs the page count before Track 4 exists. It defines `_page_count(design_dir, step)` in `checks.py`; Track 4 moves that helper to `assets.page_pages` and updates the import in the same track.
