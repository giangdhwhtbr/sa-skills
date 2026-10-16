# Aggregate roots

## Summary

One aggregate root per subdomain; roots refer to each other by ID and Order is the hub.

## Decisions

- Order is the hub
- Detail: roots-only

## Details

| Subdomain | Root |
|---|---|
| ordering | Order |
| dispatch | DeliveryJob |
| restaurant-catalog | Restaurant |
| kitchen | KitchenTicket |
| ratings | Rating |
| payments | Payment |

## Open questions

- None
