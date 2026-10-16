# Context map

## Summary

Ordering is downstream of the catalogue and payments and upstream of kitchen, dispatch and ratings, which react to its events.

## Decisions

- Upstream owns the data or rule
- Detail: ud-only

## Details

| Upstream (U) | Downstream (D) | Pattern |
|---|---|---|
| restaurant-catalog | ordering | customer-supplier |
| payments | ordering | customer-supplier |
| ordering | kitchen | domain-events |
| ordering | dispatch | domain-events |
| kitchen | dispatch | domain-events |
| ordering | ratings | domain-events |

## Open questions

- None
