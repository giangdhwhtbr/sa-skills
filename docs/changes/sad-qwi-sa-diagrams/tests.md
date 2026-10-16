# Tests: SA diagrams

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-DIAGRAMS-004, REQ-DIAGRAMS-005, REQ-DIAGRAMS-008 | manual | open examples/clinic-booking/design/diagrams/all-diagrams.drawio in draw.io; every page opens, is readable and uses the shared style |
| TC-02 | REQ-DIAGRAMS-007 | manual | compare the high-level and physical views of clinic-booking side by side; groups and service grid line up |
| TC-03 | REQ-DIAGRAMS-011 | manual | run with --png on a machine with draw.io; one PNG per page; a second run uses the cache |
| TC-04 | REQ-DIAGRAMS-006 | manual | compare food-delivery design and design-detailed context map and aggregates diagrams |
