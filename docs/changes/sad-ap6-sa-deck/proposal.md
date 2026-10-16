# SA deck: /sa-deck

Epic: sad-ap6
Date: 2026-10-16

## Why

A solution design is reviewed in a meeting, with a time limit. `/sa-design` produces the documents and data and `/sa-diagrams` the pictures, but turning them into a talk is still slow manual work. Each slide needs a title and a key message, plus a fitting diagram or table and a spoken script that fits its time. The PowerPoint version and the browser version drift apart, and the numbers on the slides drift away from the design data. A deck built from one checked source (`deck.yaml`), next to the design data and diagrams, can be drafted in minutes and re-rendered after every design change. It keeps the talk inside its time budget and its facts consistent with the design.

This is sub-project 2b; it uses the diagrams from sub-project 2a (`/sa-diagrams`).

## What Changes

- **New skill `/sa-deck`.** Claude drafts `design/deck/deck.yaml` with the user. A CLI `deck.py` then checks it and renders a self-contained HTML deck (`deck.html`, print to PDF) and an editable PowerPoint (`deck.pptx`) with speaker notes, both from the same source.
- **Default outline in 4+1 view order:**
  - cover and agenda;
  - introduction: proposed solution and business functions;
  - domain design, then the use case, logical and process views;
  - core patterns, then the high-level and physical views;
  - technology stack, ADRs, and Q&A.
  The outline is proposed from the steps that are done, with a suggested time per slide scaled to the talk length.
- **Body blocks:** bullets, table, one diagram, two diagrams, diagram with text, agenda and image. Diagrams come from `/sa-diagrams` PNGs, with the legend rebuilt as chips under each diagram.
- **Time budget and spoken script:** each slide carries seconds and a script. The checks warn when the total exceeds the budget or a script is too long for its seconds.
- **Theme block:** colours, font, optional logo, presenter and footer. One neutral default theme ships with the plugin.
- **Consistency checks:** schema, diagram references, and counts stated on slides against the design data.
- **Incremental rebuilds, and no data changes:** unchanged decks are not rebuilt. The deck never changes the design data.
- **New `/sa-review` rule DK-01:** a deck that is older than its source or the diagrams it uses.
- **An example deck** for `examples/clinic-booking`.

## Capabilities Affected

- `deck`: the new `/sa-deck` skill and its CLI.
- `review`: rule DK-01.
- `quality`: example deck and tests.
- `plugin`: the plugin exposes four skills.

## Non-goals

- Rendering into a corporate PPTX template or master file.
- Slide animations and transitions.
- Languages other than English for generated text.
- Topic-specific slides beyond the generic outline (users add their own with the bullets, table or image blocks).
- Live or zoomable diagrams in the HTML deck (diagrams are images).
- Editing the design data from the deck.

## Success Criteria

- **Example deck:** `/sa-deck` produces a 20-minute deck for `examples/clinic-booking`, committed with the example:
  - `deck.html` presents with keyboard navigation and a notes panel, and prints one slide per PDF page;
  - `deck.pptx` opens in PowerPoint or Keynote with the same slides, titles and speaker notes.
- **Outline:** for `examples/food-delivery` (steps 01-05 only), the proposed outline contains only slides for those steps.
- **Checks:** a deck whose times exceed the budget gets a warning. A slide stating a different service count than `subdomains.yaml` is an error.
- **Quality:** `pytest` and `ruff check .` pass, and the plugin still names no real client, course, organisation or past project.
