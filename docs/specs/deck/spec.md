# Deck

## Purpose

## Requirements

### REQ-DECK-001: Deck skill and CLI
The plugin SHALL provide a skill `sa-deck` and a CLI `skills/sa-deck/scripts/deck.py DESIGN_DIR [--outline] [--minutes N] [--force]` that reads `DESIGN_DIR/deck/deck.yaml` and writes `deck.html`, `deck.pptx` and slide images into `DESIGN_DIR/deck/`, without modifying `deck.yaml` or any file outside `DESIGN_DIR/deck/`.

#### Scenario: Deck written, sources untouched
- GIVEN a design folder with a valid `deck/deck.yaml`
- WHEN `deck.py design` runs
- THEN `design/deck/deck.html` and `design/deck/deck.pptx` exist and no other file under `design/` changed, including `deck.yaml`

### REQ-DECK-002: Proposed outline
WHEN `deck.py design --outline --minutes N` runs, the CLI SHALL print a draft `deck.yaml` with these sections, in this order:
1. cover and agenda;
2. introduction (proposed solution, business functions);
3. domain design (subdomains, context map, aggregates);
4. use case view (one slide per use-case diagram page);
5. logical view;
6. process view (one slide per saga scenario);
7. core patterns;
8. high-level and physical view;
9. development view (technology stack, ADRs);
10. Q&A.

The draft SHALL include only slides whose source step is `done`, and its suggested slide seconds SHALL total no more than N minutes.

#### Scenario: Partial design
- GIVEN a design with steps 01-05 done and steps 06-12 todo
- WHEN `deck.py design --outline --minutes 10` runs
- THEN the outline has the cover, agenda, introduction and domain design slides and Q&A only, and its seconds total at most 600

### REQ-DECK-003: Deck source schema
`deck.yaml` SHALL be validated against `references/deck.schema.yaml`, which defines:
- `meta`: title, subtitle, presenter, date, minutes;
- `theme`: optional;
- `sections`: each with a title and slides;
- each slide: `title`, `message`, one body `block`, `notes` (spoken script) and `seconds`.

#### Scenario: Unknown block type
- GIVEN a slide whose block type is `chart`
- WHEN `deck.py design` runs
- THEN it exits 1, names the slide number and the field, and writes nothing

### REQ-DECK-004: Body blocks
The renderers SHALL support these block types, each in both HTML and PPTX:
- `bullets`: at most 6 items, bold runs allowed;
- `table`: header and at most 8 rows;
- `diagram`: one diagram page;
- `diagrams`: two diagram pages side by side;
- `diagram-text`: a diagram page with 2 to 4 bullets;
- `agenda`: generated from the section titles;
- `image`: a PNG or JPEG file inside `DESIGN_DIR/deck/`.

#### Scenario: Table in PowerPoint
- GIVEN a slide with a `table` block of 5 rows
- WHEN the deck is rendered
- THEN the PPTX slide holds a table object with 6 rows (header included) and the HTML slide holds a `<table>` with the same cells

### REQ-DECK-005: Diagrams on slides
A diagram block SHALL name a step key and a page number of a `/sa-diagrams` file. The slide SHALL show that page as a PNG at slide resolution, keep its proportions, and show the legend entries of that page as chips under the image. IF the PNG cannot be produced because the draw.io CLI is missing, THEN the slide SHALL show a placeholder naming `/sa-diagrams --png`, and the run SHALL warn and still succeed.

#### Scenario: Legend as chips
- GIVEN a slide showing the context map page, whose legend lists sync and async arrows
- WHEN the deck is rendered
- THEN the slide shows the diagram image without its legend and notes boxes, and two chips labelled "Sync call" and "Async event"

### REQ-DECK-006: Time budget and spoken script
The checks SHALL warn WHEN the slide seconds total more than `meta.minutes` × 60, and WHEN a slide's notes exceed its seconds at 130 words per minute plus 15%. Warnings SHALL NOT stop rendering.

#### Scenario: Over budget
- GIVEN `meta.minutes: 20` and slides totalling 1,320 seconds
- WHEN `deck.py design` runs
- THEN it exits 0, the deck is written, and a warning states 22:00 against a 20:00 budget

### REQ-DECK-007: Consistency with the design
The checks SHALL report an error, write nothing and exit 1 WHEN:
- a diagram block names a step or page that has no diagram;
- an image block names a file outside `DESIGN_DIR/deck/` or one that does not exist;
- any slide text states "<number> services" with a number different from the number of services in `subdomains.yaml`.

#### Scenario: Wrong service count
- GIVEN `subdomains.yaml` with 8 services and a slide message "Twelve services, one per subdomain"
- WHEN `deck.py design` runs
- THEN it exits 1 and names that slide

### REQ-DECK-008: HTML deck
`deck.html` SHALL be one self-contained file with no external URL (images and the logo inlined). It SHALL provide:
- navigation by arrow keys, space, Home and End;
- `#n` to open slide n;
- a speaker-notes panel toggled by N;
- the slide position and the total time in a status bar;
- a print stylesheet that gives one 16:9 slide per page.

#### Scenario: Print to PDF
- GIVEN a deck of 20 slides
- WHEN `deck.html` is printed to PDF
- THEN the PDF has 20 pages and no status bar or notes panel

### REQ-DECK-009: PowerPoint deck
`deck.pptx` SHALL have the same slides in the same order as `deck.html`, with the same titles, key messages and speaker notes. Text and tables SHALL be editable objects, not images. WHERE Node.js or pptxgenjs is not available, the CLI SHALL write the HTML deck, skip the PPTX, print the `npm install` command and exit 0.

#### Scenario: Renderers in step
- GIVEN any valid deck
- WHEN both files are rendered
- THEN the slide count, the slide titles and the notes of `deck.pptx` equal those of `deck.html`

### REQ-DECK-010: Theme
A `theme` block SHALL set:
- the primary, accent and text colours;
- the font family;
- an optional logo file inside `DESIGN_DIR/deck/`;
- the presenter and footer text.

Values left out SHALL come from the plugin's neutral default theme, which names no organisation.

#### Scenario: Custom primary colour
- GIVEN `theme.primary: "#0B5394"`
- WHEN the deck is rendered
- THEN slide titles and table headers use `#0B5394` in both HTML and PPTX

### REQ-DECK-011: Incremental rebuild
The deck SHALL record a hash over `deck.yaml`, the effective theme, the logo and every embedded image. WHEN the recorded hash equals the current one and both output files exist, the CLI SHALL NOT rewrite them unless `--force` is given.

#### Scenario: Nothing changed
- GIVEN a deck rendered from unchanged sources
- WHEN `deck.py design` runs again
- THEN it reports the deck unchanged and both files keep their modification times
