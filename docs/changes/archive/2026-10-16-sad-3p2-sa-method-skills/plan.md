# Plan: SA method skills (/sa-design and /sa-review)

Epic: sad-3p2
Spec: `docs/changes/sad-3p2-sa-method-skills/` (proposal.md, spec-delta.md, design.md, tests.md)

## Objective

A project-independent Claude Code plugin, `sa-design-kit`, at the root of this repository, with two skills:
`/sa-design` guides a solution architect through 12 DDD + microservices design steps (Markdown + YAML per step, configurable detail, per-step checklist, resumable state);
`/sa-review` audits a design set read-only and writes `design/review-report.md`.
Done when every REQ in spec-delta.md has passing tests or a recorded manual check, `pytest` and `ruff check .` pass, and both example design sets pass `check.py`.

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
- Problem statement: the DDD + microservices design method and its review rules are not packaged; every architect rediscovers the path and reviewers catch the same issues again.
- Success criteria (copied from proposal.md):
  - Running `/sa-design` on the clinic-booking sample brief with the `high-level` preset produces a complete design set (all 12 steps) in `examples/clinic-booking/`, and `check.py` reports no errors on it.
  - Steps 01-05 run on the food-delivery sample brief (`examples/food-delivery/`) and pass the checks, showing the method is not tied to one domain.
  - Switching the preset to `detailed` changes what steps propose (for example entities and value objects in aggregates, external systems on the context map) and which rules are active, without editing the skills.
  - The plugin contains no references to any specific client, course or past project.
  - `pytest` passes.
- Constraints (Global Constraints, copied from the spec):
  - REQ-QUALITY-005: The plugin's skills, references, templates and examples SHALL NOT name any real client, course, organisation or past project; examples SHALL use fictional sample briefs.
  - REQ-DESIGN-004: no step writes its files until the user has answered its key questions.
  - REQ-REVIEW-001: `/sa-review` never modifies design files.
  - Steps 01-09 stay vendor-neutral by default; cloud services appear from step 10 (REQ-CONFIG-006).
  - Python 3.10+, dependencies limited to PyYAML and jsonschema; tests with pytest; lint with ruff.
- Non-goals (copied from proposal.md):
  - Drawing diagrams (draw.io, Mermaid) or building slide decks; that is sub-project 2.
  - Effort, cost and schedule estimation, pattern catalogue and review Q&A library; that is sub-project 3.
  - Architecture styles other than DDD + microservices (modular monolith, serverless-first).
  - Cloud profiles other than AWS.
  - Per-step slash commands (for example `/sa-context-map`); steps are run through `/sa-design`.

## Approach Options
### Option 1: Orchestrator skill with step guides + read-only review skill (selected in discuss, ADR 0001)
- Summary: `/sa-design` loads one step guide at a time from `references/steps/`; shared schemas, presets and rules; `/sa-review` runs `check.py` plus judgement rules.
- Pros: two commands; small context per run; one source of truth for schemas, options, rules and step dependencies.
- Cons: steps are not individual slash commands.

### Option 2: One skill per step
- Summary: about 12 skills plus orchestrator and review.
- Pros: each step directly invocable.
- Cons: duplicated shared rules and schema references; more drift.

### Recommended Approach
- Selected option: Option 1.
- Reasoning: matches the guided, stateful use confirmed in discuss and keeps one source of truth (see `docs/adr/0001-orchestrator-skill-with-step-guides.md`).

## Scope
- In scope: plugin packaging, config (presets, options, rules), 12 data schemas and templates, `check.py` and its tests, 12 step guides, AWS profile, the two SKILL.md files, two fictional example design sets, neutral-content test.
- Out of scope: everything listed under Non-goals.

## Execution Strategy

```yaml
execution_strategy:
  mode: direct
  workers:
    mode: sequential
  rationale: Single provider mode; tracks share one schema and rule vocabulary and mostly depend on each other in sequence, so one agent working track by track avoids interface drift.
```

## Shared definitions (used by every track)

### Repository layout

```
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
pyproject.toml
README.md
skills/sa-design/SKILL.md
skills/sa-design/references/steps/NN-<key>.md          # 12 step guides (front matter + body)
skills/sa-design/references/schema/<file>.schema.yaml  # 12 data schemas + sa-config + design-state
skills/sa-design/references/templates/                 # sa-config.yaml, design-state.yaml, NN-<key>.md, <data>.yaml
skills/sa-design/references/presets.yaml
skills/sa-design/references/rules.yaml
skills/sa-design/references/vendor-terms.yaml
skills/sa-design/references/profiles/aws.md
skills/sa-review/SKILL.md
skills/sa-review/scripts/check.py                      # CLI entry
skills/sa-review/scripts/sacheck/__init__.py
skills/sa-review/scripts/sacheck/model.py              # Finding, Severity
skills/sa-review/scripts/sacheck/catalog.py            # load step guides, presets, rules, schemas
skills/sa-review/scripts/sacheck/config.py             # effective configuration
skills/sa-review/scripts/sacheck/checks.py             # check functions
skills/sa-review/scripts/sacheck/report.py             # text / json output
tests/conftest.py
tests/test_*.py
tests/fixtures/<case>/design/...
tests/deny-terms.txt
examples/clinic-booking/brief.md, examples/clinic-booking/design/...
examples/food-delivery/brief.md, examples/food-delivery/design/...
```

### Steps (key, number, files)

| # | key | Markdown | data file | inputs (data files read) |
|---|---|---|---|---|
| 01 | brief | 01-brief.md | brief.yaml | none |
| 02 | functions | 02-functions.md | functions.yaml | brief.yaml |
| 03 | subdomains | 03-subdomains.md | subdomains.yaml | brief.yaml, functions.yaml |
| 04 | context-map | 04-context-map.md | context-map.yaml | subdomains.yaml |
| 05 | aggregates | 05-aggregates.md | aggregates.yaml | subdomains.yaml, context-map.yaml |
| 06 | use-cases | 06-use-cases.md | use-cases.yaml | brief.yaml, functions.yaml |
| 07 | logical-view | 07-logical-view.md | logical.yaml | brief.yaml, subdomains.yaml, context-map.yaml |
| 08 | saga | 08-saga.md | saga.yaml | subdomains.yaml, aggregates.yaml, logical.yaml |
| 09 | patterns | 09-patterns.md | patterns.yaml | logical.yaml |
| 10 | architecture | 10-architecture.md | architecture.yaml | logical.yaml, patterns.yaml |
| 11 | stack | 11-stack.md | stack.yaml | architecture.yaml |
| 12 | adrs | 12-adrs.md | adrs.yaml | brief.yaml and all earlier data files |

### Step guide front matter (exact keys; parsed by `catalog.py`)

```yaml
---
number: 4
key: context-map
title: Context map
markdown: 04-context-map.md
data: context-map.yaml
schema: context-map.schema.yaml
inputs: [subdomains.yaml]
options:
  detail:
    values: [ud-only, with-patterns, with-externals]
    default: ud-only
    affects: "What the map shows: only upstream/downstream, plus relationship patterns, or also external systems"
rules: [CM-01, CM-02, CM-03]
---
```

### Options (declared in step guides; values below are authoritative)

| step key | option | values | default |
|---|---|---|---|
| subdomains | service-per-subdomain | one, allow-shared | one |
| context-map | detail | ud-only, with-patterns, with-externals | ud-only |
| aggregates | detail | roots-only, full | roots-only |
| logical-view | vendors | none, technology-hints, named-services | none |
| saga | failure-scenarios | 1, 2, 3 | 2 |
| patterns | split | one-per-pattern, combined | one-per-pattern |
| architecture | shared-layout | true, false | true |

`roots-only` = aggregate roots and the ID references between them; `full` adds entities, value objects and domain events.

### presets.yaml (exact content)

```yaml
high-level:
  context-map: {detail: ud-only}
  aggregates: {detail: roots-only}
  logical-view: {vendors: none}
  patterns: {split: one-per-pattern}
  architecture: {shared-layout: true}
detailed:
  context-map: {detail: with-externals}
  aggregates: {detail: full}
  logical-view: {vendors: technology-hints}
  patterns: {split: one-per-pattern}
  architecture: {shared-layout: true}
```
`custom` has no entry: every option takes its explicit value in `sa-config.yaml` or its default.

### sa-config.yaml (template content)

```yaml
profile: high-level      # high-level | detailed | custom
cloud: aws
steps: {}                # e.g. {context-map: {detail: with-patterns}}
rules: {}                # e.g. {LV-01: warn}
```

### design-state.yaml (template content, 12 entries in this form)

```yaml
version: 1
steps:
  - key: brief
    status: todo          # todo | done | stale | needs-review
    decisions: []         # short strings, one per decided question
    open_questions: []
    exceptions: []        # [{rule: LV-01, reason: "..."}]
    stale_reason: null
    files: {}             # {"brief.yaml": "<sha256>", "01-brief.md": "<sha256>"} written by the skill after each write
```

### Data file shapes (each schema enforces these; IDs are kebab-case strings)

- `brief.yaml`: `system {name, summary}`, `goals [str]`, `pain_points [{id, text}]`, `actors [{id, name, kind: person|system}]`, `nfrs [{id, category, target}]`, `constraints [str]`, `assumptions [str]`.
- `functions.yaml`: `groups [{id, name, actor_ids [id], functions [{id, name, description}]}]`.
- `subdomains.yaml`: `subdomains [{id, name, type: core|supporting|generic, description, service {id, name}, function_ids [id]}]`. The subdomain `id` is also the bounded-context ID used by later steps.
- `context-map.yaml`: `relationships [{upstream, downstream, pattern, label}]` with `pattern` in `customer-supplier, open-host-service, published-language, conformist, anti-corruption-layer, partnership, shared-kernel, domain-events`; optional `externals [{id, name, direction: inbound|outbound}]`.
- `aggregates.yaml`: `aggregates [{id, root, subdomain_id, entities [str], value_objects [str], events [str]}]`, `references [{from, to, via, multiplicity}]`, `no_aggregate [{subdomain_id, reason}]`.
- `use-cases.yaml`: `use_cases [{id, name, actor_ids [id], function_ids [id], includes [id], extends [id]}]`.
- `logical.yaml`: `layers [{id, name, components [{id, name, kind, service_id?}]}]` with `kind` in `client, gateway, identity-provider, service, broker, datastore, external`; `flows [{from, to, kind: sync|async|data|auth|external, label}]`.
- `saga.yaml`: `flow {id, name, orchestrator}`, `participants [id]`, `scenarios [{id, name, kind: happy|failure, steps [{n, from, to, message, kind: sync|async|compensate|self}]}]`.
- `patterns.yaml`: `patterns [{id: security|observability|resilience, summary, steps [{n, from, to, text}]}]`.
- `architecture.yaml`: `cloud`, `mapping [{logical_id, cloud_service, notes}]`, `high_level {groups [str]}`, `physical {regions: int, availability_zones: int, groups [str], tiers [{id, name, internet_route: bool, cidr}], security_rules [str]}`.
- `stack.yaml`: `layers [{id, name, choice, reason}]`.
- `adrs.yaml`: `adrs [{id, title, decision, alternatives [str], tradeoff, rationale, status: proposed|accepted|superseded, pain_points [id]}]`.

### rules.yaml (exact catalogue; `check: script` rules are implemented in `checks.py` under the same ID)

| id | step | severity | condition | check | statement |
|---|---|---|---|---|---|
| BR-01 | brief | error | | script | Every pain point, actor and NFR has a unique ID |
| FN-01 | functions | error | | judgement | The functions document lists functions grouped by actor; it does not draw a flow |
| FN-02 | functions | error | | script | Every function group names at least one actor from brief.yaml |
| SD-01 | subdomains | warn | | script | At least one subdomain is core |
| SD-02 | subdomains | error | subdomains.service-per-subdomain = one | script | Every subdomain has exactly one service and service IDs are unique |
| CM-01 | context-map | error | context-map.detail = ud-only | script | The context map has no external systems |
| CM-02 | context-map | error | | script | Every relationship end is a known context and upstream differs from downstream |
| CM-03 | context-map | warn | | script | Every context appears in at least one relationship |
| AG-01 | aggregates | error | aggregates.detail = roots-only | script | Aggregates list roots only: entities, value objects and events are empty |
| AG-02 | aggregates | error | | script | Every aggregate belongs to a known subdomain and every reference joins two known aggregates by an ID field |
| AG-03 | aggregates | warn | | script | Every subdomain has an aggregate or a no_aggregate entry with a reason |
| UC-01 | use-cases | error | | script | Every use case has an actor from brief.yaml and refers to known functions |
| LV-01 | logical-view | error | logical-view.vendors = none | script | The logical view names no vendor or product (vendor-terms.yaml) |
| LV-02 | logical-view | error | | script | Every service in subdomains.yaml appears as a service component |
| SG-01 | saga | error | | script | The saga has a happy scenario and at least `saga.failure-scenarios` failure scenarios |
| SG-02 | saga | error | | script | Every failure scenario contains a compensate step |
| SG-03 | saga | error | | script | The orchestrator and every participant are known services or externals |
| PT-01 | patterns | error | | script | Security, observability and resilience are each described |
| PT-02 | patterns | warn | patterns.split = one-per-pattern | judgement | Each pattern has its own section and view |
| AR-01 | architecture | error | | script | Every logical component of kind gateway, identity-provider, broker or datastore maps to a cloud service |
| AR-02 | architecture | error | architecture.shared-layout = true | script | high_level.groups and physical.groups are the same list in the same order |
| AR-03 | architecture | warn | | script | A tier named data has internet_route false |
| ST-01 | stack | error | | script | Every stack layer has a choice and a reason |
| AD-01 | adrs | error | | script | Every ADR has at least one alternative and a non-empty trade-off |
| TR-01 | adrs | error | | script | Every pain point in brief.yaml is referenced by an ADR or by a subdomain description |
| XS-01 | all | error | | script | Every ID referenced in any data file is defined in its source file |
| XS-02 | all | error | | script | Any "<number> services" statement in the Markdown files equals the number of services in subdomains.yaml |
| DOC-01 | all | warn | | judgement | Each document's title matches what its content shows |
| DOC-02 | all | warn | | judgement | Documents describe the solution, not how the design evolved or who reviewed it |

`rules.yaml` stores each row as `{id, step, severity, condition: {step: <key>, option: <name>, equals: <value>} | null, check: script|judgement, statement}`.

### check.py interface (exact)

```
python3 skills/sa-review/scripts/check.py DESIGN_DIR [--step KEY] [--format text|json]
        [--dependents KEY] [--changed]
exit 0: no error findings; exit 1: at least one error finding; exit 2: usage error, unreadable file or missing dependency
```
- default: run all checks for all steps whose status is `done` (and XS rules across them).
- `--step KEY`: run that step's schema validation and rules only.
- `--dependents KEY`: print the keys of steps that read the step's data file, directly or transitively, one per line, exit 0.
- `--changed`: print `<file>` for every file whose sha256 differs from `design-state.yaml` `files`, exit 0.
- text output: one line per finding `ERROR|WARN <rule-id> <file> <item>: <message>`, errors first, then a summary line `N errors, M warnings`.
- json output: `{"config": {...effective...}, "findings": [{"rule","severity","file","item","message"}], "exceptions": [{"step","rule","reason"}]}`.

```python
# sacheck/model.py
from dataclasses import dataclass
from typing import Literal
Severity = Literal["error", "warn"]
@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    file: str
    item: str
    message: str
```

Built-in check IDs that are not catalogue rules: `SCHEMA` (data file invalid against schema), `MISSING` (a `done` step lacks a file), `CONFIG` (unknown preset, option, value or rule ID in sa-config.yaml); all are severity `error`.

## Tasks

### Track 1: Plugin skeleton and configuration catalogue
- **Dependencies**: none
- **Requirements**: REQ-PLUGIN-001, REQ-CONFIG-001, REQ-CONFIG-002, REQ-CONFIG-003, REQ-CONFIG-004, REQ-QUALITY-001
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - create `.claude-plugin/plugin.json` (`name: sa-design-kit`, `version: 0.1.0`, description "Guided DDD + microservices solution design and review", `author {name}`)
  - create `.claude-plugin/marketplace.json` (`name: sa-design-kit-marketplace`, one plugin entry with `source: "./"`)
  - create `pyproject.toml` (project `sa-design-kit`, requires-python `>=3.10`, deps `pyyaml`, `jsonschema`; dev `pytest`, `ruff`; `[tool.ruff.lint] select = ["E","F","I","B","UP","BLE"]`; `[tool.pytest.ini_options] testpaths = ["tests"]`, `pythonpath = ["skills/sa-review/scripts"]`)
  - create `skills/sa-design/references/presets.yaml`, `rules.yaml` (all rows above), `vendor-terms.yaml` (list: aws, amazon, azure, gcp, google cloud, kafka, rabbitmq, sns, sqs, eventbridge, kinesis, aurora, postgresql, postgres, mysql, oracle, mongodb, dynamodb, redis, elasticache, opensearch, elasticsearch, s3, lambda, fargate, ecs, eks, kubernetes, cognito, entra, okta, keycloak, cloudfront, route 53, nginx, spring, nestjs, react, next.js)
  - create `skills/sa-design/references/schema/sa-config.schema.yaml`, `design-state.schema.yaml`
  - create `skills/sa-design/references/templates/sa-config.yaml`, `design-state.yaml` (12 entries, keys from the Steps table)
  - create `skills/sa-review/scripts/sacheck/__init__.py`, `model.py`, `catalog.py`, `config.py`
  - create `tests/conftest.py` (fixtures `refs_dir`, `catalog`), `tests/test_catalog.py`, `tests/test_config.py`, `tests/test_plugin.py`
  - modify `.agent-workflow/config.yaml` via `gin-workflow setup configure --set 'verify.checks.test="pytest"' --set 'verify.checks.lint="ruff check ."'` (dry-run first, then apply)
- **Interfaces produced**:
  - `catalog.load_steps(refs: Path) -> list[StepSpec]` with `StepSpec(number:int, key:str, title:str, markdown:str, data:str, schema:str, inputs:list[str], options:dict[str, OptionSpec], rules:list[str])`, `OptionSpec(values:list, default:Any, affects:str)`. Track 1 reads step front matter only from files that exist; Tracks 3-4 add the guides.
  - `catalog.load_rules(refs) -> dict[str, RuleSpec]` with `RuleSpec(id, step, severity, condition: Condition|None, check, statement)`, `Condition(step, option, equals)`.
  - `catalog.load_presets(refs) -> dict[str, dict[str, dict[str, Any]]]`.
  - `config.effective(design_dir: Path, refs: Path) -> EffectiveConfig` with `EffectiveConfig(profile:str, cloud:str, options: dict[str, dict[str, Any]], severities: dict[str, str], problems: list[Finding])`; `config.rule_active(rule: RuleSpec, cfg: EffectiveConfig) -> bool`.
- **Steps**:
  1. Write `tests/test_plugin.py::test_manifest_names_two_skills` (REQ-PLUGIN-001): load plugin.json, assert `name == "sa-design-kit"`; assert `skills/` contains exactly `sa-design/SKILL.md` and `sa-review/SKILL.md` paths (create the two SKILL.md files with front matter `name`, `description` only in this track). Run `pytest tests/test_plugin.py` → fails; create files → passes.
  2. Write `tests/test_catalog.py::test_rules_well_formed` (REQ-QUALITY-001, REQ-CONFIG-003): every rule has id matching `^[A-Z]{2,3}-\d{2}$`, step in step keys or `all`, severity in `error|warn|off`, check in `script|judgement`; `test_bad_severity_rejected` loads a temp rules file with `severity: fatal` and asserts `catalog.load_rules` raises `ValueError` naming the rule. Run → fail; implement `catalog.load_rules` → pass.
  3. Write `tests/test_config.py`: `test_default_high_level` (REQ-CONFIG-002) builds a temp design dir from the templates and asserts `cfg.options["aggregates"]["detail"] == "roots-only"`; `test_detailed_preset` asserts `full` and `with-externals`; `test_custom_uses_defaults_and_explicit`; `test_unknown_value_rejected` (REQ-CONFIG-001) with `steps: {context-map: {detail: everything}}` asserts one `CONFIG` finding listing the allowed values; `test_severity_override` (REQ-CONFIG-004) with `rules: {LV-01: warn}`; `test_unknown_rule_override_rejected`; `test_rule_active_condition` (CM-01 inactive when detail = with-externals). Until Track 3/4 add guides, the tests pass the options table through a fixture `step_options` that `conftest.py` builds from a minimal front-matter file written to a temp refs dir. Run → fail; implement `config.effective` and `config.rule_active` → pass.
  4. Run `ruff check .` and `pytest`; both clean.
- **Acceptance criteria**: tests above pass; `ruff check .` clean; verify commands set in `.agent-workflow/config.yaml`.

### Track 2: Data schemas and templates
- **Dependencies**: Track 1
- **Requirements**: REQ-DESIGN-003, REQ-DESIGN-005, REQ-QUALITY-001
- **Provider role**: `backend`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - create `skills/sa-design/references/schema/{brief,functions,subdomains,context-map,aggregates,use-cases,logical,saga,patterns,architecture,stack,adrs}.schema.yaml` (JSON Schema draft 2020-12 written in YAML, shapes from "Data file shapes"; `additionalProperties: false`; IDs `pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"`)
  - create `skills/sa-design/references/templates/<data>.yaml` for the 12 data files (smallest valid instance with one example item each, neutral names such as `example-context`)
  - create `skills/sa-design/references/templates/NN-<key>.md` for the 12 steps (headings: `# <Title>`, `## Summary`, `## Decisions`, `## Details`, `## Open questions`)
  - create `skills/sa-review/scripts/sacheck/schemas.py`
  - create `tests/test_schemas.py`
- **Interfaces produced**: `schemas.validate(data_file: Path, schema_file: Path) -> list[Finding]` (rule `SCHEMA`, item = JSON path of the error); `schemas.schema_for(step: StepSpec, refs: Path) -> Path`.
- **Steps**:
  1. Write `tests/test_schemas.py::test_templates_validate` (REQ-QUALITY-001), parametrised over the 12 data templates, asserting `schemas.validate(...) == []`. Run → fail (files missing).
  2. Create the 12 schemas and templates; implement `schemas.validate` with `jsonschema.Draft202012Validator`. Run → pass.
  3. Write `test_bad_edge_type_rejected` (REQ-DESIGN-005): a context-map with `pattern: friendly` yields one `SCHEMA` finding whose item names `relationships[0].pattern`. Run → pass.
  4. Write `test_every_step_has_schema_and_templates` (REQ-DESIGN-003): for each row of the Steps table, the schema, the data template and the Markdown template exist. Run → pass.
- **Acceptance criteria**: 12 schemas, 24 templates; tests pass; ruff clean.

### Track 3: Mechanical checks (check.py) and fault fixtures
- **Dependencies**: Track 2
- **Requirements**: REQ-REVIEW-002, REQ-REVIEW-004, REQ-REVIEW-005, REQ-REVIEW-006, REQ-DESIGN-006, REQ-DESIGN-008, REQ-DESIGN-009, REQ-CONFIG-005, REQ-QUALITY-002
- **Provider role**: `backend`
- **Reasoning**: `high`
- **Model class**: `standard_impl`
- **Estimated complexity**: high
- **Files**:
  - create `skills/sa-review/scripts/sacheck/checks.py`, `report.py`, `skills/sa-review/scripts/check.py`
  - create `tests/fixtures/clean/design/` (all 12 steps `done`, small consistent fictional system "parcel-locker"), and fault fixtures copied from it with one change each: `broken-reference` (saga participant `unknown-svc`), `vendor-in-logical` (component name "Kafka broker"), `adr-without-tradeoff`, `missing-file` (step 06 done, use-cases.yaml absent), `count-mismatch` (Markdown says "9 services" while 8 exist), `unaddressed-pain-point`, `roots-only-violated` (entities listed with roots-only), `exception-accepted` (vendor-in-logical plus `exceptions: [{rule: LV-01, reason: "..."}]` on step logical-view)
  - create `tests/test_checks.py`, `tests/test_cli.py`
- **Interfaces produced**:
  - `checks.run(design_dir: Path, refs: Path, step: str | None = None) -> tuple[EffectiveConfig, list[Finding], list[dict]]` (findings exclude accepted exceptions, which are returned as the third element).
  - one function per script rule, named `rule_<id>` with `-` replaced by `_` (for example `rule_lv_01(ctx) -> list[Finding]`), registered in `checks.RULES: dict[str, Callable[[Context], list[Finding]]]`; `Context(design_dir, refs, cfg, data: dict[str, Any], markdown: dict[str, str], steps: list[StepSpec], state: dict)`.
  - `checks.dependents(step_key: str, steps: list[StepSpec]) -> list[str]` (transitive, by `inputs`).
  - `checks.changed_files(design_dir: Path) -> list[str]` (sha256 vs `design-state.yaml` `files`).
  - `report.text(findings, exceptions, cfg) -> str`, `report.json(findings, exceptions, cfg) -> str`.
- **Steps** (each: write the test, run it failing, implement, run it passing):
  1. `test_clean_fixture_has_no_errors` (REQ-QUALITY-002): `checks.run(clean)` returns no `error` findings.
  2. `test_broken_reference` (REQ-REVIEW-004): exactly one finding `XS-01` on `saga.yaml` with item `unknown-svc`; implement XS-01 by collecting defined IDs per source file and walking every `*_id`, `*_ids`, `from`, `to`, `upstream`, `downstream`, `orchestrator`, `participants`, `subdomain_id`, `logical_id`, `service_id` field.
  3. `test_vendor_in_logical` (REQ-DESIGN-009): one `LV-01` error; `test_vendor_allowed_with_hints` sets `logical-view: {vendors: technology-hints}` and asserts no LV-01.
  4. `test_adr_without_tradeoff` (REQ-REVIEW-005): one `AD-01`; `test_unaddressed_pain_point`: one `TR-01` naming the pain point ID.
  5. `test_missing_file` (REQ-REVIEW-002): one `MISSING` finding for step `use-cases`.
  6. `test_count_mismatch`: one `XS-02` naming the Markdown file.
  7. `test_roots_only_violated`: one `AG-01`; with `aggregates: {detail: full}` none.
  8. `test_exception_accepted` (REQ-DESIGN-009): no LV-01 error finding; the exception is returned with its reason.
  9. Remaining script rules (BR-01, FN-02, SD-01, SD-02, CM-01, CM-02, CM-03, AG-02, AG-03, UC-01, LV-02, SG-01, SG-02, SG-03, PT-01, AR-01, AR-02, AR-03, ST-01): one positive test each on the clean fixture (no finding) and one negative test each built by mutating a copy of the clean fixture in `tmp_path`; `test_every_script_rule_implemented` asserts `set(checks.RULES) == {r.id for r in rules if r.check == "script"}`.
  10. `test_dependents` (REQ-DESIGN-006, REQ-CONFIG-005): `dependents("subdomains")` equals `["context-map", "aggregates", "logical-view", "saga", "patterns", "architecture", "stack", "adrs"]` (transitive over the Steps table inputs; `use-cases` is not included because it reads only brief and functions); `dependents("brief")` equals every other step key in step order.
  11. `test_changed_files` (REQ-DESIGN-008): edit a fixture copy's `subdomains.yaml`; `changed_files` returns `["subdomains.yaml"]`.
  12. `tests/test_cli.py` (REQ-REVIEW-006): run `check.py` with `subprocess` on clean → exit 0 and last line `0 errors, ...`; on broken-reference → exit 1 and a line starting `ERROR XS-01 saga.yaml unknown-svc`; on a missing directory → exit 2; `--format json` parses and has keys `config, findings, exceptions`; `--dependents subdomains` prints the list from step 10; `--step context-map` on broken-reference → exit 0 (saga not checked).
- **Acceptance criteria**: all tests pass; every script rule has a positive and negative test; ruff clean.

### Track 4: Step guides 01-06
- **Dependencies**: Track 2
- **Requirements**: REQ-DESIGN-003, REQ-DESIGN-004, REQ-CONFIG-001, REQ-CONFIG-002
- **Provider role**: `docs`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `skills/sa-design/references/steps/01-brief.md` … `06-use-cases.md`; create `tests/test_step_guides.py`.
- **Content of every guide** (sections in this order): front matter (exact keys above, options from the Options table, rules from rules.yaml for that step); `## Purpose` (one paragraph); `## Inputs` (data files read and what is used from each); `## Propose` (what to draft from the inputs, per option value: for example 05 under `roots-only` drafts roots and ID references only, under `full` adds entities, value objects and events); `## Key questions` (2-5 numbered questions, each with the recommended answer and why); `## Write` (the Markdown sections and the data fields to fill); `## Checklist` (rule IDs with their statements, and the judgement rules spelled out for the agent); `## Good and bad` (one short correct and one incorrect example, using a neutral domain).
- **Step-specific key questions**:
  - 01 brief: system name and one-line summary; top 3-5 pain points; actors (people and external systems); NFR targets (availability, latency, peak load); hard constraints (cloud, identity provider, compliance).
  - 02 functions: grouping by actor (recommend traveler/customer-facing, back office, administration style groups); any function that belongs to two actors; functions out of scope.
  - 03 subdomains: classification of each candidate (core, supporting, generic) with the "competitive advantage / needed / buy" test; split or merge candidates (recommend split when lifecycles or change rates differ); one service per subdomain (option).
  - 04 context-map: upstream for each dependency (who provides the model); relationship pattern per edge when `detail` is not `ud-only`; external systems when `with-externals`.
  - 05 aggregates: root per subdomain; subdomains with no aggregate (read models) and why; references by ID and multiplicity; under `full`, entities/value objects/events per root.
  - 06 use-cases: use cases per actor derived from functions; include/extend relations; external systems taking part.
- **Steps**:
  1. Write `tests/test_step_guides.py::test_guides_front_matter` (parametrised 01-12, skip missing ones until Track 5 lands): front matter keys exactly as specified; `rules` subset of rules.yaml for that step; options equal the Options table; required sections present in order. Run → fail.
  2. Write guides 01-06. Run → pass for 01-06.
  3. Write `test_presets_only_set_declared_options` (REQ-CONFIG-002): every preset option exists in a guide with an allowed value (runs fully after Track 5).
- **Acceptance criteria**: tests pass for 01-06; guides contain no vendor names in steps 01-06 (checked by `test_guides_vendor_neutral` for numbers 1-9 using vendor-terms.yaml).

### Track 5: Step guides 07-12 and the AWS profile
- **Dependencies**: Track 2
- **Requirements**: REQ-DESIGN-003, REQ-DESIGN-004, REQ-CONFIG-006
- **Provider role**: `docs`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**: create `skills/sa-design/references/steps/07-logical-view.md` … `12-adrs.md`; create `skills/sa-design/references/profiles/aws.md`; extend `tests/test_step_guides.py`.
- **Content**: same section structure as Track 4. Step-specific key questions:
  - 07 logical-view: layers (client, edge with gateway and identity provider, services, messaging and data, external); per-client API style (recommend one gateway with per-client routes); sync vs async per interaction; where data from several services is combined (recommend read models inside services).
  - 08 saga: the core multi-service flow; orchestration vs choreography (recommend orchestration for one owner of state); failure scenarios to cover (count from option), compensation per step; idempotency and outbox.
  - 09 patterns: security (identity provider, token check at the gateway, authorization in every service, secrets); observability (traces, metrics, logs, alarms); resilience (timeout, retry with backoff and jitter, circuit breaker, bulkhead, fallback).
  - 10 architecture: cloud profile mapping per logical component (from profiles/<cloud>.md); regions and availability zones; subnet tiers and which tier has internet routes; group names shared by the high-level and physical views (option).
  - 11 stack: one choice per layer with a reason; managed vs self-run.
  - 12 adrs: the 5-10 decisions a reviewer will challenge; for each: alternatives, trade-off, rationale, the pain points it addresses.
- **profiles/aws.md**: a table logical kind → AWS service with notes (gateway → API Gateway with per-client routes, VPC Link to internal ALB; identity-provider → Cognito, external IdP federated; service → ECS Fargate; broker → SNS FIFO + SQS FIFO, EventBridge Scheduler for jobs; datastore → Aurora PostgreSQL per service, ElastiCache Redis, OpenSearch, S3; edge → Route 53, CloudFront, WAF; observability → CloudWatch, X-Ray via ADOT; secrets → Secrets Manager, KMS; AI → Bedrock); default network: 1 region, 2 AZs, public/app/data tiers, data tier without internet route, VPC endpoints.
- **Steps**:
  1. Remove the skip for 07-12 in `test_guides_front_matter`; run → fail.
  2. Write guides 07-12 and the profile; run → pass; `test_presets_only_set_declared_options` now passes.
  3. Add `test_guides_vendor_neutral` coverage for 07-09; add `test_aws_profile_covers_kinds`: every logical `kind` except `client` and `external` appears in aws.md.
- **Acceptance criteria**: tests pass for all 12 guides; aws profile covers every kind.

### Track 6: /sa-design orchestrator skill
- **Dependencies**: Track 3, Track 4, Track 5
- **Requirements**: REQ-DESIGN-001, REQ-DESIGN-002, REQ-DESIGN-004, REQ-DESIGN-005, REQ-DESIGN-006, REQ-DESIGN-007, REQ-DESIGN-008, REQ-DESIGN-009, REQ-CONFIG-005, REQ-CONFIG-006
- **Provider role**: `general`
- **Reasoning**: `high`
- **Model class**: `high_reasoning`
- **Estimated complexity**: high
- **Files**: modify `skills/sa-design/SKILL.md`; create `tests/test_skill_docs.py`.
- **SKILL.md content** (sections in order):
  - front matter: `name: sa-design`; `description`: "Guided, step-by-step DDD + microservices solution design (functions, subdomains, context map, aggregates, use cases, logical view, saga, patterns, architecture, stack, ADRs). Use when designing or updating a solution architecture; resumes from design/design-state.yaml."
  - `## Locate`: find `design/` in the current project; if absent, propose `design/`, ask to confirm, copy `references/templates/sa-config.yaml` and `design-state.yaml` (REQ-DESIGN-001).
  - `## Start of every run`: run `python3 <plugin>/skills/sa-review/scripts/check.py design --changed`; for each changed file report it and run `--dependents` to name steps that may be stale (REQ-DESIGN-008); load the effective config via `check.py design --format json --step brief` header or by reading sa-config + presets; report `CONFIG` errors and stop.
  - `## Choose the step`: named step, else first `stale`, else first `todo` (REQ-DESIGN-002); if an input step is not `done`, name it and offer to run it first (REQ-DESIGN-007).
  - `## Run the step`: read only `references/steps/NN-<key>.md` and the input data files; propose at the configured option values; ask the key questions one at a time with the recommendation; write nothing until answered (REQ-DESIGN-004); vendor names only from step 10 using `references/profiles/<cloud>.md` (REQ-CONFIG-006).
  - `## Write`: write `design/NN-<key>.md` and the data file; run `check.py design --step <key>`; on `SCHEMA` findings fix and re-run before reporting the step as written (REQ-DESIGN-005).
  - `## Checklist`: show each active rule of the step (script results from `check.py --step`, judgement rules checked by reading the files) as pass/fail; each failed `error` rule is fixed or recorded in `exceptions` with the user's reason (REQ-DESIGN-009).
  - `## Record`: set status `done`, decisions, open questions, sha256 of written files in `files`; if IDs were added, removed or renamed, or an option changed, mark every `--dependents` step `stale` with `stale_reason` (REQ-DESIGN-006, REQ-CONFIG-005); stop and suggest the next step.
  - `## Changing options`: edit `sa-config.yaml` only after the user agrees; then mark the affected step and its dependents stale.
  - `## Writing style`: documents describe the solution for its audience; no review history; titles match content (DOC-01, DOC-02).
- **Steps**:
  1. Write `tests/test_skill_docs.py::test_sa_design_sections` asserting the front matter and the section headings above in order, and that every REQ-DESIGN and REQ-CONFIG-005/006 ID appears in an HTML comment `<!-- REQ-... -->` beside the section that implements it. Run → fail.
  2. Write SKILL.md. Run → pass.
  3. Manual check TC-02 and TC-03 from tests.md in a scratch project; record the result in `docs/changes/sad-3p2-sa-method-skills/tests.md` evidence column.
- **Acceptance criteria**: test passes; TC-02, TC-03 recorded.

### Track 7: /sa-review skill
- **Dependencies**: Track 3
- **Requirements**: REQ-REVIEW-001, REQ-REVIEW-003
- **Provider role**: `general`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: low
- **Files**: modify `skills/sa-review/SKILL.md`; extend `tests/test_skill_docs.py`; create `tests/test_review_report.py`; create `skills/sa-review/scripts/sacheck/review_md.py`.
- **SKILL.md content**: front matter `name: sa-review`, description "Read-only audit of a design/ folder produced by sa-design: completeness, schemas, rules, cross-step consistency and traceability; writes design/review-report.md."; sections `## Run checks` (`check.py design --format json`), `## Judgement rules` (DOC-01, DOC-02, FN-01, PT-02 and any other `check: judgement` rule: read the files and decide pass/fail with the evidence), `## Write the report` (`python3 .../check.py design --format json` piped to `review_md.py` for the skeleton, then add judgement findings), `## Never` (never edit files under `design/` other than `review-report.md`).
- **Interfaces produced**: `review_md.render(result: dict, judgement: list[dict]) -> str` producing `# Design review`, `## Configuration` (profile, cloud, options, overrides), `## Summary`, `## Errors`, `## Warnings`, `## Accepted exceptions`, `## Step status`.
- **Steps**:
  1. `tests/test_review_report.py::test_render_order` (REQ-REVIEW-001): render from the json of the `exception-accepted` fixture with `LV-01: warn` override; headings in the order above; configuration lists the override. Run → fail; implement → pass.
  2. `test_exceptions_listed_separately` (REQ-REVIEW-003): the LV-01 exception appears under `## Accepted exceptions` with its reason and not under `## Errors`.
  3. `test_sa_review_sections` in `test_skill_docs.py`.
- **Acceptance criteria**: tests pass.

### Track 8: Example design sets and neutral-content check
- **Dependencies**: Track 6, Track 7
- **Requirements**: REQ-QUALITY-003, REQ-QUALITY-004, REQ-QUALITY-005, REQ-CONFIG-002
- **Provider role**: `general`
- **Reasoning**: `medium`
- **Model class**: `standard_impl`
- **Estimated complexity**: medium
- **Files**:
  - create `examples/clinic-booking/brief.md` (fictional multi-clinic appointment booking: patients book and pay online, clinics manage doctors' schedules, reminders, insurance pre-check as an external system; 4 pain points; NFRs)
  - create `examples/clinic-booking/design/` by running `/sa-design` steps 01-12 with preset `high-level` (all files written by the skill, including `review-report.md` from `/sa-review`)
  - create `examples/food-delivery/brief.md` (fictional restaurant ordering and courier delivery) and `examples/food-delivery/design/` with steps 01-05 run
  - create `examples/food-delivery/design-detailed/` with steps 01-05 re-run under preset `detailed` (shows the difference required by the success criteria)
  - create `tests/deny-terms.txt` (one term per line, case-insensitive; initial content: `OpenTourNext`, `GiangDH19`, `SALevelUp`, `SA Level Up`, `FHN`, `assignment-work`, `instructor`; the repository owner adds terms as needed) and `tests/test_examples.py`
- **Steps**:
  1. `tests/test_examples.py::test_clinic_booking_passes` (REQ-QUALITY-003): `check.py examples/clinic-booking/design` exit 0 and all 12 steps `done`. Run → fail.
  2. Write the brief; run `/sa-design` through all 12 steps; run `/sa-review`. Run → pass.
  3. `test_food_delivery_passes` (REQ-QUALITY-004): steps 01-05 `done`, exit 0. Produce the set; run → pass.
  4. `test_detailed_differs` (REQ-CONFIG-002): `design-detailed/aggregates.yaml` has non-empty `entities` for at least one aggregate and `context-map.yaml` has `externals`; the `high-level` set has neither.
  5. `test_neutral_content` (REQ-QUALITY-005): no line of any file under `skills/` or `examples/` contains a term from `tests/deny-terms.txt` (case-insensitive). Run → pass.
  6. Manual checks TC-01, TC-04, TC-05 from tests.md; record evidence.
- **Acceptance criteria**: tests pass; manual cases recorded.

## Requirement coverage

| REQ | Track |
|---|---|
| REQ-PLUGIN-001 | 1 |
| REQ-DESIGN-001, 002, 007 | 6 |
| REQ-DESIGN-003 | 2, 4, 5 |
| REQ-DESIGN-004 | 4, 5, 6 |
| REQ-DESIGN-005 | 2, 6 |
| REQ-DESIGN-006, 008, 009 | 3, 6 |
| REQ-CONFIG-001 | 1, 4 |
| REQ-CONFIG-002 | 1, 4, 8 |
| REQ-CONFIG-003, 004 | 1 |
| REQ-CONFIG-005 | 3, 6 |
| REQ-CONFIG-006 | 5, 6 |
| REQ-REVIEW-001, 003 | 7 |
| REQ-REVIEW-002, 004, 005, 006 | 3 |
| REQ-QUALITY-001 | 1, 2 |
| REQ-QUALITY-002 | 3 |
| REQ-QUALITY-003, 004, 005 | 8 |

## Integration
- **Branch**: `feat/sa-method-skills`, created from `spec/sa-method-skills` (which carries the spec and this plan).
- **Merge strategy**: sequential. Track order: 1 → 2 → 3 → 4 → 5 → 7 → 6 → 8 (Tracks 3, 4, 5 are independent after Track 2 but run one after another in direct mode).
- Track beads close when their tests pass and the self-check review is done. The Parent Bead `sad-3p2` stays open until the user confirms the merge.

## Validation
- [ ] `pytest` passes (all tracks)
- [ ] `ruff check .` clean
- [ ] `python3 skills/sa-review/scripts/check.py examples/clinic-booking/design` exits 0
- [ ] `python3 skills/sa-review/scripts/check.py examples/food-delivery/design` exits 0
- [ ] `gin-workflow specs lint --change sad-3p2` and `gin-workflow specs trace --change sad-3p2` clean
- [ ] Manual cases TC-01 to TC-05 recorded in tests.md

## Notes
- Model guidance is planning metadata, not Beads state.
- Provider roles are portable (`backend`, `docs`, `general`); concrete models are resolved from local configuration at orchestration.
- Every new test names its REQ-ID in the test name or a comment.
