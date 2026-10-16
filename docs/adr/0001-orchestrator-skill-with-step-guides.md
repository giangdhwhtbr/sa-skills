# Orchestrator skill with step guides for the SA method

Date: 2026-10-16
Status: proposed

## Context

The solution-design method has 12 steps (brief intake to ADRs), shares one data schema, one naming scheme and one rules catalogue, and is used in a guided, stateful way: resume, re-run a step, mark later steps stale. Options considered: one skill per step (about 12 commands), four phase skills, or one orchestrator skill that loads one step guide at a time.

## Decision

Ship two skills: `/sa-design`, an orchestrator that tracks progress in `design/design-state.yaml` and loads only the current step's guide from `references/steps/`, and `/sa-review`, a read-only audit. Step guides, schemas, presets and `rules.yaml` are reference files shared by both skills.

## Consequences

- Two commands to learn; the context per run stays small because only one step guide loads.
- One source of truth for schemas, rules and step dependencies; less drift than 12 separate skills.
- A step cannot be invoked as its own slash command; users say "run step 4" instead. Per-step commands can be added later if needed.
