---
number: 11
key: stack
title: Technology stack
markdown: 11-stack.md
data: stack.yaml
schema: stack.schema.yaml
inputs: [architecture.yaml]
options: {}
rules: [ST-01]
---

# Step 11 - Technology stack

## Purpose

Choose one technology per layer and give the reason, so the development view is clear and each choice can be defended. Prefer managed services so the team spends less time running infrastructure.

## Inputs

- `architecture.yaml`: the cloud services already chosen; the stack must agree with them.
- The brief's constraints (team skills, mandated platforms).

## Propose

One row per layer, each with a choice and a reason:
- **Clients**: web, mobile and admin frameworks; prefer one language across clients when one team owns them.
- **Edge**: gateway, identity, CDN and firewall from the architecture.
- **Services**: language and framework; strong transaction support matters for the saga and outbox.
- **API contract**: contract-first API descriptions and generated clients.
- **Messaging**: broker and dead-letter handling.
- **Data**: database per service, cache, search, object storage.
- **Compute**: container platform and auto scaling.
- **Observability** and **Security**: from the patterns.
- **AI** (if the brief asks for it): managed models and the rules that keep them read-only.

## Key questions

1. Managed or self-run for each layer? Recommended: managed, unless a constraint or a cost limit at scale says otherwise.
2. Which language for the services? Recommended: one the team already knows, with mature libraries for transactions, resilience and tracing.
3. Does any choice add a second runtime or skill set? Recommended: avoid it unless a layer really needs it, and say why in the reason.

## Write

- `11-stack.md`: Summary, Decisions, Details (table: layer, choice, reason), Open questions.
- `stack.yaml`: `layers` with `id`, `name`, `choice`, `reason`.

## Checklist

- ST-01: every layer has a choice and a reason.
- DOC-01, DOC-02 (judgement): the reasons are about the solution, not about who preferred what.

## Good and bad

- Good: "Messaging: managed FIFO topics and queues with dead-letter queues - ordered per order, no brokers to run."
- Bad: "Services: the framework the current team likes" - a reason about people, not about the system.
