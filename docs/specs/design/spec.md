# Design

## Purpose

## Requirements

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
