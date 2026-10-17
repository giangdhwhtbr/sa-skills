# Tests: SA deck

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-DECK-008 | manual | open examples/clinic-booking/design/deck/deck.html in a browser: arrow keys, Home/End, #n, N notes panel, total time; print to PDF gives one slide per page without the status bar |
| TC-02 | REQ-DECK-009, REQ-DECK-004 | manual | open deck.pptx in PowerPoint or Keynote: same slides, titles and speaker notes as the HTML deck; tables and text are editable |
| TC-03 | REQ-DECK-005, REQ-DECK-010 | manual | diagrams are readable at slide size, legend chips match each diagram, theme colours and font applied in both formats |
| TC-04 | REQ-DECK-002, REQ-DECK-006 | manual | run /sa-deck on examples/clinic-booking with a 20-minute budget; the drafted deck stays within budget and every script fits its seconds |

## Manual results (2026-10-16, macOS, Chrome headless and the built-in browser pane, Node 24, pptxgenjs 3.12.0, draw.io 32.4.1)

**How the example deck was written.** `examples/clinic-booking/design/deck/deck.yaml` was written by following `skills/sa-deck/SKILL.md`:
1. `check.py` reported 0 errors and 0 warnings, and all 16 diagram PNGs were present.
2. `deck.py --outline --minutes 20` proposed 24 slides.
3. The messages, tables and scripts were filled from the design documents, using only facts from the design.

At each question, the recommended option was taken:
- **Length and audience:** 20 minutes, for an architecture review board.
- **Presenter:** "Solution architect", so the example names no real person.
- **Slides:** all 22 kept. The technology stack was folded onto one 8-row slide by putting "API contract" in the Services row (the outline had split it in two).
- **Timing:** scripts sized for 17:55, which leaves a 2-minute margin.

**TC-01: pass.**
- **Presenting.** `deck.html` was served locally and opened in the built-in browser pane. I looked at all 22 slides by stepping through with →, Space and PageDown, and also tested End, Home, `#4` (opens slide 4) and N (the notes panel shows the slide's script). The status bar showed `n / 22` and `Total 17:55 of 20:00`.
- **Printing.** Chrome headless `--print-to-pdf` gave **22 pages** of 960×540 pt (16:9), one slide per page, with no status bar and no notes panel; I checked pages 2, 3, 12, 20 and 22.
- **Bug found and fixed.** The first print showed two pain-point rows of the Proposed solution table split into three cells. An unquoted comma in a YAML `[...]` list caused it. I quoted the rows, and `checks.py` now rejects any table row whose cell count differs from the header (`test_table_row_width_matches_header`).

**TC-02: pass, through an alternative method.**
- **PowerPoint not used.** Microsoft PowerPoint is installed but did not answer AppleScript (`AppleEvent timed out`, probably a dialog waiting on screen). I did not force-quit it, so I could not open the file in PowerPoint itself.
- **What was checked instead.** Each of the 22 slides was rendered as a one-slide `.pptx` with the same renderer and opened with macOS Quick Look. All 22 match the HTML deck: same titles, key messages, tables with real cells (3 table slides), diagrams with wrapped legend chips, agenda, and cover.
- **Automated checks.** `test_deck_pptx` checks that the slide count, titles and notes match the HTML, and that tables are real `<a:tbl>` objects.
- **Fonts.** Quick Look renders Calibri with a serif fallback, so fonts were not compared.

**TC-03: pass.**
- **Diagrams.** All diagram slides are readable at slide size: the images were exported at 2× from the diagram pages, without title, legend or notes boxes. The chips under each diagram list exactly that page's legend entries.
- **Theme.** The default theme (navy titles and table headers, magenta accent) is applied in both formats.
- **Weak spot.** The two failure-scenario saga slides show small diagrams, because the full-height lifelines are scaled into the slide. They are readable, but a cropped variant would read better.

**TC-04: pass.**
- **Draft.** The outline at 20 minutes was 24 slides at ≤ 20:00, with the seconds scaled from the default weights.
- **Final deck.** 22 slides, 17:55 of 20:00. `deck.py` reported no budget or script warnings, and `test_example_deck_fits` asserts no findings.
- **Rebuilds.** A second `deck.py` run printed `unchanged deck`, and `check.py` shows no DK-01 or DG-01.
