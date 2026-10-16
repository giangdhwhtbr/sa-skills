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

# Step 04 - Context map

## Purpose

Show how the bounded contexts depend on each other: for every relationship, which context is upstream (provides the model or data) and which is downstream (consumes it). The map makes coupling visible and tells teams whose contracts must stay stable. At high-level detail it holds no design details such as sagas, protocols or external integrations.

## Inputs

- `subdomains.yaml`: the contexts (one per subdomain) and their descriptions.

## Propose

- For each pair of contexts that interact, one relationship with `upstream`, `downstream` and a `pattern`:
  - `customer-supplier`: the downstream team's needs shape the upstream API.
  - `open-host-service` / `published-language`: the upstream offers one stable API or event schema to many consumers.
  - `domain-events`: the upstream publishes events the downstream consumes.
  - `conformist`, `anti-corruption-layer`, `partnership`, `shared-kernel` when they apply.
- Arrow direction is always upstream -> downstream. Mark each end with U and D in the document.
- By option:
  - `ud-only`: relationships between our contexts only; the pattern is recorded but the document only needs U/D and a short label.
  - `with-patterns`: the document names the pattern on every edge.
  - `with-externals`: also add `externals` (payment provider, identity provider, ERP) with direction, each behind an anti-corruption layer on our side.
- Name the most connected context (often the one that orchestrates the core flow) and say why its upstreams must keep stable contracts.

## Key questions

1. For each dependency, who is upstream? Recommended: the context that owns the data or rule is upstream; the one that needs it is downstream.
2. Should the map show relationship patterns or external systems? Recommended: keep `ud-only` for a high-level design; use `with-externals` only when integration risk is a main concern of the review.
3. Is any relationship two-way? Recommended: avoid it; split it into a command one way and events the other way, so each edge has one upstream.

## Write

- `04-context-map.md`: Summary (the most connected contexts), Decisions (direction choices that were not obvious), Details (relationship table: upstream, downstream, pattern, label), Open questions.
- `context-map.yaml`: `relationships` (`upstream`, `downstream`, `pattern`, `label`); `externals` only when `detail = with-externals`.

## Checklist

- CM-01 (when `detail = ud-only`): no external systems on the map.
- CM-02: every relationship end is a known context, and upstream differs from downstream.
- CM-03: every context appears in at least one relationship.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Pricing (U) -> Ordering (D), customer-supplier: Ordering takes an authoritative quote at checkout."
- Bad: a context map with saga steps, protocols and the external payment provider on it when the design is high level.
