# Tests: SA diagrams

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-DIAGRAMS-004, REQ-DIAGRAMS-005, REQ-DIAGRAMS-008 | manual | open examples/clinic-booking/design/diagrams/all-diagrams.drawio in draw.io; every page opens, is readable and uses the shared style |
| TC-02 | REQ-DIAGRAMS-007 | manual | compare the high-level and physical views of clinic-booking side by side; groups and service grid line up |
| TC-03 | REQ-DIAGRAMS-011 | manual | run with --png on a machine with draw.io; one PNG per page; a second run uses the cache |
| TC-04 | REQ-DIAGRAMS-006 | manual | compare food-delivery design and design-detailed context map and aggregates diagrams |

## Manual results (2026-10-16, macOS, draw.io desktop 32.4.1, Node 24)

- **TC-01: pass.** `diagrams.py examples/clinic-booking/design --png` wrote nine step files (16 pages). The draw.io CLI exported `all-diagrams.drawio` to a cropped PDF of 16 pages, one per diagram, so every page opens and renders. I inspected each page's PNG in `diagrams/png/`:
  - **Bands:** functions use one coloured band per actor group, named in the legend; subdomains use core/supporting/generic bands with the service under each subdomain.
  - **Graphs:** the context map has U and D at both ends of all 8 arrows. The aggregates page shows references labelled `<id> <multiplicity>`, plus a note for Reporting, which has no aggregate. Use cases get 3 pages: people on the left, external systems on the right.
  - **Logical view and patterns:** layers with routed, numbered flows. No arrow crosses a node and no label overlaps another. There are 3 pattern pages with S/O/R steps listed in the notes.
  - **Saga:** 3 sequence pages; the labels sit above the arrows, and compensations are red on a light red band.
  - **Architecture:** the high-level view, and a physical view with AWS icons, subnet tiers with their CIDRs, the VPC and the region.
  - **Shared style:** every page uses the same fills per subdomain type and the same arrow styles. Each legend lists only what its page uses.
- **TC-02: pass.** In `10-architecture-p1.png` and `10-architecture-p2.png`, the boxes have the same labels and positions: Clients, Edge, Backend (Microservices, Data, Managed services) and External systems. The service grid has the same order in both views: Scheduling, Appointment, Directory and Insurance, then Notification, Reporting, Payment and Identity. The physical view only adds the region and VPC frames and the tier labels around that grid. `test_architecture_shared_skeleton` checks identical coordinates for the example and for 3 and 15 services.
- **TC-03: pass.** The first `--png` run exported 16 PNGs for clinic-booking and 4 for each food-delivery set. The second run printed `png: 0 exported, 16 cached` (and `0 exported, 4 cached` for each food-delivery set), with every step `unchanged`. `test_png_cache` checks the same in CI when draw.io is installed.
- **TC-04: pass.** On the food-delivery context maps, `design` (high-level) shows the 7 contexts and their relationship labels only. `design-detailed` adds an "External systems" group with the card payment provider and the maps and routing provider, each reached through an `ACL` arrow, and labels the arrows with the pattern names. The detailed aggregates diagram shows entities, value objects and events inside each aggregate boundary. The high-level one shows aggregate roots only.

### Page-by-page PNG review (all 24 committed pages opened)

| Set | Pages | Seen |
|---|---|---|
| clinic-booking | 02 p1 · 03 p1 · 04 p1 · 05 p1 · 06 p1–p3 · 07 p1 · 08 p1–p3 · 09 p1–p3 · 10 p1–p2 (16) | all readable; no node overlaps; no arrow through a node; legends list only what the page uses |
| food-delivery/design | 02 · 03 · 04 · 05 (4) | 02 and 03 are byte-identical to design-detailed (same data, no option dependency); 04 has no externals; 05 shows roots only |
| food-delivery/design-detailed | 02 · 03 · 04 · 05 (4) | 04 adds an External systems group with ACL arrows; 05 shows entities, value objects and events inside each aggregate |

Cosmetic notes (readable, not blocking):
- **09 p2 (observability):** the O2 self-loop label sits close to the O1 label.
- **07 p1:** the flow label "4. route to the owning service" overlaps the "Microservice layer" heading.
- **05 (detailed):** the aggregate boxes carry empty space on the left, a result of the hierarchical ELK layout.

### Branch readiness
- **Merge:** `main` (= `origin/main`, 5ab34dd) is an ancestor of `feat/sa-diagrams`, so the branch merges into `main` as a clean fast-forward (`git merge-tree` reports no conflicts).
- **Remote:** `feat/sa-diagrams` does not exist on `origin`; nothing was pushed or merged, and no history was rewritten.
