# Spec Delta: SA method skills

## ADDED

### REQ-PLUGIN-001: Installable plugin with two skills
The repository SHALL be a Claude Code plugin whose manifest exposes exactly two skills, `sa-design` and `sa-review`, installable into any project from a local path or marketplace entry.

#### Scenario: Install into a new project
- GIVEN a project without the plugin
- WHEN the user installs the plugin from this repository
- THEN `/sa-design` and `/sa-review` are available in that project's Claude Code session

### REQ-DESIGN-001: Initialize a design folder
WHEN `/sa-design` runs in a project that has no `design/` folder, the skill SHALL create `design/` with `sa-config.yaml` (preset `high-level`, cloud `aws`) and `design-state.yaml` listing all 12 steps as `todo`, after the user confirms the location.

#### Scenario: First run
- GIVEN a project with no `design/` folder
- WHEN the user runs `/sa-design` and confirms the location
- THEN `design/sa-config.yaml` and `design/design-state.yaml` exist and every step is `todo`

### REQ-DESIGN-002: Pick the step to run
WHEN `/sa-design` runs on an existing design folder, the skill SHALL run the step the user names, or else the first step whose status is `stale` or `todo`, and SHALL load only that step's guide and the data files of the steps it depends on.

#### Scenario: Resume
- GIVEN steps 01-03 are `done` and step 04 is `todo`
- WHEN the user runs `/sa-design` without naming a step
- THEN step 04 (context map) runs and only its guide, `subdomains.yaml` and the configuration are loaded

#### Scenario: Stale before todo
- GIVEN step 05 is `stale` and step 07 is `todo`
- WHEN the user runs `/sa-design`
- THEN step 05 runs first

### REQ-DESIGN-003: Twelve steps with fixed outputs
The skill SHALL provide these steps, each writing `design/NN-<step>.md` and its data file: 01 brief intake (`brief.yaml`), 02 business functions by actor (`functions.yaml`), 03 subdomains with one service each (`subdomains.yaml`), 04 context map (`context-map.yaml`), 05 aggregate roots and ID references (`aggregates.yaml`), 06 use cases by actor (`use-cases.yaml`), 07 logical view (`logical.yaml`), 08 core-flow saga with failure cases (`saga.yaml`), 09 core patterns: security, observability, resilience (`patterns.yaml`), 10 high-level and physical architecture (`architecture.yaml`), 11 technology stack (`stack.yaml`), 12 ADRs (`adrs.yaml`).

#### Scenario: Step output
- GIVEN step 03 completes
- WHEN the user lists `design/`
- THEN `03-subdomains.md` and `subdomains.yaml` exist

### REQ-DESIGN-004: Decide before writing
WHILE a step runs, the skill SHALL first show its proposed content, then ask the step's key decisions one question at a time with a recommended option, and SHALL NOT write the step's files until the user has answered.

#### Scenario: No write without decision
- GIVEN step 04 has shown its proposed context map
- WHEN the user has not yet answered the step's questions
- THEN no file under `design/` has changed

### REQ-DESIGN-005: Valid, complete writes
WHEN a step writes its files, each data file SHALL validate against its schema; IF validation fails, THEN the skill SHALL fix the content and validate again, and SHALL NOT leave a step with only some of its files written.

#### Scenario: Schema error
- GIVEN a drafted `context-map.yaml` with an edge whose `type` is not an allowed value
- WHEN the step tries to write
- THEN the error is shown, corrected, and both `04-context-map.md` and `context-map.yaml` are written only after validation passes

### REQ-DESIGN-006: Shared identifiers and stale propagation
Every service and context reference in steps 04-12 SHALL use an ID defined in `subdomains.yaml`; WHEN a re-run step changes, adds or removes IDs, the skill SHALL mark every later step that reads them as `stale` with the reason in `design-state.yaml`.

#### Scenario: Rename a subdomain
- GIVEN steps 03-07 are `done`
- WHEN step 03 is re-run and a subdomain ID changes
- THEN steps 04-07 become `stale` with a reason naming the changed ID

### REQ-DESIGN-007: Missing prerequisite
IF the selected step depends on a step that is not `done`, THEN the skill SHALL name the missing step and offer to run it first.

#### Scenario: Context map before subdomains
- GIVEN step 03 is `todo`
- WHEN the user asks to run step 04
- THEN the skill reports that step 03 is required and offers to run it

### REQ-DESIGN-008: Manual edits
WHEN `/sa-design` starts and a design file was edited outside the skill, the skill SHALL validate it again and report any difference from the decisions recorded in `design-state.yaml` before running a step.

#### Scenario: Hand-edited YAML
- GIVEN the user added a context to `subdomains.yaml` by hand
- WHEN `/sa-design` starts
- THEN the skill reports the new context and that steps reading it may be stale

### REQ-DESIGN-009: Step checklist
WHEN a step has written its files, the skill SHALL check every rule that is active for that step under the current configuration, show pass or fail per rule, and require each failed `error` rule to be fixed or recorded as an accepted exception with a reason in `design-state.yaml`.

#### Scenario: Vendor in logical view
- GIVEN option `logical-view.vendors = none` and a logical view naming "SNS"
- WHEN step 07 runs its checklist
- THEN rule LV-01 fails and the step is not marked `done` until the name is removed or an exception is recorded

### REQ-CONFIG-001: Project configuration file
The design SHALL be configured by `design/sa-config.yaml` containing a `profile` preset (`high-level`, `detailed` or `custom`), a `cloud` profile, per-step `steps` options, and per-rule `rules` severity overrides; every option SHALL be declared with its allowed values and default in the step's guide.

#### Scenario: Unknown option value
- GIVEN `steps.context-map.detail: everything` in `sa-config.yaml`
- WHEN `/sa-design` or `/sa-review` loads the configuration
- THEN the value is rejected with the list of allowed values

### REQ-CONFIG-002: Presets
The presets SHALL expand to option values: `high-level` = context map U/D only, aggregate roots only, logical view without vendors, one view per pattern, shared layout for high-level and physical views; `detailed` = context map with external systems, aggregates with entities, value objects and events, technology hints allowed in the logical view; WHERE `custom` is selected, every option SHALL take its explicit value or its default.

#### Scenario: Detailed preset
- GIVEN `profile: detailed`
- WHEN step 05 runs
- THEN it proposes entities and value objects inside each aggregate, not roots only

### REQ-CONFIG-003: Rules catalogue
Review rules SHALL live in one `rules.yaml`, each with an ID, the step it applies to, a check statement, a default severity (`error`, `warn` or `off`), an optional condition on option values, and whether it is checked by script or by judgement.

#### Scenario: Conditional rule
- GIVEN rule CM-01 "context map shows only upstream/downstream relationships" with condition `context-map.detail = ud-only`
- WHEN the configuration sets `context-map.detail: with-externals`
- THEN CM-01 is not active

### REQ-CONFIG-004: Severity overrides
WHERE `sa-config.yaml` sets a rule's severity, that value SHALL replace the rule's default: `error` must be fixed or excepted, `warn` is reported only, `off` is skipped.

#### Scenario: Downgrade a rule
- GIVEN `rules: { LV-01: warn }`
- WHEN the logical view names a vendor
- THEN LV-01 is reported as a warning and step 07 can be marked `done`

### REQ-CONFIG-005: Option change makes steps stale
WHEN an option or the preset changes, the steps that read that option and the steps depending on them SHALL be marked `stale` with the reason.

#### Scenario: Aggregates detail raised
- GIVEN step 05 is `done` with `aggregates.detail: roots-only`
- WHEN the option changes to `full`
- THEN step 05 becomes `stale`

### REQ-CONFIG-006: Cloud profile
Steps 01-09 SHALL stay vendor-neutral by default, and step 10 (architecture) and step 11 (stack) SHALL map logical components to services from the configured cloud profile; the plugin SHALL ship an `aws` profile.

#### Scenario: AWS mapping
- GIVEN `cloud: aws` and a logical "message broker"
- WHEN step 10 runs
- THEN it proposes an AWS service for it (for example SNS + SQS) and records the mapping in `architecture.yaml`

### REQ-REVIEW-001: Read-only report
WHEN `/sa-review` runs, it SHALL NOT modify design files and SHALL write `design/review-report.md` that starts with the effective configuration (preset, options, overrides), followed by findings with errors first, and SHALL print a short summary in chat.

#### Scenario: Report header
- GIVEN a design set with `profile: high-level` and `LV-01: warn`
- WHEN `/sa-review` runs
- THEN the report header lists the preset, the options and the LV-01 override, and no design file changed

### REQ-REVIEW-002: Completeness and schemas
The review SHALL report each step's status and, for each `done` step, whether its files exist and validate against their schemas.

#### Scenario: Missing file
- GIVEN step 06 is `done` but `use-cases.yaml` was deleted
- WHEN `/sa-review` runs
- THEN it reports an error for step 06

### REQ-REVIEW-003: Rules and exceptions
The review SHALL check every active rule across all steps and SHALL list accepted exceptions separately with their reasons.

#### Scenario: Exception listed
- GIVEN rule LV-01 failed and was accepted as an exception in step 07
- WHEN `/sa-review` runs
- THEN the report lists LV-01 under accepted exceptions with its reason, not as an error

### REQ-REVIEW-004: Cross-step consistency
The review SHALL report as errors: a reference to an unknown service or context ID; a context-map edge whose end is not a known context; an aggregate root without a subdomain; a service in the architecture that is not in the logical view; and a service count that differs between documents.

#### Scenario: Unknown reference
- GIVEN `saga.yaml` names a participant `pricing-svc` that is not in `subdomains.yaml`
- WHEN `/sa-review` runs
- THEN it reports an error naming `saga.yaml` and `pricing-svc`

### REQ-REVIEW-005: Traceability
The review SHALL report every pain point in `brief.yaml` that no design element or ADR addresses, and every ADR without a stated trade-off.

#### Scenario: ADR without trade-off
- GIVEN an ADR whose `tradeoff` field is empty
- WHEN `/sa-review` runs
- THEN it reports that ADR

### REQ-REVIEW-006: Mechanical checks script
The schema, reference, consistency, traceability and script-checked rules SHALL be implemented in `skills/sa-review/scripts/check.py`, which takes a design folder, prints findings, and exits 0 when there are no errors and 1 when there is at least one error.

#### Scenario: Exit code
- GIVEN a design folder with one broken reference
- WHEN `python check.py design/` runs
- THEN it prints the finding and exits 1

### REQ-QUALITY-001: Static tests
The test suite SHALL check that every template validates against its schema, every rule in `rules.yaml` has an ID, step, severity and valid condition, and every option referenced by a rule is declared by its step.

#### Scenario: Bad rule
- GIVEN a rule with severity `fatal`
- WHEN `pytest` runs
- THEN a test fails naming the rule

### REQ-QUALITY-002: Fault fixtures
The test suite SHALL include design-set fixtures with known faults (broken reference, vendor in the logical view, ADR without trade-off, missing step file) and a clean fixture, and SHALL assert that `check.py` reports exactly the expected findings for each.

#### Scenario: Clean fixture
- GIVEN the clean fixture
- WHEN `check.py` runs on it
- THEN it reports no errors and exits 0

### REQ-QUALITY-003: Golden replay
The repository SHALL contain `examples/opentournext/`, the design set produced by running `/sa-design` on the OpenTourNext brief with the `high-level` preset, and `check.py` SHALL report no errors on it.

#### Scenario: Replay matches decisions
- GIVEN `examples/opentournext/`
- WHEN its data files are read
- THEN they contain 11 subdomains with one service each, a context map with U/D on every edge, aggregate roots with ID references, a saga with a happy path and two failure cases, and 8 ADRs each with a trade-off

### REQ-QUALITY-004: Generality trial
The repository SHALL contain `examples/clinic-booking/` with steps 01-05 run on a second sample brief, and `check.py` SHALL report no errors on it.

#### Scenario: Second brief
- GIVEN `examples/clinic-booking/`
- WHEN `check.py` runs
- THEN steps 01-05 are `done` and there are no errors

## MODIFIED

## REMOVED
