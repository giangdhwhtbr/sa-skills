# SA method skills: /sa-design and /sa-review

Epic: sad-3p2
Date: 2026-10-16

## Why

Designing a DDD + microservices solution follows a repeatable path: business functions, subdomains, context map, aggregate roots, use cases, logical view, the core flow as a saga, the core patterns (security, observability, resilience), high-level and physical views, technology stack and architecture decisions. Most of the quality comes from the method and from a small set of review rules, for example: each diagram shows what its title promises; a context map shows upstream/downstream relationships; a high-level design shows aggregate roots rather than every entity; a logical view stays free of vendor names; each core pattern gets its own view; the high-level and physical views share one layout so readers can map blocks between them; presentation notes describe the solution, not how the design evolved. Without a shared method, every architect rediscovers this path and these rules, and reviews catch the same issues again.

This change packages the method as a reusable, project-independent Claude Code plugin that guides a solution architect through the design step by step and audits the result. It is sub-project 1 of 3; diagram/deck tools (2) and a knowledge base (3) follow as separate changes.

## What Changes

- A Claude Code plugin in this repository with two skills:
  - `/sa-design`: a stateful, guided design process of 12 steps. Each step proposes content, asks the key decisions one at a time, writes a Markdown document and a YAML data file into the target project's `design/` folder, runs its checklist, and records progress.
  - `/sa-review`: a read-only audit of a design set (completeness, schemas, rules, cross-step consistency, traceability) that writes `design/review-report.md`.
- Configurable detail: a project file `design/sa-config.yaml` selects a preset (`high-level`, `detailed`, `custom`), per-step options (for example context-map detail, logical-view vendor names, aggregate detail) and rule severity overrides. Review rules live in one `rules.yaml` with IDs, severities and option conditions.
- A cloud-agnostic core with AWS as the first cloud profile.
- A Python check script for the mechanical checks, pytest tests, and two example design sets built from fictional sample briefs: a complete worked example (clinic booking) and a short trial on a second domain (food delivery).

## Capabilities Affected

- `plugin`: plugin packaging and installation.
- `design`: the `/sa-design` guided process.
- `config`: presets, step options, rules and cloud profiles.
- `review`: the `/sa-review` audit.
- `quality`: tests and example design sets.

## Non-goals

- Drawing diagrams (draw.io, Mermaid) or building slide decks; that is sub-project 2.
- Effort, cost and schedule estimation, pattern catalogue and review Q&A library; that is sub-project 3.
- Architecture styles other than DDD + microservices (modular monolith, serverless-first).
- Cloud profiles other than AWS.
- Per-step slash commands (for example `/sa-context-map`); steps are run through `/sa-design`.

## Success Criteria

- Running `/sa-design` on the clinic-booking sample brief with the `high-level` preset produces a complete design set (all 12 steps) in `examples/clinic-booking/`, and `check.py` reports no errors on it.
- Steps 01-05 run on the food-delivery sample brief (`examples/food-delivery/`) and pass the checks, showing the method is not tied to one domain.
- Switching the preset to `detailed` changes what steps propose (for example entities and value objects in aggregates, external systems on the context map) and which rules are active, without editing the skills.
- The plugin contains no references to any specific client, course or past project.
- `pytest` passes.
