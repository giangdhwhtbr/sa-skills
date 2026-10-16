---
number: 5
key: aggregates
title: Aggregate roots
markdown: 05-aggregates.md
data: aggregates.yaml
schema: aggregates.schema.yaml
inputs: [subdomains.yaml, context-map.yaml]
options:
  detail:
    values: [roots-only, full]
    default: roots-only
    affects: "roots-only = aggregate roots and the ID references between them; full = also entities, value objects and domain events"
rules: [AG-01, AG-02, AG-03]
---

# Step 05 - Aggregate roots

## Purpose

Identify the aggregate root of each subdomain: the single entry point that protects its business rules and changes in one local transaction. Then show how roots refer to each other: always by ID, never by holding the other object. This keeps services independent and tells the saga (step 08) where consistency must come from events.

## Inputs

- `subdomains.yaml`: one or more roots per subdomain.
- `context-map.yaml`: relationships suggest which roots reference which.

## Propose

- One root per subdomain in most cases; two when a subdomain has two independent lifecycles (for example price lists and promotions, or staff accounts and guest access).
- A subdomain that only builds read models (reporting) gets a `no_aggregate` entry with the reason.
- References between roots: `from` holds the ID of `to` (`via` = the ID field, `multiplicity` such as `* : 1`). The most connected root (usually the one at the centre of the core flow) is the hub.
- By option:
  - `roots-only`: roots and references only; leave `entities`, `value_objects` and `events` empty. Entities and value objects are low-level design.
  - `full`: for each root, list its entities, value objects and the domain events it raises.

## Key questions

1. Is this the right root for each subdomain? Recommended: the root is the thing whose rules must hold in one transaction (an order and its lines, a departure and its capacity), not every noun.
2. Does any subdomain need two roots, or none? Recommended: two only for truly independent lifecycles; none for read-model-only subdomains, with the reason recorded.
3. How do roots refer to each other? Recommended: by ID only, with the multiplicity; never embed another root's data.

## Write

- `05-aggregates.md`: Summary (roots and the hub), Decisions (two-root or no-root subdomains), Details (table: subdomain, root(s); reference list with multiplicities; under `full` also entities, value objects, events), Open questions.
- `aggregates.yaml`: `aggregates`, `references`, `no_aggregate`.

## Checklist

- AG-01 (when `detail = roots-only`): entities, value objects and events are empty.
- AG-02: every aggregate belongs to a known subdomain; every reference joins two known aggregates by an ID field.
- AG-03: every subdomain has an aggregate or a `no_aggregate` entry with a reason.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Order (root, Ordering) holds `customerId` and `quoteId`; Payment (root, Payments) holds `orderId` (`* : 1`)."
- Bad: Order contains the full Customer and Payment objects, so one transaction spans three services.
