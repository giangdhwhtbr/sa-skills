---
number: 6
key: use-cases
title: Use cases
markdown: 06-use-cases.md
data: use-cases.yaml
schema: use-cases.schema.yaml
inputs: [brief.yaml, functions.yaml]
options: {}
rules: [UC-01]
---

# Step 06 - Use cases

## Purpose

Describe what each actor does with the system, as use cases inside the system boundary, with the external systems that take part. Use cases connect the business functions (step 02) to the behaviour the architecture must support, and they are the basis of the use case view.

## Inputs

- `brief.yaml`: actors (people and external systems).
- `functions.yaml`: the functions each use case realises.

## Propose

- For each person actor, 4-12 use cases named as goals ("Book a slot", "Cancel and get a refund"), each linked to the functions it realises.
- `includes` for steps every run needs (for example "Verify email" included by "Check out as guest"); `extends` for optional variations ("Apply voucher" extends "Check out").
- External system actors take part where they act (payment provider in "Pay online").
- Separate diagrams or sections per actor group (customer, staff) keep each view readable.

## Key questions

1. Are these the use cases each actor needs? Recommended: cover every function from step 02 at least once; drop use cases no actor starts.
2. Which steps are includes or extensions? Recommended: use `includes` only for steps every run needs and `extends` for optional ones; avoid deep chains.
3. Which external systems take part? Recommended: show an external system only in the use cases where it really acts.

## Write

- `06-use-cases.md`: Summary, Decisions, Details (one section per actor group: use case, functions, external systems, include/extend), Open questions.
- `use-cases.yaml`: `use_cases` with `id`, `name`, `actor_ids`, `function_ids`, `includes`, `extends`.

## Checklist

- UC-01: every use case has an actor from `brief.yaml` and refers to known functions.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Customer: Book a slot (functions: search-slots, book-slot; includes Verify email; payment provider takes part)."
- Bad: "Use case: Database update" - not a goal of any actor.
