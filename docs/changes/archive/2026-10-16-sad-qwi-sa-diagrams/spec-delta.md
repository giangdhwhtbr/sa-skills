# Spec Delta: SA diagrams

## ADDED

### REQ-DIAGRAMS-001: Diagrams skill and CLI
The plugin SHALL provide a skill `sa-diagrams` and a CLI `skills/sa-diagrams/scripts/diagrams.py DESIGN_DIR [--only KEY ...] [--png]` that reads a design folder and writes diagrams into `DESIGN_DIR/diagrams/` without modifying any other file of the design folder.

#### Scenario: Diagrams written, design untouched
- GIVEN a design folder whose steps 02-10 are `done` with no errors
- WHEN `diagrams.py design` runs
- THEN `design/diagrams/` contains the diagram files and no other file under `design/` changed

### REQ-DIAGRAMS-002: Valid data first
WHEN a run starts, the CLI SHALL run the design checks and, IF any step to be drawn has an error finding, THEN it SHALL write nothing, name the step and exit 1; warnings SHALL NOT stop the run.

#### Scenario: Broken reference
- GIVEN `saga.yaml` names an unknown participant
- WHEN `diagrams.py design` runs
- THEN it exits 1, names the saga step and writes no diagram

### REQ-DIAGRAMS-003: Steps drawn
The CLI SHALL draw every step whose status is `done` among steps 02-10, or only the steps given with `--only`, and SHALL list skipped steps (`todo`, `stale`, or not drawable) in its summary.

#### Scenario: Partial design
- GIVEN steps 01-05 are `done` and steps 06-12 are `todo`
- WHEN `diagrams.py design` runs
- THEN diagrams for steps 02-05 are written and steps 06-10 are listed as skipped

### REQ-DIAGRAMS-004: Output files
For each drawn step the CLI SHALL write `NN-<key>.drawio` and `NN-<key>.mermaid.md`, and SHALL write `all-diagrams.drawio` containing every page of every drawn step in step order.

#### Scenario: Consolidated file
- GIVEN steps 02 and 03 are drawn
- WHEN the run ends
- THEN `all-diagrams.drawio` has the pages of `02-functions.drawio` followed by those of `03-subdomains.drawio`

### REQ-DIAGRAMS-005: Diagram content per step
Each diagram SHALL show every item of its source data: step 02 every function in bands by actor group; step 03 every subdomain in core/supporting/generic bands with its service; step 04 every relationship as an arrow from upstream to downstream with U and D markers; step 05 every aggregate root and every reference with its ID field and multiplicity; step 06 every use case with its actors, one page per actor group; step 07 every component in its layer and every flow with its label; step 08 one sequence page per scenario with every step as a numbered message and compensations marked; step 09 one page each for security, observability and resilience with numbered steps; step 10 a high-level view and a physical/network view containing every service, data store, external system and network tier.

#### Scenario: Context map completeness
- GIVEN a context map with 8 relationships
- WHEN step 04 is drawn
- THEN the diagram has 8 arrows, each with a U marker at the upstream end and a D marker at the downstream end

### REQ-DIAGRAMS-006: Options respected
Diagrams SHALL follow the effective configuration: external systems appear on the context map only WHERE `context-map.detail = with-externals`; entities, value objects and events appear on aggregates only WHERE `aggregates.detail = full`; the logical view names no vendor WHERE `logical-view.vendors = none`.

#### Scenario: Detailed aggregates
- GIVEN `aggregates.detail = full` and an aggregate with entities
- WHEN step 05 is drawn
- THEN the entities appear inside that aggregate's boundary

### REQ-DIAGRAMS-007: Shared architecture skeleton
WHERE `architecture.shared-layout = true`, the high-level and physical views SHALL be laid out on one skeleton computed from the data: the same groups in the same order and positions, and the services in the same grid order in both views, for any number of services.

#### Scenario: Aligned views at different sizes
- GIVEN designs with 3, 8 and 15 services
- WHEN step 10 is drawn for each
- THEN in each design the group positions and the service order are identical in both views

### REQ-DIAGRAMS-008: One style
Every diagram SHALL use one shared style: the same fill per subdomain type (core, supporting, generic), the same marking for the scheduling service and the identity provider, the same arrow style per interaction kind (sync, async, auth, data, external), and a legend that lists only the styles used on that page.

#### Scenario: Legend matches the page
- GIVEN a page with sync and async arrows only
- WHEN it is drawn
- THEN its legend lists sync and async arrows and no other arrow kind

### REQ-DIAGRAMS-009: Readable layout
No two nodes on a page SHALL overlap, nodes inside a group SHALL stay inside its bounds, and IF a page would hold more than 40 nodes, THEN it SHALL be split into pages by group.

#### Scenario: Large use-case set
- GIVEN 50 use cases across three actor groups
- WHEN step 06 is drawn
- THEN there is one page per actor group and no page has overlapping nodes

### REQ-DIAGRAMS-010: Graph layout through elkjs
Graph-shaped diagrams (context map, aggregates, use cases) SHALL be laid out with elkjs through Node; IF a step to be drawn needs elkjs and Node or elkjs is not available, THEN the CLI SHALL write nothing, print the install command, and exit 2; runs that draw only other steps SHALL NOT need Node.

#### Scenario: Node missing
- GIVEN `node` is not on the PATH and step 04 is to be drawn
- WHEN `diagrams.py design` runs
- THEN it exits 2 and prints the `npm install` command for `skills/sa-diagrams/tools`

#### Scenario: No graph diagram requested
- GIVEN `node` is not on the PATH
- WHEN `diagrams.py design --only functions subdomains` runs
- THEN both diagrams are written and the exit code is 0

### REQ-DIAGRAMS-011: Optional PNG export
WHEN `--png` is given and the draw.io desktop CLI is found, the CLI SHALL export one PNG per page to `diagrams/png/`, with a timeout, at most two retries, and a cache keyed by page content; IF the draw.io CLI is not found, THEN it SHALL still write the draw.io and Mermaid files, warn, and exit 0.

#### Scenario: draw.io not installed
- GIVEN no draw.io CLI on the machine
- WHEN `diagrams.py design --png` runs
- THEN the `.drawio` and `.mermaid.md` files are written, a warning names the missing CLI, and the exit code is 0

### REQ-DIAGRAMS-012: Incremental runs
Each diagram file SHALL record the hash of the data files it was drawn from; WHEN a run finds the recorded hash equal to the current one, it SHALL NOT rewrite that diagram.

#### Scenario: One file changed
- GIVEN all diagrams are up to date
- WHEN `context-map.yaml` changes and the CLI runs
- THEN only the diagrams that read `context-map.yaml` are rewritten

### REQ-DIAGRAMS-013: Mermaid twins
Each Mermaid twin SHALL contain one fenced `mermaid` block per page, a `flowchart` for structure diagrams and a `sequenceDiagram` for saga pages, naming the same nodes and edges as the draw.io page.

#### Scenario: Saga twin
- GIVEN a saga with three scenarios
- WHEN step 08 is drawn
- THEN `08-saga.mermaid.md` has three `sequenceDiagram` blocks

### REQ-REVIEW-007: Out-of-date diagrams
The rule catalogue SHALL include DG-01 (severity `warn`, checked by script): a diagram in `design/diagrams/` whose recorded source hash differs from the current data is reported as out of date.

#### Scenario: Data changed after drawing
- GIVEN diagrams were drawn and `subdomains.yaml` changed afterwards
- WHEN `check.py design` runs
- THEN it reports DG-01 as a warning for `03-subdomains.drawio`

### REQ-QUALITY-006: Example diagrams
The example design sets SHALL include generated diagrams: steps 02-10 for `examples/clinic-booking/design` and steps 02-05 for `examples/food-delivery/design` and `design-detailed`, and a test SHALL check that they are up to date with their data.

#### Scenario: Examples up to date
- GIVEN the committed examples
- WHEN the example test runs
- THEN every diagram's recorded source hash matches its data

## MODIFIED

## REMOVED
