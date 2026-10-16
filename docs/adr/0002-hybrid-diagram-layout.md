# Hybrid layout by diagram kind for generated diagrams

Date: 2026-10-16
Status: proposed

## Context

`/sa-diagrams` must draw nine kinds of diagram from design YAML for any project size. Options considered: one auto-layout engine (elkjs) for everything; fixed templates with slots; or a layout per diagram kind.

## Decision

Use elkjs (through Node) for graph-shaped diagrams (context map, aggregate roots, use cases); computed bands and grids in Python for functions, subdomains, the logical view and pattern chains; one shared skeleton, sized from the data, for the high-level and physical architecture views; and a dedicated sequence renderer for saga scenarios.

## Consequences

- Each diagram kind gets the layout that reads best; the high-level and physical views stay aligned for any number of services.
- Three layout techniques to maintain instead of one.
- Node and elkjs become a dependency of `/sa-diagrams` (not of `/sa-design` or `/sa-review`).
