---
name: sa-deck
description: Build a timed presentation of a design/ folder produced by sa-design - drafts deck.yaml with the user (4+1 view order, key messages, speaker scripts within a time budget), then renders a self-contained HTML deck and an editable PowerPoint from it.
---

# sa-deck

Turn a design made with `/sa-design` and its diagrams from `/sa-diagrams` into a talk. One source file, `design/deck/deck.yaml`, holds every slide's title, key message, body (bullets, table or diagram), spoken script and time. `deck.py` checks it against the design and renders `design/deck/deck.html` (present in a browser, print to PDF) and `design/deck/deck.pptx` (editable PowerPoint with speaker notes).

`<plugin>` below is the directory of this plugin (the folder that contains `skills/`).

## Before building
<!-- REQ-DECK-001 -->

1. Find the design folder (`design/` in the current project, or the folder the user names). It needs `sa-config.yaml` and `design-state.yaml`, and the steps to present must be `done`.
2. Run `python3 <plugin>/skills/sa-review/scripts/check.py <design>`.
   - If it reports errors, stop and suggest fixing them with `/sa-design` first.
   - If it reports DG-01 (diagrams out of date), or `<design>/diagrams/png` is missing, offer to run `/sa-diagrams --png` first. The deck uses the diagrams as slide images, and pages that were never exported appear as placeholders.
3. The PowerPoint needs Node.js 18+ and pptxgenjs. Install them once with `npm install --prefix <plugin>/skills/sa-deck/tools`. Without them only the HTML deck is written.

## Draft the deck
<!-- REQ-DECK-002 -->
<!-- REQ-DECK-006 -->

Skip to Render when `<design>/deck/deck.yaml` already exists and the user only wants it re-rendered or changed.

1. Ask, one question at a time and each with a recommendation:
   - the talk length (recommended: 20 minutes);
   - the audience (architecture review board, delivery team, or steering committee);
   - the presenter name and date.
2. Run `python3 <plugin>/skills/sa-deck/scripts/deck.py <design> --outline --minutes N` and read the draft. It lists the slides in 4+1 view order for the steps that are done, with the seconds already scaled to the budget.
3. Read `<plugin>/skills/sa-deck/references/outline.md`. It says what each slide's key message and script should cover. Then read the design's Markdown documents and YAML data, and fill every slide:
   - **Key message:** one line of at most 140 characters that states the point, not the topic.
   - **Proposed solution table:** answer each pain point with the pattern, subdomain or ADR that solves it. Use only facts from the design.
   - **Spoken script (notes):** short sentences, one idea each. Keep it to about 130 words per minute of the slide's seconds. Name the pattern and the problem it solves.
   - **Cover:** a 2–3 sentence opening.
4. Ask the key cut and emphasis choices one at a time, each with a recommendation. For example: which saga scenarios to keep in a short talk, whether to merge the high-level and physical views into one `diagrams` slide, and which ADRs matter most to this audience.
5. Write `<design>/deck/deck.yaml` and show the user the slide list with the times.

## Render
<!-- REQ-DECK-009 -->

Run `python3 <plugin>/skills/sa-deck/scripts/deck.py <design> [--force]`.

- **Exit 0:** the output lists `wrote deck.html (N slides, MM:SS of MM:SS)` and `wrote deck.pptx`, or `unchanged deck`, followed by any warnings.
  - A budget warning, or a slide whose notes run longer than its seconds: shorten the scripts or cut slides in `deck.yaml`, then render again.
  - A placeholder warning: run `/sa-diagrams --png`.
  - `pptx skipped`: give the user the install command it prints.
- **Exit 1:** `deck.yaml` has errors. The output names the slide and the field; fix `deck.yaml` and render again. Errors include a schema problem, a diagram page that does not exist, an image outside `deck/`, or a stated service count that differs from `subdomains.yaml`.
- **Exit 2:** a usage or dependency problem. Report it.

Then tell the user how to use the outputs:
- Open `deck.html` in a browser. Arrow keys move between slides, `N` opens the speaker notes, `#n` in the URL jumps to slide n, and printing it gives a PDF with one slide per page.
- `deck.pptx` holds the same slides and notes as editable PowerPoint.

When the design or the diagrams change later, `/sa-review` reports DK-01 until the deck is rendered again.

## Never

- Never change the design's Markdown or YAML files: this skill writes only `deck/deck.yaml` and the rendered files in `deck/`.
- Never invent facts, numbers, names or decisions that are not in the design documents; ask the user instead.
- Never hide a check error by editing the rendered files; fix `deck.yaml` and render again.
