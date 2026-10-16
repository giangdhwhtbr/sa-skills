# One deck source, two renderers

Date: 2026-10-16
Status: proposed

## Context

`/sa-deck` must produce a browser deck (HTML, printable to PDF) and an editable PowerPoint with the same slides and speaker notes. We considered three options:
- treating the HTML as the source and extracting the PowerPoint from it, as an earlier hand-built deck did;
- rendering both formats with python-pptx;
- keeping one structured source and rendering each format from it.

## Decision

`deck.yaml` is the single source. It is validated against a schema and normalised into a render model. Python renders the HTML deck from the model. A Node script renders the PowerPoint with pptxgenjs 3.12.0 from the same model, written as JSON. Both renderers use one layout grid, and a test checks that their slide count, titles and notes agree.

## Consequences

- No HTML scraping. The deck content is checkable (schema, budget, references, stated counts) before anything is rendered.
- The PowerPoint keeps real text and tables that can be edited.
- The layout is implemented twice, so the renderers can drift. A parity test guards the slide count, titles and notes; the visual parity is a manual check.
- pptxgenjs becomes a dependency of `/sa-deck` only. Without Node, the HTML deck is still produced.
