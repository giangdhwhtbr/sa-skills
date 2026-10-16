---
name: sa-diagrams
description: Draw the diagrams of a design/ folder produced by sa-design (steps 02-10) as editable draw.io files with Mermaid twins and optional PNGs, in one shared style; redraws only what changed.
---

# sa-diagrams

Turn the YAML data of a design made with `/sa-design` into diagrams: main business functions, domain decomposition, context map, aggregate roots, use cases, logical view, saga sequences, core patterns, and the high-level and physical architecture views. The diagrams are generated from the data, so they never drift from it: change the design with `/sa-design`, then draw again.

`<plugin>` below is the directory of this plugin (the folder that contains `skills/`).

## Before drawing
<!-- REQ-DIAGRAMS-010 -->

1. Find the design folder (`design/` in the current project, or the folder the user names). It must contain `sa-config.yaml` and `design-state.yaml`; only steps 02-10 marked `done` are drawn.
2. Python 3.10+ with `pyyaml` and `jsonschema` (the same as `/sa-review`).
3. The context map, aggregates and use cases are laid out with elkjs, which needs Node.js 18+. Install it once:
   `npm install --prefix <plugin>/skills/sa-diagrams/tools`
   Runs that draw only other steps (`--only functions subdomains ...`) do not need Node.
4. PNG export is optional and needs the draw.io desktop app. It is found through the `DRAWIO` variable, the macOS app, or `drawio` on the PATH.
<!-- REQ-DIAGRAMS-011 -->

## Draw
<!-- REQ-DIAGRAMS-001 -->
<!-- REQ-DIAGRAMS-002 -->

Run
`python3 <plugin>/skills/sa-diagrams/scripts/diagrams.py <design> [--only KEY ...] [--png] [--force]`

- `--only context-map saga` draws only those steps (keys: functions, subdomains, context-map, aggregates, use-cases, logical-view, saga, patterns, architecture).
- `--png` also exports one PNG per page to `<design>/diagrams/png/`; unchanged pages are not exported again.
- `--force` redraws even when the data has not changed.

Exit 0 = diagrams written or already up to date; 1 = the design data has error findings, so nothing was drawn (the output names the step: fix it with `/sa-design`, `/sa-review` lists the findings); 2 = usage error or a missing dependency (the output gives the install command). Report exit 1 and 2 to the user and stop.

## Read the result

The script prints one line per step: `wrote 04-context-map.drawio (1 page)`, `unchanged 03-subdomains.drawio`, `skipped 06-use-cases (todo)`, then the PNG count and any warning. Tell the user what was drawn and what was skipped, and why.

Everything is written to `<design>/diagrams/`:
- `NN-<key>.drawio`: the editable diagram of one step, one page per view (open it in draw.io or diagrams.net).
- `NN-<key>.mermaid.md`: the same nodes and arrows as Mermaid, for Markdown viewers and code review.
- `all-diagrams.drawio`: every page of every drawn step, in step order; open this one to present the design.
- `png/NN-<key>-pN.png`: the exported pages (with `--png`).

Each diagram records the hash of the data it was drawn from. When the data changes later, `/sa-review` reports the diagram as out of date (rule DG-01, a warning) until it is drawn again.

## Never

- Never edit the design's Markdown or YAML files: this skill only writes into `<design>/diagrams/`.
- Never draw from data with error findings, and never hand-edit generated files to hide a data problem; fix the data with `/sa-design` and draw again.
- Never edit the generated `.drawio` files when the design will be redrawn: changes made by hand are replaced on the next run. Copy a file first if it needs manual touches.
