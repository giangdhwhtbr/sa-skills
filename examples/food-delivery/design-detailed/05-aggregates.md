# Aggregate roots

## Summary

One aggregate root per subdomain; roots refer to each other by ID and Order is the hub. Each root lists its entities, value objects and domain events.

## Decisions

- Order is the hub
- Detail: full

## Details

| Subdomain | Root | Entities | Value objects | Events |
|---|---|---|---|---|
| ordering | Order | OrderLine | Money, DeliveryAddress | OrderPlaced, OrderDelivered |
| dispatch | DeliveryJob | RouteLeg | GeoPoint | CourierAssigned, Delivered |
| restaurant-catalog | Restaurant | MenuItem | OpeningHours | MenuChanged |
| kitchen | KitchenTicket | - | PrepTime | OrderAccepted, OrderReady |
| ratings | Rating | - | Score | OrderRated |
| payments | Payment | Refund | Money | PaymentCaptured |

## Open questions

- None
