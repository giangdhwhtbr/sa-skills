---
number: 8
key: saga
title: Core flow (saga)
markdown: 08-saga.md
data: saga.yaml
schema: saga.schema.yaml
inputs: [subdomains.yaml, aggregates.yaml, logical.yaml]
options:
  failure-scenarios:
    values: [1, 2, 3]
    default: 2
    affects: "How many failure scenarios (with compensation) the saga must cover besides the happy path"
rules: [SG-01, SG-02, SG-03]
---

# Step 08 - Core flow (saga)

## Purpose

Describe the most important multi-service flow as a saga: the happy path and the failure cases with their compensation. Most user journeys are simple calls to one service; the saga covers the part that spans several services and must stay consistent without a distributed transaction.

## Inputs

- `subdomains.yaml`: the services that take part.
- `aggregates.yaml`: the roots changed at each step (each change is one local transaction).
- `logical.yaml`: sync vs async interactions and external systems.

## Propose

- Pick the core flow (usually checkout, ordering or booking) and its orchestrator: the service that owns the flow's state.
- Happy path: numbered steps. The orchestrator saves its state first, then sends commands and receives events; every command carries an idempotency key and every state change writes an outbox row in the same local transaction.
- Failure scenarios (count from the option), for example a participant rejects a step, or an external call times out with an unknown result. Each failure lists the compensation steps in reverse order, and what happens to anything that cannot be undone (dead-letter queue and an alert to the operations team).
- For an uncertain external result: never guess; keep the state pending and reconcile later with the same key.

## Key questions

1. What is the core flow and who orchestrates it? Recommended: orchestration by the service that owns the flow's state, so one place shows and recovers every instance.
2. Which failure scenarios matter most? Recommended: one business rejection (a participant says no) and one technical uncertainty (timeout with unknown result).
3. What happens when a compensation itself fails? Recommended: retry with the same idempotency key, then dead-letter queue and an alert for a person.

## Write

- `08-saga.md`: Summary, Decisions (orchestration, idempotency, outbox), Details (one numbered sequence per scenario, with the state of the flow after each), Open questions.
- `saga.yaml`: `flow` (`id`, `name`, `orchestrator`), `participants`, `scenarios` (`kind: happy|failure`, numbered `steps` with `kind: sync|async|compensate|self`).

## Checklist

- SG-01: one happy scenario and at least the configured number of failure scenarios.
- SG-02: every failure scenario contains a compensate step.
- SG-03: the orchestrator and every participant are known services or external systems.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Payment times out: the payment stays pending; a scheduled reconcile asks the provider again with the same key; paid in time -> continue, paid late -> full refund."
- Bad: "If anything fails we roll back the transaction" across four services.
