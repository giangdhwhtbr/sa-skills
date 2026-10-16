---
number: 3
key: subdomains
title: Subdomains
markdown: 03-subdomains.md
data: subdomains.yaml
schema: subdomains.schema.yaml
inputs: [brief.yaml, functions.yaml]
options:
  service-per-subdomain:
    values: [one, allow-shared]
    default: one
    affects: "Whether every subdomain gets exactly one service (one) or several subdomains may share a service (allow-shared)"
rules: [SD-01, SD-02]
---

# Step 03 - Subdomains

## Purpose

Decompose the business domain into subdomains and classify each one, so effort goes where the business competes. With the default option, each subdomain becomes exactly one microservice; the subdomain ID is also the bounded-context ID used by every later step.

## Inputs

- `brief.yaml`: goals and pain points (which areas matter most).
- `functions.yaml`: the functions to distribute over subdomains.

## Propose

- Cluster related functions into subdomains by business capability: things that change together, share language and have one owner.
- Classify each subdomain:
  - **core**: where the business competes; build it, invest most.
  - **supporting**: needed to run the business but not a differentiator; build it simply.
  - **generic**: solved problems (identity, payment, documents); buy, reuse or integrate.
- Under `service-per-subdomain: one`, give each subdomain one service with an ID such as `ordering-service`. Under `allow-shared`, record which subdomains share a service and why.
- Put scheduled or batch work in its own supporting subdomain when several services need timed jobs, so schedules and run history have one owner.
- Map every function from step 02 to exactly one subdomain (`function_ids`). Mention in each description which pain points the subdomain helps with, by ID.

## Key questions

1. Is each subdomain correctly classified as core, supporting or generic? Recommended: apply the test "would a competitor's version of this hurt us?": yes = core; needed but ordinary = supporting; commodity = generic.
2. Should any candidate be split or merged? Recommended: split when two parts change at different speeds or have different owners (for example catalogue content and pricing rules); merge when two parts always change together.
3. One service per subdomain? Recommended: yes (`one`); it keeps ownership clear and the count easy to explain. Choose `allow-shared` only for very small teams.

## Write

- `03-subdomains.md`: Summary (count and classification), Decisions (splits and merges with reasons), Details (table: subdomain, type, service, functions, pain points addressed), Open questions.
- `subdomains.yaml`: `subdomains` with `id`, `name`, `type`, `description`, `service` (`id`, `name`), `function_ids`.

## Checklist

- SD-01: at least one subdomain is core.
- SD-02 (when `service-per-subdomain = one`): every subdomain has exactly one service and service IDs are unique.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Pricing & Promotion (core): price lists, promotions, quotes; changes weekly, owned by the revenue team; separate from Catalogue (content) because it changes faster."
- Bad: one "Business logic" subdomain holding half the functions; or a subdomain named after a technology ("Database service").
