# Subdomains

## Summary

Six subdomains, each one service, so the design has 6 services: ordering and dispatch are core.

## Decisions

- Ordering and dispatch are core
- Kitchen is split from ordering: it runs at the restaurant and changes with it
- One service per subdomain

## Details

| Subdomain | Type | Service |
|---|---|---|
| Ordering | core | Order service |
| Dispatch | core | Dispatch service |
| Restaurant catalogue | supporting | Catalogue service |
| Kitchen | supporting | Kitchen service |
| Ratings | supporting | Rating service |
| Payments | generic | Payment service |

## Open questions

- None
