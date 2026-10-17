# Design: SA deck

Epic: sad-ap6

## Architecture

A fourth skill: one checked source and two renderers (approach A; see `docs/adr/0003-one-deck-source-two-renderers.md`).

```
skills/sa-deck/SKILL.md
skills/sa-deck/scripts/deck.py              # CLI; exit 0 written/unchanged, 1 deck errors, 2 usage/dependency
skills/sa-deck/scripts/sadeck/
    model.py      # Deck, Section, Slide, Block, Theme (normalised render model)
    schema.py     # load deck.yaml, validate against references/deck.schema.yaml
    outline.py    # draft deck.yaml from done steps (4+1 order, seconds scaled to the budget)
    checks.py     # budget, script length, references, stated counts (errors and warnings)
    assets.py     # diagram page -> slide PNG (via sadiagram export + cache), legend chips, placeholder
    html.py       # Deck -> self-contained deck.html
    pptx.py       # Deck -> deck.json -> node tools/pptx.js -> deck.pptx
    stamp.py      # deck source hash (deck/.deck-stamp.json)
    run.py        # orchestration used by deck.py
skills/sa-deck/tools/pptx.js                # pptxgenjs renderer (same grid as html.py)
skills/sa-deck/tools/package.json           # pptxgenjs 3.12.0
skills/sa-deck/references/deck.schema.yaml
skills/sa-deck/references/theme.yaml        # neutral default theme
skills/sa-deck/references/outline.md        # what each default slide shows and says
```

The package reuses `sacheck` (load the configuration and data, run the checks) and `sadiagram` (page XML, PNG export and cache, the legend entries of a page). It does not duplicate them.

## Data Flow

1. **Outline.** `/sa-deck` runs `deck.py design --outline --minutes N`, which prints a draft. Claude completes the messages, table rows and scripts from the design documents, asks the user one question at a time on cuts and emphasis, and writes `design/deck/deck.yaml`.
2. **Load and validate.** `deck.py design` loads and validates `deck.yaml`, then runs the deck checks. Any error means exit 1 and nothing is written.
3. **Images.** For each diagram block, `assets` takes the page from `diagrams/NN-key.drawio` and strips its legend and notes cells. It exports the page at scale 2 through the `sadiagram` PNG cache and reads the page's legend entries for the chips.
4. **Render.**
   - `html.py` writes `deck.html` with the images inlined.
   - `pptx.py` writes `deck/.build/deck.json` (absolute image paths, normalised text runs) and runs `node tools/pptx.js` to write `deck.pptx`.
5. **Stamp.** `stamp.py` records the source hash. The next run compares hashes and skips rendering when nothing changed.

## Layout Grid (shared by both renderers)

| Element | HTML (px, 1280×720) | PPTX (in, 13.333×7.5) |
|---|---|---|
| Title | 34,18 · 1180 wide · 32 px | 0.45,0.2 · 28 pt |
| Key message | 34,62 · 16 px | 0.45,0.8 · 15 pt |
| Body | 34,100 · 1212×560 | 0.45,1.3 · 12.43×5.6 |
| Footer, number | bottom 10 px | bottom 0.4 in |

## Error Handling

- **Deck errors** (schema, references, stated counts): list each one with its slide number and field, write nothing, exit 1.
- **Missing `deck.yaml` without `--outline`:** say "run with --outline first", exit 2.
- **Node or pptxgenjs missing:** write the HTML, skip the PPTX, print `npm install --prefix <plugin>/skills/sa-deck/tools`, exit 0.
- **draw.io missing:** use cached PNGs. A page with no PNG gets a placeholder, plus a warning; exit 0.
- **pptxgenjs failure:** keep the HTML, report the Node error, exit 2.

## Testing

- **Schema:** a valid deck passes, and each block type with a wrong field is rejected with its slide number.
- **Outline:** clinic-booking gives every section in 4+1 order; food-delivery gives only the slides for steps 01-05; the seconds stay within the budget.
- **Checks:** over budget, a script too long, an unknown diagram page, an image outside the deck folder, and a wrong service count.
- **HTML:** one section per slide, notes present, images inlined, no `http` URL, and the print stylesheet present.
- **PPTX** (skipped without Node): read the file with `zipfile`; check the slide count, titles, notes and table objects; HTML and PPTX must agree.
- **CLI:** exits 1 and 2, an unchanged rebuild, `--force`, Node missing, draw.io missing.
- **DK-01:** positive and negative cases in the sa-review tests.
- **Example deck:** up to date with its sources.
