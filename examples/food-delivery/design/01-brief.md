# Brief

## Summary

A food-delivery platform connects customers, restaurants and couriers. The design must stop lost orders, assign couriers automatically and stay fast at meal peaks.

## Decisions

- Three pain points kept, ordered by impact
- Both external systems listed: payment and maps
- Numbers set for durability, latency and peak load

## Details

| Pain point | Description |
|---|---|
| pp-lost-orders | Orders are lost when a restaurant tablet is offline |
| pp-manual-dispatch | A dispatcher assigns couriers by chat |
| pp-peak-slowness | The single application slows down for everyone at peaks |

## Open questions

- None
