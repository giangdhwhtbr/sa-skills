---
number: 2
key: functions
title: Business functions
markdown: 02-functions.md
data: functions.yaml
schema: functions.schema.yaml
inputs: [brief.yaml]
options: {}
rules: [FN-01, FN-02]
---

# Step 02 - Business functions

## Purpose

List what the platform must do, grouped by who uses it. This is a function map, not a flow: it answers "what capabilities exist?" and becomes the input for subdomains (step 03) and use cases (step 06).

## Inputs

- `brief.yaml`: the actors (to group functions by) and the goals (to check nothing is missing).

## Propose

- Group functions by actor type, for example customer-facing, back office, and administration. Use the actors from the brief; a group may serve several actors of the same kind.
- In each group, list 4-10 functions as verb phrases ("Search and filter offers", "Manage price lists"), each with an ID and a one-line description.
- Order functions in each group the way a user meets them, but draw no arrows and no sequence: a flow belongs in the saga (step 08) and use cases (step 06).
- Include functions the brief implies but does not state (view my order status, manage staff roles, configure notification templates) and mark them in the open questions if unsure.

## Key questions

1. Are these the right groups? Recommended: one group per kind of user (customer-facing, back office, administration); split a group only when its users and permissions clearly differ.
2. Is any function missing or out of scope? Recommended: walk the main user journey and each back-office role once; anything they need is a function, anything nobody uses is out.
3. Does any function belong to two groups? Recommended: keep it once, in the group of the actor who owns the outcome, and mention the other actor in its description.

## Write

- `02-functions.md`: Summary (the groups and why), Decisions (in/out of scope), Details (one table per group: function, description), Open questions.
- `functions.yaml`: `groups` with `id`, `name`, `actor_ids`, and `functions` (`id`, `name`, `description`).

## Checklist

- FN-01 (judgement): the document lists functions grouped by actor; it does not draw or describe a flow. A title such as "Main business functions" must be followed by functions, not a journey.
- FN-02: every group names at least one actor from `brief.yaml`.
- DOC-01, DOC-02 (judgement): the title matches the content; the text describes the solution.

## Good and bad

- Good: "Back-office functions: Manage catalogue, Manage price lists, Handle refunds, View sales reports."
- Bad: a slide titled "Main business functions" that shows "Search -> Select -> Pay -> Receive ticket" as a flow.
