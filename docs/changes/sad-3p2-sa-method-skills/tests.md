# Tests: SA method skills

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-PLUGIN-001 | manual | install the plugin into an empty project; `/sa-design` and `/sa-review` appear |
| TC-02 | REQ-DESIGN-001, REQ-DESIGN-002, REQ-DESIGN-004 | manual | first run creates `design/`; resume picks the next step; no files change before the questions are answered |
| TC-03 | REQ-DESIGN-006, REQ-CONFIG-005 | manual | re-run step 03 with a renamed subdomain, and change `aggregates.detail`; later steps become `stale` with reasons |
| TC-04 | REQ-CONFIG-002 | manual | run step 05 under `high-level` and `detailed`; proposals differ (roots only vs entities and value objects) |
| TC-05 | REQ-QUALITY-003 | manual | run all 12 steps on the clinic-booking sample brief; read the design set end to end for coherence |
