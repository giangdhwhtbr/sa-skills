---
name: sa-design
description: Guided, step-by-step DDD + microservices solution design (functions, subdomains, context map, aggregates, use cases, logical view, saga, patterns, architecture, stack, ADRs). Use when designing or updating a solution architecture; resumes from design/design-state.yaml.
---

# sa-design

Guide the user through a DDD + microservices solution design, one step per run. Each step proposes content, asks the step's key decisions one at a time, writes a Markdown document and a YAML data file into the design folder, checks them, and records progress so the next run resumes where this one stopped.

`<plugin>` below is the directory of this plugin (the folder that contains `skills/`); `<design>` is the design folder. The check script needs Python 3.10+ with `pyyaml` and `jsonschema`.

The 12 steps, in order (guide in `<plugin>/skills/sa-design/references/steps/NN-<key>.md`):
01 brief, 02 functions, 03 subdomains, 04 context-map, 05 aggregates, 06 use-cases, 07 logical-view, 08 saga, 09 patterns, 10 architecture, 11 stack, 12 adrs.

## Locate
<!-- REQ-DESIGN-001 -->

1. Look for `design/` in the current project (or the folder the user names) containing `sa-config.yaml` and `design-state.yaml`.
2. If there is none, propose creating `design/` in the project root and ask the user to confirm the location. Then copy `<plugin>/skills/sa-design/references/templates/sa-config.yaml` and `design-state.yaml` into it. The new design uses the `high-level` preset and the `aws` cloud profile, and every step is `todo`. Show the user the presets (`high-level`, `detailed`, `custom`) and ask whether to keep `high-level`.

## Start of every run
<!-- REQ-DESIGN-008 -->

1. Run `python3 <plugin>/skills/sa-review/scripts/check.py <design> --changed`. For every file it prints (edited outside this skill), run `check.py <design> --dependents <step-key>` for the step that owns the file, tell the user which file changed and which later steps may now be stale, and ask whether to mark them `stale`.
2. Run `python3 <plugin>/skills/sa-review/scripts/check.py <design> --format json --step brief` and read `config` (effective preset, options, overrides). If the output has `CONFIG` findings (unknown preset, option, value or rule), show them with the allowed values and stop until the configuration is fixed.

## Choose the step
<!-- REQ-DESIGN-002 -->
<!-- REQ-DESIGN-007 -->

1. If the user named a step (number or key), run that step.
2. Otherwise run the first step whose status is `stale`, else the first `todo` step. If every step is `done`, say so and suggest `/sa-review`.
3. Check the step's `inputs` (front matter of its guide): if a step that produces one of them is not `done`, name that step and offer to run it first. Do not run a step on missing inputs.

## Run the step
<!-- REQ-DESIGN-004 -->
<!-- REQ-CONFIG-006 -->

1. Read only this step's guide (`references/steps/NN-<key>.md`) and the data files listed in its `inputs`. Do not load other guides.
2. Draft the content as the guide's "Propose" section describes, at the option values of the effective configuration (for example `aggregates.detail = roots-only` drafts roots and ID references only). Show the draft as a short table or list.
3. Ask the guide's key questions one at a time, each with its recommended answer and the reason, and wait for each answer. Write nothing until every key question is answered.
4. Steps 01-09 stay vendor-neutral unless an option allows otherwise. From step 10, map logical components to cloud services with `references/profiles/<cloud>.md` (the `cloud` of the effective configuration).

## Write
<!-- REQ-DESIGN-003 -->
<!-- REQ-DESIGN-005 -->

1. Write `<design>/NN-<key>.md` (sections: Summary, Decisions, Details, Open questions; start from `references/templates/NN-<key>.md`) and the step's data file (start from `references/templates/<data>.yaml`; fields as in `references/schema/<data>.schema.yaml`). Use only service and context IDs defined in `subdomains.yaml`.
2. Run `python3 <plugin>/skills/sa-review/scripts/check.py <design> --step <key> --format json`. If it reports `SCHEMA` findings, fix the data file and run it again before going on. Never leave a step with only one of its two files written.

## Checklist
<!-- REQ-DESIGN-009 -->

1. Show every rule listed in the guide's `rules` that is active for the effective configuration, plus DOC-01 and DOC-02, as pass or fail:
   - script rules: the findings of the `--step` run above;
   - judgement rules (FN-01, PT-02, DOC-01, DOC-02): read the written files and decide, quoting the evidence.
2. For each failed `error` rule: fix the files and check again, or, only if the user decides so, record an accepted exception `{rule, reason}` in this step's `exceptions` in `design-state.yaml`. A `warn` is reported only.

## Record
<!-- REQ-DESIGN-006 -->

1. In `design-state.yaml`, set this step to `status: done`, add one short line per decided question to `decisions`, list unresolved points in `open_questions`, clear `stale_reason`, and store the SHA-256 of both written files in `files` (for example `python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <file>`).
2. If this run added, removed or renamed any ID (subdomain, service, context, aggregate, component, pain point), run `check.py <design> --dependents <key>` and set every listed step that is `done` to `stale` with `stale_reason` naming the changed IDs.
3. Stop. Summarise what was written and suggest the next step.

## Changing options
<!-- REQ-CONFIG-005 -->

1. Change `sa-config.yaml` (preset, step option, cloud or rule severity) only after the user agrees, and only to values listed in the step guides.
2. After a change, mark the step that owns the option and every step from `check.py <design> --dependents <key>` as `stale` with the reason (for example `aggregates.detail changed to full`). Changing the preset or the cloud marks every affected step the same way.

## Writing style

- Write for the audience of the design: describe the solution, its decisions and their reasons (DOC-02). Do not describe how the design evolved, earlier drafts or who reviewed it.
- Every title says what its content shows (DOC-01); a "functions" document lists functions, a "context map" shows relationships.
- Keep each document short: tables and numbered flows over prose. One idea per sentence.
