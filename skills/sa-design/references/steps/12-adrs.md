---
number: 12
key: adrs
title: Architecture decisions
markdown: 12-adrs.md
data: adrs.yaml
schema: adrs.schema.yaml
inputs: [brief.yaml, functions.yaml, subdomains.yaml, context-map.yaml, aggregates.yaml, use-cases.yaml, logical.yaml, saga.yaml, patterns.yaml, architecture.yaml, stack.yaml]
options: {}
rules: [AD-01, TR-01]
---

# Step 12 - Architecture decisions

## Purpose

Record the decisions a reviewer will challenge, each with the alternatives considered and the trade-off accepted, and check that every pain point from the brief is answered. This closes the design: each decision stands on its own for a reader who did not follow the discussion.

## Inputs

- `brief.yaml`: pain points that must each be addressed.
- All earlier data files: the decisions they contain (decomposition, saga style, consistency, data ownership, compute and messaging, entry point, AI limits, batch jobs).

## Propose

- 5-10 decisions, for example: one service per subdomain; orchestrated saga; outbox and idempotency instead of two-phase commit; database per service; managed compute and messaging; one API gateway with per-client routes; read-only AI with human approval; one service for scheduled jobs.
- For each: the decision, the alternatives (at least one), the trade-off accepted (what we give up) and the rationale (why we accept it), and the pain points it answers.
- Phrase each decision against real alternatives, not against earlier drafts of this design.

## Key questions

1. Which decisions will reviewers challenge? Recommended: every choice that has a well-known alternative or a visible cost.
2. What do we give up with each decision? Recommended: name the cost plainly (more services to run, eventual consistency, no cross-service joins).
3. Is every pain point answered? Recommended: each pain point appears in at least one ADR or subdomain description.

## Write

- `12-adrs.md`: Summary, then one section per ADR (decision, alternatives, trade-off, rationale, pain points), Open questions.
- `adrs.yaml`: `adrs` with `id`, `title`, `decision`, `alternatives`, `tradeoff`, `rationale`, `status`, `pain_points`.

## Checklist

- AD-01: every ADR has at least one alternative and a non-empty trade-off.
- TR-01: every pain point in `brief.yaml` is referenced by an ADR or a subdomain description.
- DOC-01, DOC-02 (judgement): each ADR stands on its own; none says "instead of the earlier version".

## Good and bad

- Good: "One API gateway as the only entry point, with web and mobile routes; instead of clients calling services directly or a GraphQL layer; trade-off: no response composition at the edge; read models combine data."
- Bad: "We removed the extra layer from the previous draft" - history, not a decision.
