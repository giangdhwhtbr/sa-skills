# SA method skills: /sa-design and /sa-review

Epic: sad-3p2
Date: 2026-10-16

## Why

The OpenTourNext assignment (`../GiangDH19/assignment-work-v4`) produced a full DDD + microservices solution design: business functions, subdomains, context map, aggregate roots, use cases, logical view, booking saga, core patterns, high-level and physical views, tech stack and ADRs, plus a 23-slide deck. Most of the value came from the *method* and from the instructor's review lessons (title matches content, context map shows only upstream/downstream, high-level design shows aggregate roots only, logical view has no vendors, one slide per pattern, architecture and physical views share one layout, notes present the solution and not the review history). Today that knowledge lives in one project's files and in a long chat. A new project would have to rediscover it.

This change packages the method as a reusable Claude Code plugin that guides a solution architect through the design step by step and audits the result. It is sub-project 1 of 3; diagram/deck tools (2) and the knowledge base (3) follow as separate changes.

## What Changes

- A Claude Code plugin in this repository with two skills:
  - `/sa-design`: a stateful, guided design process of 12 steps. Each step proposes content, asks the key decisions one at a time, writes a Markdown document and a YAML data file into the target project's `design/` folder, runs its checklist, and records progress.
  - `/sa-review`: a read-only audit of a design set (completeness, schemas, rules, cross-step consistency, traceability) that writes `design/review-report.md`.
- Configurable detail: a project file `design/sa-config.yaml` selects a preset (`high-level`, `detailed`, `custom`), per-step options (for example context-map detail, logical-view vendor names, aggregate detail) and rule severity overrides. Review rules live in one `rules.yaml` with IDs, severities and option conditions.
- A cloud-agnostic core with AWS as the first cloud profile.
- A Python check script for the mechanical checks, pytest tests, and two example design sets: the OpenTourNext replay (golden reference) and a short trial on a second sample brief.

## Capabilities Affected

- `plugin`: plugin packaging and installation.
- `design`: the `/sa-design` guided process.
- `config`: presets, step options, rules and cloud profiles.
- `review`: the `/sa-review` audit.
- `quality`: tests and example design sets.

## Non-goals

- Drawing diagrams (draw.io, Mermaid) or building slide decks; that is sub-project 2.
- Effort, cost and schedule estimation, pattern catalogue and defence Q&A library; that is sub-project 3.
- Architecture styles other than DDD + microservices (modular monolith, serverless-first).
- Cloud profiles other than AWS.
- Per-step slash commands (for example `/sa-context-map`); steps are run through `/sa-design`.

## Success Criteria

- Running `/sa-design` on the OpenTourNext brief with the `high-level` preset reproduces the final design decisions (11 subdomains with one service each, the U/D context map, aggregate roots with ID references, the layered logical view, the booking saga with two failure cases, the eight ADRs) as Markdown + YAML in `examples/opentournext/`, and `check.py` reports no errors on it.
- Steps 01-05 run on a second sample brief (`examples/clinic-booking/`) and pass the checks, proving the method is not tied to OpenTourNext.
- Switching the preset to `detailed` changes what steps propose (for example entities and value objects in aggregates, external systems on the context map) and which rules are active, without editing the skills.
- `pytest` passes.
