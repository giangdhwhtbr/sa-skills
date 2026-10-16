# Tests: SA deck

Automated tests carry the REQ-ID in the test name or a comment. List here only manual or QE cases.

| TC | REQ | type | evidence |
|---|---|---|---|
| TC-01 | REQ-DECK-008 | manual | open examples/clinic-booking/design/deck/deck.html in a browser: arrow keys, Home/End, #n, N notes panel, total time; print to PDF gives one slide per page without the status bar |
| TC-02 | REQ-DECK-009, REQ-DECK-004 | manual | open deck.pptx in PowerPoint or Keynote: same slides, titles and speaker notes as the HTML deck; tables and text are editable |
| TC-03 | REQ-DECK-005, REQ-DECK-010 | manual | diagrams are readable at slide size, legend chips match each diagram, theme colours and font applied in both formats |
| TC-04 | REQ-DECK-002, REQ-DECK-006 | manual | run /sa-deck on examples/clinic-booking with a 20-minute budget; the drafted deck stays within budget and every script fits its seconds |
