# Default deck outline

`deck.py <design> --outline --minutes N` prints a draft `deck.yaml` in this order. A slide appears only if its source step is `done`. The author fills every `message` and `notes`, completes the empty table cells, then cuts or reorders slides to fit the talk.

General rules for every slide:
- **Message:** one line, at most 140 characters. It states the point of the slide, not its topic ("Each subdomain is owned by one service", not "Subdomains").
- **Notes:** the spoken script, in short sentences, one idea per sentence. It runs at about 130 words per minute: 60 seconds is about 130 words.
- **Facts:** every fact comes from the design documents and data. Never invent numbers, names or decisions. A count of services must match `subdomains.yaml`.
- **Problem and answer:** name the pattern or decision, and the problem it solves.

| Section | Slide | Block | Source | Key message should say | Script should cover |
|---|---|---|---|---|---|
| (cover) | Title, subtitle, presenter, date | — | `meta` | — | who you are, what the talk covers, in 2–3 sentences |
| Agenda | Agenda | `agenda` | section titles | the storyline (e.g. "From the problem to the architecture, following the 4+1 views") | the order of the talk in one or two sentences per section |
| Introduction | Proposed solution | `table` (Problem, Answer) | `brief.yaml` pain points; answers from subdomains, patterns and ADRs | how many problems, solved by which kind of design | each problem, then the pattern or decision that answers it |
| Introduction | Main business functions | `diagram` functions | `02-functions` | who uses the system and for what | each actor group and its main functions |
| Domain design | Subdomains | `diagram` subdomains | `03-subdomains` | core vs supporting vs generic, one service each | why the core subdomains are core |
| Domain design | Context map | `diagram` context-map | `04-context-map` | which contexts are upstream of the core | the main upstream/downstream relationships and why |
| Domain design | Aggregate roots | `diagram` aggregates | `05-aggregates` | aggregates refer to each other by ID | the central aggregate and its references |
| Use case view | One per actor group | `diagram` use-cases page n | `06-use-cases` | what this actor group can do | the main use cases and the external systems involved |
| Logical view | Logical view | `diagram` logical-view | `07-logical-view` | the layers and the main interaction rule | the request path through the layers, by the numbered flows |
| Process view | One per saga scenario | `diagram` saga page n | `08-saga` | the outcome of the scenario | the numbered steps; for failures, the compensations |
| Core patterns | One per pattern (or one combined) | `diagram` patterns page n | `09-patterns` | the pattern in one line | the numbered steps of the pattern |
| High-level and physical view | High-level architecture | `diagram` architecture 1 | `10-architecture` | how clients reach services and data | groups from left to right |
| High-level and physical view | Physical view and network | `diagram` architecture 2 | `10-architecture` | where it runs and how the network is split | region, zones, subnet tiers and security rules |
| Development view | Technology stack | `table` (Layer, Choice, Why) | `stack.yaml` | the main technology choices | one line per layer: the choice and why |
| Development view | Architecture decisions | `table` (Decision, Alternatives, Trade-off) | `adrs.yaml` | the decisions that shape the design | the trade-off of each decision |
| Q&A | Questions | — | — | — | thank the audience and invite questions |

**Seconds.** The default weights are: cover 20, agenda 25, table 75, diagram 70, title-only 20. When they add up to more than the budget, every slide is scaled down to fit, in steps of 5 seconds and never below 15.

**Other blocks.**
- `diagrams`: two pages side by side, e.g. high-level next to physical.
- `diagram-text`: a page with 2–4 points beside it.
- `bullets`: up to 6 points.
- `image`: a PNG or JPEG inside `design/deck/`.
