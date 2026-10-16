# Tests: SA method skills

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-PLUGIN-001 | manual | install the plugin into an empty project; `/sa-design` and `/sa-review` appear |
| TC-02 | REQ-DESIGN-001, REQ-DESIGN-002, REQ-DESIGN-004 | manual | 2026-10-16, agent-run in a scratch project following skills/sa-design/SKILL.md: first run copied the templates, 12 steps `todo`, effective config `high-level` (aggregates.detail = roots-only); after step 01 was done the next step chosen was `functions`; `check.py design` -> `0 errors, 0 warnings`, exit 0; asking for step 04 before 03: guide inputs `[subdomains.yaml]` -> offer to run step 03 first. No file was written before the step's questions were answered (instruction in Run the step, item 3). |
| TC-03 | REQ-DESIGN-006, REQ-CONFIG-005 | manual | 2026-10-16, agent-run on a copy of the clean fixture with recorded hashes: renaming subdomain `lockers` -> `locker-network` made `check.py --changed` print `subdomains.yaml`; `--dependents subdomains` -> `context-map aggregates logical-view saga patterns architecture stack adrs` (marked stale per SKILL.md Record step 2); the dangling references surfaced as `ERROR AG-02 aggregates.yaml locker` and two warnings; option change `aggregates.detail` -> `full`: `--dependents aggregates` -> `saga adrs` plus the aggregates step itself. |
| TC-04 | REQ-CONFIG-002 | manual | run step 05 under `high-level` and `detailed`; proposals differ (roots only vs entities and value objects) |
| TC-05 | REQ-QUALITY-003 | manual | run all 12 steps on the clinic-booking sample brief; read the design set end to end for coherence |
