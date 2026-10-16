---
number: 1
key: brief
title: Brief intake
markdown: 01-brief.md
data: brief.yaml
schema: brief.schema.yaml
inputs: []
options: {}
rules: [BR-01]
---

# Step 01 - Brief intake

## Purpose

Capture what the system must achieve before designing anything: the business goals, the problems of today's system, who uses it, the quality targets and the hard constraints. Every later step and every architecture decision traces back to this brief, so keep it short, concrete and agreed.

## Inputs

- The requirement documents the user provides (brief, RFP, interview notes, current-system description). Read them in full.
- No earlier design files.

## Propose

Draft, from the documents:
- **System**: a name and one sentence: what it does and for whom.
- **Goals**: 3-6 outcomes the new design must deliver (faster change, scale for peaks, fewer outages, new channels).
- **Pain points**: the concrete problems of the current system, each with a short ID (`pp-slow-release`). Prefer the client's own wording.
- **Actors**: people (customer, staff roles) and external systems (payment provider, ERP, identity provider), each with an ID and `kind`.
- **NFRs**: measurable targets per category (availability, latency, peak load, data retention, security). Mark a target as an assumption when the documents give none.
- **Constraints**: what is fixed (regulation, required identity provider, region, budget, team skills).
- **Assumptions**: everything you inferred and the user must confirm.

## Key questions

1. Are these the right top pain points, in this order of importance? Recommended: keep 3-6, each one a problem the design must visibly answer; drop wishes that are really goals.
2. Which actors use the system, and which external systems does it depend on? Recommended: list every external system now, even if integration details come later, so the context map and logical view do not miss one.
3. What are the NFR targets (availability, latency, peak load)? Recommended: put numbers on the two or three that drive the architecture; record the rest as assumptions.
4. Which constraints are hard (cannot change) and which are preferences? Recommended: treat only regulation, contracts and mandated platforms as hard.

## Write

- `01-brief.md`: Summary (system and goals), Decisions (what is in and out of scope), Details (pain points table, actors table, NFR table, constraints, assumptions), Open questions.
- `brief.yaml`: `system`, `goals`, `pain_points`, `actors`, `nfrs`, `constraints`, `assumptions` (see the schema).

## Checklist

- BR-01: every pain point, actor and NFR has a unique ID.
- DOC-01 (judgement): the document's title and summary say what the brief covers.
- DOC-02 (judgement): the brief describes the problem and the target, not the history of the discussion.

## Good and bad

- Good pain point: `pp-peak-overload: "Evening order peaks overload the single database and checkout times out."`
- Bad pain point: `"The system is old"` - not a problem the design can answer or a reviewer can check.
