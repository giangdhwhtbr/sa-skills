# Review

## Purpose

## Requirements

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

### REQ-REVIEW-007: Out-of-date diagrams
The rule catalogue SHALL include DG-01 (severity `warn`, checked by script): a diagram in `design/diagrams/` whose recorded source hash differs from the current data is reported as out of date.

#### Scenario: Data changed after drawing
- GIVEN diagrams were drawn and `subdomains.yaml` changed afterwards
- WHEN `check.py design` runs
- THEN it reports DG-01 as a warning for `03-subdomains.drawio`
