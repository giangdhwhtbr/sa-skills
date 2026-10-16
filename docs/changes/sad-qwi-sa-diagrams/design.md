# Design: SA diagrams

Epic: sad-qwi

## Architecture

A third skill in the plugin with a Python package and a small Node tool for graph layout (approach A, hybrid by diagram kind; see `docs/adr/0002-hybrid-diagram-layout.md`).

```
skills/sa-diagrams/SKILL.md
skills/sa-diagrams/scripts/diagrams.py          # CLI entry; exit 0 written, 1 design errors, 2 dependency/usage
skills/sa-diagrams/scripts/sadiagram/
    model.py            # Node, Group, Edge, Page, DiagramSet (shared drawing model, absolute geometry)
    style.py            # palette, node kinds, arrow kinds
    legend.py           # legend and notes block for a page (only the styles used)
    elk.py              # elkjs bridge: model -> ELK JSON -> node tools/layout.js -> positions
    layouts/bands.py    # bands and grids (functions, subdomains, logical layers, pattern chains)
    layouts/skeleton.py # shared architecture skeleton sized from the data
    layouts/sequence.py # saga sequence pages
    builders/           # one module per step: read YAML + effective config -> list[Page]
    drawio.py           # DiagramSet -> mxfile XML (one diagram element per page)
    mermaid.py          # DiagramSet -> Markdown with one mermaid block per page
    export.py           # PNG via draw.io desktop CLI: timeout, retries, content-hash cache
    stamp.py            # source-hash stamp read/write in the mxfile
skills/sa-diagrams/tools/layout.js
skills/sa-diagrams/tools/package.json           # elkjs, installed with npm in this folder
```

The package reuses `sacheck` (from sa-review) to load the effective configuration and to run the checks before drawing; it does not duplicate them.

## Data Flow

1. `diagrams.py` resolves the plugin references and the design folder, runs `sacheck.checks.run` for the steps to draw; any error finding -> exit 1 without writing.
2. It selects steps 02-10 that are `done` (or `--only`), computes the source hash of each step's data inputs, and skips steps whose diagram stamp matches.
3. Each builder turns YAML into pages of the drawing model at the configured detail; the layout for its kind sets geometry (elkjs for 04, 05, 06; bands for 02, 03, 07, 09; skeleton for 10; sequence for 08).
4. `drawio.py` and `mermaid.py` write the step files; `all-diagrams.drawio` is rebuilt from every step file in step order.
5. With `--png`, `export.py` exports each page to `diagrams/png/NN-<key>-pN.png`, using a cache keyed by the page XML hash.

## Error Handling

- Design errors: stop before writing, name the step, exit 1.
- Node or elkjs missing: stop before writing, print `npm install --prefix <plugin>/skills/sa-diagrams/tools`, exit 2.
- draw.io CLI missing with `--png`: write draw.io and Mermaid, warn, exit 0.
- draw.io export hang: timeout 120 s, at most two retries, then report the page and continue.
- More than 40 nodes on one page: split by group and mention it in the summary.

## Testing

- Writers: generated mxfiles parse, cell IDs are unique, every edge's source and target exist; Mermaid blocks parse by structure.
- Completeness: every ID of the source data appears on its diagram (per builder).
- Options: externals only under `with-externals`; aggregate internals only under `full`; no vendor terms on the logical view under `vendors: none`.
- Skeleton: identical group positions and service order in both views for 3, 8 and 15 services.
- Layout sanity: no overlapping nodes; children inside group bounds.
- Incremental: unchanged data does not rewrite; one changed file rewrites only its dependants.
- Dependencies: elkjs missing -> exit 2; `--png` without draw.io -> exit 0 with a warning.
- elkjs-dependent tests skip with a reason when Node is not installed; band, skeleton and sequence tests never need Node.
- DG-01 positive and negative cases in the sa-review tests.
