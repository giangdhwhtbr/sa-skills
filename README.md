# sa-design-kit

A Claude Code plugin that guides you through a **DDD + microservices solution design**, step by step, and reviews the result.

- **`/sa-design`** walks you through 12 design steps: brief, business functions, subdomains, context map, aggregate roots, use cases, logical view, core flow (saga), core patterns, architecture, technology stack and architecture decisions. Each step proposes content, asks you the key decisions one at a time (always with a recommendation), then writes a Markdown document and a YAML data file into your project's `design/` folder.
- **`/sa-review`** audits the design folder without changing it: completeness, schemas, review rules, cross-step consistency and traceability. It writes `design/review-report.md`.

The level of detail is configurable: one high-level preset for architecture reviews, one detailed preset, or your own mix of options and rule severities.

---

## Requirements

| Need | Version | Why |
|---|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | recent | runs the skills |
| Python | 3.10 or newer | the review checks (`check.py`) |
| `pyyaml`, `jsonschema` | any recent | used by `check.py` |

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

You should see `Skills (2): sa-design, sa-review`. Start a new Claude Code session in your project and the commands `/sa-design` and `/sa-review` are available.

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

## Examples

Two fictional design sets show what the output looks like:

| Example | Content |
|---|---|
| [`examples/clinic-booking`](examples/clinic-booking) | All 12 steps for a clinic appointment platform (`high-level` preset), with the review report |
| [`examples/food-delivery/design`](examples/food-delivery/design) | Steps 01-05 for a food ordering and delivery system (`high-level`) |
| [`examples/food-delivery/design-detailed`](examples/food-delivery/design-detailed) | The same steps under the `detailed` preset: aggregate internals and external systems appear |

Each folder has the sample brief (`brief.md`) next to the generated `design/` folder.

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
examples/                  fictional sample design sets
tests/                     pytest suite
docs/specs/                living specification of the plugin
```

---

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install pyyaml jsonschema pytest ruff
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
claude plugin validate .
```

When you add a rule to `rules.yaml` with `check: script`, implement it in `skills/sa-review/scripts/sacheck/checks.py` under the same ID and add a negative case in `tests/test_checks.py`. The test suite fails if a script rule has no implementation.
