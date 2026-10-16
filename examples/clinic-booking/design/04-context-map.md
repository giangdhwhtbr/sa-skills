# Context map

## Summary

Appointments is downstream of scheduling, payments, insurance verification and identity, so those teams keep their contracts stable. Appointments and scheduling publish events that notifications and reporting consume.

## Decisions

- Upstream is the context that owns the data or rule
- Detail kept at ud-only for a high-level design
- No two-way relationships: commands one way, events the other

## Details

| Upstream (U) | Downstream (D) | Label |
|---|---|---|
| clinic-directory | scheduling | doctors and services |
| scheduling | appointments | slot holds |
| payments | appointments | deposit collection |
| insurance-verification | appointments | cover checks |
| identity | appointments | patient identity |
| appointments | notifications | appointment events |
| appointments | reporting | appointment events |
| scheduling | reporting | schedule events |

## Open questions

- None
