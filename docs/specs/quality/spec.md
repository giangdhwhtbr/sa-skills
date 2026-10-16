# Quality

## Purpose

## Requirements

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

### REQ-QUALITY-003: Complete worked example
The repository SHALL contain `examples/clinic-booking/` with a fictional sample brief and the design set produced by running all 12 steps of `/sa-design` on it with the `high-level` preset, and `check.py` SHALL report no errors on it.

#### Scenario: Worked example is complete
- GIVEN `examples/clinic-booking/`
- WHEN `check.py` runs on its design folder
- THEN all 12 steps are `done`, every context-map edge has U/D ends, every ADR states a trade-off, and there are no errors

### REQ-QUALITY-004: Generality trial
The repository SHALL contain `examples/food-delivery/` with a second fictional sample brief and steps 01-05 run on it, and `check.py` SHALL report no errors on it.

#### Scenario: Second domain
- GIVEN `examples/food-delivery/`
- WHEN `check.py` runs
- THEN steps 01-05 are `done` and there are no errors

### REQ-QUALITY-005: Project-independent content
The plugin's skills, references, templates and examples SHALL NOT name any real client, course, organisation or past project; examples SHALL use fictional sample briefs.

#### Scenario: Neutral content
- GIVEN the plugin repository
- WHEN a test scans `skills/` and `examples/` against a deny-list of project-specific terms kept in `tests/`
- THEN no match is found

### REQ-QUALITY-006: Example diagrams
The example design sets SHALL include generated diagrams: steps 02-10 for `examples/clinic-booking/design` and steps 02-05 for `examples/food-delivery/design` and `design-detailed`, and a test SHALL check that they are up to date with their data.

#### Scenario: Examples up to date
- GIVEN the committed examples
- WHEN the example test runs
- THEN every diagram's recorded source hash matches its data
