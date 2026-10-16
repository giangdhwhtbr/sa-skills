# SA diagrams: /sa-diagrams

Epic: sad-qwi
Date: 2026-10-16

## Why

`/sa-design` produces a complete design as Markdown and YAML, but reviewers and audiences understand an architecture through diagrams: the domain decomposition, the context map, the logical view, the core flow as a sequence, the core patterns, and the high-level and physical views. Drawing these by hand takes days, drifts from the data as soon as a step changes, and makes it easy to break the review rules the design already follows (for example a context map that shows only upstream/downstream, or high-level and physical views that share one layout). Because every step already writes structured YAML, the diagrams can be generated from it, kept in step with the design, and re-drawn in seconds.

This is sub-project 2a. A slide-deck tool that uses these diagrams (sub-project 2b) follows as a separate change.

## What Changes

- A third skill in the plugin, `/sa-diagrams`, with a CLI `diagrams.py` that reads a design folder and writes, for every drawn step, an editable draw.io file and a Mermaid twin into `design/diagrams/`, plus `all-diagrams.drawio` with every page in step order.
- Diagrams for steps 02-10: main business functions, domain decomposition, context map with U/D markers, aggregate roots and ID references, use cases per actor group, layered logical view, one saga sequence per scenario, one page per core pattern, and the high-level architecture and physical/network views on one shared skeleton sized from the data.
- One shared style (palette, arrow kinds, legend and notes block) for every diagram.
- Layout by diagram kind: elkjs (through Node) for graph-shaped diagrams, computed bands and grids in Python, a shared architecture skeleton, and a sequence renderer for the saga.
- Optional PNG export through the draw.io desktop CLI, with timeout, retries and a content-hash cache.
- Incremental runs: each diagram records the hash of its source data, so unchanged diagrams are not rewritten and out-of-date diagrams can be detected.
- A new `/sa-review` warning rule, DG-01, for diagrams that are out of date with their data.
- Generated diagrams for the existing example design sets.

## Capabilities Affected

- `diagrams`: the new `/sa-diagrams` skill and its CLI.
- `review`: rule DG-01.
- `quality`: example diagrams and tests.

## Non-goals

- Slide decks, speaker notes, HTML or PPTX output; that is sub-project 2b.
- Diagrams for step 01 (brief), step 11 (stack) and step 12 (ADRs), which are tables, not diagrams.
- Editing design data from a diagram (diagrams are output only).
- Image formats other than PNG, and themes other than the one shared style.
- Cloud icon sets other than AWS for the physical view.

## Success Criteria

- `/sa-diagrams` generates the diagrams of steps 02-10 for `examples/clinic-booking` and of steps 02-05 for `examples/food-delivery/design` and `design-detailed`; they are committed with the examples.
- The `detailed` food-delivery set shows external systems on the context map and entities inside the aggregates; the `high-level` set shows neither.
- The high-level and physical views of clinic-booking use the same groups in the same order and the same service grid.
- Every generated draw.io file is valid and every ID of the source data appears on its diagram.
- `pytest` and `ruff check .` pass, and the plugin still names no real client, course, organisation or past project.
