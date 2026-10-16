# sa-design-kit

A Claude Code plugin that guides you through a **DDD + microservices solution design**, step by step, and reviews the result.

- **`/sa-design`** walks you through 12 design steps: brief, business functions, subdomains, context map, aggregate roots, use cases, logical view, core flow (saga), core patterns, architecture, technology stack and architecture decisions. Each step proposes content, asks you the key decisions one at a time (always with a recommendation), then writes a Markdown document and a YAML data file into your project's `design/` folder.
- **`/sa-review`** audits the design folder without changing it: completeness, schemas, review rules, cross-step consistency and traceability. It writes `design/review-report.md`.
- **`/sa-diagrams`** draws the design as editable draw.io diagrams with Mermaid twins (and PNGs if you have draw.io desktop), generated from the YAML data so they never drift from it.
- **`/sa-deck`** turns the design into a timed talk: it drafts the slides with you (key messages and speaker scripts within a time budget), then renders a self-contained HTML deck and an editable PowerPoint from one source file.

The level of detail is configurable: one high-level preset for architecture reviews, one detailed preset, or your own mix of options and rule severities.

---

## Requirements

| Need | Version | Why |
|---|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | recent | runs the skills |
| Python | 3.10 or newer | the review checks (`check.py`) |
| `pyyaml`, `jsonschema` | any recent | used by `check.py` and `diagrams.py` |
| Node.js + `elkjs` | Node 18 or newer | `/sa-diagrams` only: layout of the context map, aggregates and use cases |
| draw.io desktop | any recent | `/sa-diagrams --png` and the slide images of `/sa-deck` (optional) |
| Node.js + `pptxgenjs` | Node 18 or newer | `/sa-deck` only: the PowerPoint file (the HTML deck needs nothing) |

Install the Python packages once for the `python3` on your PATH:

```bash
python3 -m pip install --user pyyaml jsonschema
```

---

## Install

The repository is both a plugin and a one-plugin marketplace.

### Option A: install from a local clone

```bash
git clone <repository-url> sa-design-kit
claude plugin marketplace add ./sa-design-kit
claude plugin install sa-design-kit@sa-design-kit-marketplace
```

### Option B: install for one project only

Run these inside the project where you want to use the skills. Nothing changes in your other projects.

```bash
claude plugin marketplace add /path/to/sa-design-kit --scope local
claude plugin install sa-design-kit@sa-design-kit-marketplace --scope local
```

### Check the install

```bash
claude plugin details sa-design-kit@sa-design-kit-marketplace
```

You should see `Skills (4): sa-deck, sa-design, sa-diagrams, sa-review`. Start a new Claude Code session in your project and the commands `/sa-design`, `/sa-review`, `/sa-diagrams` and `/sa-deck` are available.

For `/sa-diagrams` and `/sa-deck`, install the Node packages once (Node.js 18+ required):

```bash
npm install --prefix <plugin>/skills/sa-diagrams/tools
npm install --prefix <plugin>/skills/sa-deck/tools
```

### Update and uninstall

```bash
claude plugin update sa-design-kit@sa-design-kit-marketplace
claude plugin uninstall sa-design-kit@sa-design-kit-marketplace
```

---

## Quick start

1. Put your requirements where Claude can read them (for example `docs/brief.md`).
2. In Claude Code, run:

   ```
   /sa-design
   ```

   The first run asks where to create the design folder (default `design/`) and which preset to use (default `high-level`).
3. Step 01 (brief) reads your requirements, shows a draft, and asks a few questions. Answer them, or accept the recommendation. The step then writes `design/01-brief.md` and `design/brief.yaml`, checks them, and stops.
4. Run `/sa-design` again for the next step. It always resumes where you stopped. To run a specific step, name it:

   ```
   /sa-design run step 4
   /sa-design context map
   ```

5. When the steps you need are done, run:

   ```
   /sa-review
   ```

   and read `design/review-report.md`. Fix findings by re-running the steps it names.
6. Draw the design:

   ```
   /sa-diagrams
   ```

   and open `design/diagrams/all-diagrams.drawio` in draw.io (or diagrams.net).
7. Build the talk:

   ```
   /sa-deck
   ```

   It asks the talk length and audience, drafts every slide with you, and writes `design/deck/deck.html` and `design/deck/deck.pptx`.

---

## The 12 steps

| # | Step | Writes | Reads |
|---|---|---|---|
| 01 | Brief: goals, pain points, actors, NFRs, constraints | `01-brief.md`, `brief.yaml` | your requirements |
| 02 | Main business functions, grouped by actor | `02-functions.md`, `functions.yaml` | brief |
| 03 | Subdomains (core, supporting, generic), one service each | `03-subdomains.md`, `subdomains.yaml` | brief, functions |
| 04 | Context map: upstream / downstream between contexts | `04-context-map.md`, `context-map.yaml` | subdomains |
| 05 | Aggregate roots and the ID references between them | `05-aggregates.md`, `aggregates.yaml` | subdomains, context map |
| 06 | Use cases per actor | `06-use-cases.md`, `use-cases.yaml` | brief, functions |
| 07 | Logical view: layers, no vendor names | `07-logical-view.md`, `logical.yaml` | brief, subdomains, context map |
| 08 | Core flow as a saga, with failure cases | `08-saga.md`, `saga.yaml` | subdomains, aggregates, logical view |
| 09 | Core patterns: security, observability, resilience | `09-patterns.md`, `patterns.yaml` | logical view |
| 10 | Architecture: cloud mapping, high-level and physical views, network | `10-architecture.md`, `architecture.yaml` | logical view, patterns |
| 11 | Technology stack | `11-stack.md`, `stack.yaml` | architecture |
| 12 | Architecture decisions (ADRs) with trade-offs | `12-adrs.md`, `adrs.yaml` | all earlier steps |

Progress lives in `design/design-state.yaml`. If you change an earlier step (for example rename a subdomain), the later steps that depend on it are marked `stale` and run again next.

---

## Configure the level of detail

Everything is set in `design/sa-config.yaml`:

```yaml
profile: high-level      # high-level | detailed | custom
cloud: aws               # cloud profile used from step 10
steps: {}                # per-step options, e.g. {context-map: {detail: with-externals}}
rules: {}                # rule severity overrides, e.g. {LV-01: warn}
```

### Presets

| Option | `high-level` | `detailed` |
|---|---|---|
| `context-map.detail` | `ud-only` (upstream/downstream only) | `with-externals` (adds external systems) |
| `aggregates.detail` | `roots-only` | `full` (entities, value objects, events) |
| `logical-view.vendors` | `none` | `technology-hints` |
| `patterns.split` | `one-per-pattern` | `one-per-pattern` |
| `architecture.shared-layout` | `true` | `true` |

`custom` uses the default of every option unless you set it in `steps`.

### All options

| Step | Option | Values (default first) |
|---|---|---|
| subdomains | `service-per-subdomain` | `one`, `allow-shared` |
| context-map | `detail` | `ud-only`, `with-patterns`, `with-externals` |
| aggregates | `detail` | `roots-only`, `full` |
| logical-view | `vendors` | `none`, `technology-hints`, `named-services` |
| saga | `failure-scenarios` | `2`, `1`, `3` |
| patterns | `split` | `one-per-pattern`, `combined` |
| architecture | `shared-layout` | `true`, `false` |

Changing an option marks the affected steps `stale`, so `/sa-design` redoes them at the new detail.

### Review rules

The rules live in `skills/sa-design/references/rules.yaml`. Each has an ID, the step it checks, a severity and, for some, an option condition. A few examples:

| Rule | Checks | Default |
|---|---|---|
| `FN-01` | The functions document lists functions, not a flow | error |
| `CM-01` | No external systems on a `ud-only` context map | error |
| `AG-01` | Only aggregate roots under `roots-only` | error |
| `LV-01` | No vendor or product names in the logical view | error |
| `SG-02` | Every saga failure scenario has a compensation step | error |
| `AR-02` | High-level and physical views use the same groups | error |
| `AD-01` | Every ADR names an alternative and a trade-off | error |
| `TR-01` | Every pain point is addressed by an ADR or subdomain | error |
| `DOC-02` | Documents describe the solution, not how it evolved | warn |

Override a severity per project with `error`, `warn` or `off`:

```yaml
rules:
  LV-01: warn
  DOC-02: off
```

If a rule fails and you decide to keep the design as it is, `/sa-design` can record an **accepted exception** with your reason. `/sa-review` lists exceptions separately from errors.

### Cloud profiles

Steps 01-09 stay vendor-neutral. Step 10 maps each logical component to a cloud service using `skills/sa-design/references/profiles/<cloud>.md`. The plugin ships `aws`. To add another cloud, copy `aws.md` to `<cloud>.md`, keep the table format (one row per component kind), and set `cloud: <cloud>`.

---

## Run the checks yourself

`/sa-review` runs this script for you. You can also run it directly, in CI for example:

```bash
python3 <plugin>/skills/sa-review/scripts/check.py design
```

| Command | What it does |
|---|---|
| `check.py design` | check every step marked `done` |
| `check.py design --step context-map` | check one step only |
| `check.py design --format json` | machine-readable output with the effective configuration |
| `check.py design --dependents subdomains` | list the steps that depend on a step |
| `check.py design --changed` | list files edited outside `/sa-design` |

Exit codes: `0` no errors, `1` errors found, `2` usage error, unreadable folder or missing Python package.

To write the review report without Claude:

```bash
python3 <plugin>/skills/sa-review/scripts/render_report.py design
```

`<plugin>` is where the plugin lives: your clone, or the path shown by `claude plugin details`.

---

## Draw the diagrams

`/sa-diagrams` runs this script for you:

```bash
python3 <plugin>/skills/sa-diagrams/scripts/diagrams.py design [--only KEY ...] [--png] [--force]
```

It first runs the checks: if the data a diagram needs has errors, nothing is drawn (exit 1). Then it draws every step from 02 to 10 that is `done`, into `design/diagrams/`:

| Step | Diagram | Layout |
|---|---|---|
| 02 functions | one band per actor group | bands |
| 03 subdomains | core / supporting / generic bands, one service per subdomain | bands |
| 04 context map | one arrow per relationship, U and D at the ends; external systems behind an ACL under `with-externals` | elkjs |
| 05 aggregates | aggregate roots and ID references; entities, value objects and events under `full` | elkjs |
| 06 use cases | one page per actor group (split above 40 shapes) | elkjs |
| 07 logical view | one band per layer, numbered flows, no vendor names under `vendors: none` | bands + router |
| 08 saga | one sequence page per scenario; compensations in red | sequence |
| 09 patterns | one page per pattern (or one page under `combined`), numbered steps | bands + router |
| 10 architecture | high-level view and physical / network view on one shared skeleton; AWS icons when `cloud: aws` | skeleton + router |

| File | What it is |
|---|---|
| `NN-<key>.drawio` | the editable diagram of one step (one page per view) |
| `NN-<key>.mermaid.md` | the same nodes and arrows as Mermaid blocks |
| `all-diagrams.drawio` | every page in step order: open this one to present the design |
| `png/NN-<key>-pN.png` | one PNG per page, with `--png` |

| Option | Effect |
|---|---|
| `--only context-map saga` | draw only these steps |
| `--png` | export PNGs with the draw.io desktop CLI (found through `DRAWIO`, the macOS app, or `drawio` on the PATH); unchanged pages are not exported again |
| `--force` | redraw even when the data has not changed |

Exit codes: `0` written or already up to date, `1` the design data has errors, `2` usage error or a missing dependency (the message gives the install command). Steps 04-06 need Node.js and elkjs; other steps draw without them.

Every diagram records the hash of the data it was drawn from, so a second run redraws only what changed, and `/sa-review` warns (rule `DG-01`) when a diagram is older than its data. All diagrams share one style: one fill per subdomain type, one arrow style per interaction kind (sync, async, auth, data, external), and a legend on every page that lists only what that page uses.

---

## Build the deck

`/sa-deck` drafts `design/deck/deck.yaml` with you and renders it. The single source holds, for every slide, the title, the key message, one body block, the spoken script and the seconds. You can also run the script yourself:

```bash
python3 <plugin>/skills/sa-deck/scripts/deck.py design --outline --minutes 20   # print a draft deck.yaml
python3 <plugin>/skills/sa-deck/scripts/deck.py design [--force]                # check and render
```

The draft follows the 4+1 views and contains only the steps that are done:
1. cover and agenda;
2. introduction: proposed solution, business functions;
3. domain design: subdomains, context map, aggregates;
4. the use case, logical and process views (one slide per saga scenario);
5. core patterns, then the high-level and physical views;
6. technology stack, ADRs, and Q&A.

The seconds are scaled to fit the talk length. `skills/sa-deck/references/outline.md` explains what each slide's key message and script should say.

| Block | Shows |
|---|---|
| `bullets` | up to 6 points, `**bold**` allowed |
| `table` | header and up to 8 rows |
| `diagram` / `diagrams` | one or two `/sa-diagrams` pages, with the legend as chips underneath |
| `diagram-text` | a diagram page with 2–4 points beside it |
| `agenda` | the section titles with their slide numbers |
| `image` | a PNG or JPEG inside `design/deck/` |

| File | What it is |
|---|---|
| `deck/deck.yaml` | the source you edit |
| `deck/deck.html` | one self-contained file; ← → or Space to move, `N` for speaker notes, `#n` to jump; print gives one slide per PDF page |
| `deck/deck.pptx` | the same slides, text, tables and speaker notes as editable PowerPoint |
| `deck/assets/` | slide images exported from the diagrams (cached) |

**Checks before rendering.**
- **Errors** (exit 1, nothing written): a schema problem, a diagram page that does not exist, an image outside `deck/`, a table row with the wrong number of cells, or a stated "N services" that differs from `subdomains.yaml`.
- **Warnings** (rendering continues): the talk runs over its time budget, or a script is longer than its seconds at about 130 words per minute.

**Missing tools.** Without Node or pptxgenjs, only the HTML is written. Without draw.io, cached slide images are used and other diagrams show a placeholder.

**Rebuilds.** A second run with unchanged sources reports `unchanged deck`. `/sa-review` warns with `DK-01` when the deck is older than `deck.yaml` or the diagrams it shows.

---

## Examples

Two fictional design sets show what the output looks like:

| Example | Content |
|---|---|
| [`examples/clinic-booking`](examples/clinic-booking) | All 12 steps for a clinic appointment platform (`high-level` preset), with the review report, the diagrams and a 20-minute deck (`design/deck/`) |
| [`examples/food-delivery/design`](examples/food-delivery/design) | Steps 01-05 for a food ordering and delivery system (`high-level`) |
| [`examples/food-delivery/design-detailed`](examples/food-delivery/design-detailed) | The same steps under the `detailed` preset: aggregate internals and external systems appear |

Each folder has the sample brief (`brief.md`) next to the generated `design/` folder. Every design folder also holds its generated `diagrams/` (draw.io, Mermaid and PNG).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/sa-design` is not listed | Start a new Claude Code session after installing; check with `claude plugin details sa-design-kit@sa-design-kit-marketplace` |
| `missing dependency: yaml` or `jsonschema` | `python3 -m pip install --user pyyaml jsonschema` |
| `not a design folder` | Run `/sa-design` once to create `design/` with `sa-config.yaml` and `design-state.yaml` |
| `CONFIG` error | A preset, option, value or rule ID in `sa-config.yaml` is unknown; the message lists the allowed values |
| `SCHEMA` error | A YAML data file does not match its schema; the item path shows where (for example `relationships[0].pattern`) |
| A later step is `stale` | An earlier step changed; run `/sa-design` to redo it |
| You edited a file by hand | `/sa-design` notices it at the start of the next run and offers to mark dependent steps stale |
| `graph layout needs Node.js and elkjs` | Install Node.js 18+, then `npm install --prefix <plugin>/skills/sa-diagrams/tools`; or draw other steps with `--only` |
| `png: draw.io CLI not found` | Install draw.io desktop or set `DRAWIO` to its executable; the `.drawio` and Mermaid files are written anyway |
| `DG-01` warning in the review | The data changed after the diagrams were drawn; run `/sa-diagrams` again |
| `pptx skipped` | Install Node.js 18+, then `npm install --prefix <plugin>/skills/sa-deck/tools`; the HTML deck is written anyway |
| `row N has M cells for K columns` | A table cell contains a comma in a YAML `[...]` list; quote the cell or write the row as a block list |
| `DK-01` warning in the review | `deck.yaml` or a diagram it shows changed after the deck was rendered; run `/sa-deck` again |

---

## Repository layout

```
.claude-plugin/            plugin manifest and marketplace entry
skills/sa-design/          the guided design skill
  references/steps/        one guide per step (purpose, options, key questions, checklist)
  references/schema/       JSON Schemas (in YAML) for every data file
  references/templates/    starting files for a new design folder and each step
  references/presets.yaml  preset -> option values
  references/rules.yaml    review rule catalogue
  references/profiles/     cloud profiles (aws)
skills/sa-review/          the review skill
  scripts/check.py         mechanical checks (CLI)
  scripts/render_report.py writes review-report.md
  scripts/sacheck/         the check library
skills/sa-diagrams/        the diagrams skill
  scripts/diagrams.py      draws the diagrams (CLI)
  scripts/sadiagram/       drawing model, layouts, builders per step, draw.io / Mermaid writers
  tools/                   elkjs graph layout (npm install here)
skills/sa-deck/            the presentation skill
  scripts/deck.py          drafts the outline, checks and renders the deck (CLI)
  scripts/sadeck/          deck model, schema, outline, checks, HTML and PowerPoint renderers
  references/              deck schema, default theme, outline guide
  tools/                   pptxgenjs PowerPoint renderer (npm install here)
examples/                  fictional sample design sets
tests/                     pytest suite
docs/specs/                living specification of the plugin
```

---

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install pyyaml jsonschema pytest ruff
npm install --prefix skills/sa-diagrams/tools   # graph-layout tests skip without it
npm install --prefix skills/sa-deck/tools       # PowerPoint tests skip without it
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
claude plugin validate .
```

When you add a rule to `rules.yaml` with `check: script`, implement it in `skills/sa-review/scripts/sacheck/checks.py` under the same ID and add a negative case in `tests/test_checks.py`. The test suite fails if a script rule has no implementation.
