# Design: SA method skills

Epic: sad-3p2

## Architecture

One orchestrator skill with per-step reference guides, plus a read-only review skill (see `docs/adr/0001-orchestrator-skill-with-step-guides.md`).

```
.claude-plugin/plugin.json
skills/sa-design/SKILL.md                 # state → pick step → load guide → propose → decide → write → check → record
skills/sa-design/references/
    steps/01-brief-intake.md … 12-adrs.md  # per step: purpose, inputs, options (allowed values, default),
                                           # key questions (2-5, each with a recommendation), output templates, rule IDs
    schema/<data-file>.schema.yaml         # JSON Schema (in YAML) per data file
    templates/                             # starting Markdown and YAML per step, sa-config.yaml, design-state.yaml
    presets.yaml                           # high-level / detailed → option values
    rules.yaml                             # rule catalogue (ID, step, check, severity, condition, script|judgement)
    profiles/aws.md                        # logical component → AWS service mapping and notes
skills/sa-review/SKILL.md                 # run check.py, then judgement rules, then write the report
skills/sa-review/scripts/check.py         # mechanical checks; exit 0/1
tests/                                     # pytest
tests/fixtures/<case>/design/              # fault fixtures + clean fixture
examples/clinic-booking/                   # fictional brief + complete design set (all 12 steps)
examples/food-delivery/                    # second fictional brief, steps 01-05 (generality trial)
```

Step dependencies (which data files each step reads) are declared in the front matter of each step guide, so `/sa-design` and `check.py` share one source.

## Data Flow

1. `/sa-design` reads `design/sa-config.yaml` and `design-state.yaml`, expands the preset with `presets.yaml`, and computes the effective options.
2. It selects the step (named, else first `stale`, else first `todo`) and checks prerequisites.
3. It loads that step's guide and the data files listed as its inputs.
4. It proposes content at the configured detail, asks the step's key questions one at a time, then writes `NN-<step>.md` and the data file, validated by the step schema.
5. It runs the active rules for the step (script rules via `check.py --step NN`, judgement rules by reading the files), records results, decisions, exceptions and open questions in `design-state.yaml`, and marks dependants `stale` if IDs or options changed.
6. `/sa-review` runs `check.py` on the whole folder, applies the judgement rules, and writes `review-report.md` with the effective configuration first.

Data files are YAML with stable IDs (`kebab-case`). Markdown files carry the rationale and are written for the audience, not for the review history.

## Error Handling

- Invalid data: fix and validate again before writing; never a partial step.
- Missing prerequisite: name it and offer to run it.
- Unknown option or rule ID in `sa-config.yaml`: reject with the allowed values.
- Manual edits: validate on start and report differences from the recorded decisions.
- Failed `error` rule: fix, or record an accepted exception with a reason; `/sa-review` lists exceptions separately.
- `check.py` crash or unreadable file: report the file and stop; exit code 2 (distinct from findings = 1).

## Testing

- pytest static tests: templates against schemas; `rules.yaml` well-formed; options referenced by rules are declared; presets only set declared options.
- `check.py` unit tests on fault fixtures and one clean fixture: exact findings and exit codes.
- Worked example `examples/clinic-booking/` and trial `examples/food-delivery/`: `check.py` exits 0.
- Neutral-content test: `skills/` and `examples/` contain no term from a deny-list of project-specific names kept in `tests/`.
- Test names or comments carry the REQ-ID they cover.
- Verify commands to add to `.agent-workflow/config.yaml` at plan approval: `pytest`, `ruff check .`.
