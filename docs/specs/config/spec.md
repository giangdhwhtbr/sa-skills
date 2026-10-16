# Config

## Purpose

## Requirements

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
