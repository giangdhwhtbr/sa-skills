---
name: sa-review
description: Read-only audit of a design/ folder produced by sa-design - completeness, schemas, rules, cross-step consistency and traceability; writes design/review-report.md.
---

# sa-review

Audit a solution design made with `/sa-design` and report what is missing, inconsistent or against the configured rules. The review never changes the design: fixes are made by re-running steps with `/sa-design`.

`<plugin>` below is the directory of this plugin (the folder that contains `skills/`). The scripts need Python 3.10+ with `pyyaml` and `jsonschema`.

## Run checks
<!-- REQ-REVIEW-001 -->

1. Find the design folder (`design/` in the current project, or the folder the user names). It must contain `sa-config.yaml` and `design-state.yaml`.
2. Run the mechanical checks and keep the JSON:
   `python3 <plugin>/skills/sa-review/scripts/check.py <design> --format json`
   Exit 0 = no errors, 1 = errors found, 2 = the folder or a dependency is broken (report it and stop).
3. The JSON lists the effective configuration (preset, cloud, options, rule overrides), every finding of the script rules (completeness, schemas, cross-step references, traceability) and the accepted exceptions.

## Judgement rules
<!-- REQ-REVIEW-003 -->

Some rules need reading, not scripts. Read `<plugin>/skills/sa-design/references/rules.yaml` and apply every rule with `check: judgement` that is active for the effective configuration (respect its `condition` and any severity override; skip `off`). Today these are:
- FN-01: the functions document lists functions grouped by actor; it does not draw a flow.
- PT-02 (when `patterns.split = one-per-pattern`): each core pattern has its own section and view.
- DOC-01: each document's title matches what its content shows.
- DOC-02: documents describe the solution, not how the design evolved or who reviewed it.

For each, read the Markdown documents in the design folder and decide pass or fail with evidence (file and the line or heading). Write every failure to a temporary JSON file as a list of `{"rule", "severity", "file", "item", "message"}` with the effective severity. A failure that the design state records as an accepted exception for that step is not repeated; it is listed under accepted exceptions with its reason.

## Write the report

Run
`python3 <plugin>/skills/sa-review/scripts/render_report.py <design> --judgement <temp-file>.json`
It writes `<design>/review-report.md` with, in order: Configuration, Summary, Errors (script and judgement findings, errors first), Warnings, Accepted exceptions (step, rule, reason), Step status (every step with its status and open questions).

Then print a short summary in chat: ready or not ready, the error and warning counts, the top three errors, and which steps to re-run with `/sa-design` to fix them.

## Never

- Never edit, create or delete any file in the design folder other than `review-report.md`.
- Never mark steps done, stale or excepted; that is `/sa-design`'s job after the user decides.
- Never weaken a rule to make the design pass; report the finding and let the user decide on an exception.
