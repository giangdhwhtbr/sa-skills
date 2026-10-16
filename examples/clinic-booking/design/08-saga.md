# Core flow (saga)

## Summary

Booking spans scheduling, insurance, payments and notifications, so the appointment service orchestrates it as a saga. Every step carries an idempotency key and each state change writes an outbox row in the same local transaction, so retries are safe and no message is lost.

## Decisions

- Orchestration by the appointment service, which owns the booking state
- Failure scenarios: a business rejection (slot taken) and a technical uncertainty (deposit timeout)
- A failed compensation is retried with the same key, then sent to a dead-letter queue with an alert

## Details

**Happy path**

1. appointment-service -> appointment-service: Save appointment as pending with an idempotency key (self)
2. appointment-service -> scheduling-service: Hold the slot for 10 minutes (async)
3. scheduling-service -> appointment-service: Slot held (async)
4. appointment-service -> insurance-service: Check cover (when the service needs it) (async)
5. insurance-service -> insurer: Cover check (sync)
6. insurance-service -> appointment-service: Cover confirmed (async)
7. appointment-service -> payment-service: Collect the deposit (async)
8. payment-service -> payment-provider: Charge the deposit with the same key (sync)
9. payment-service -> appointment-service: Deposit captured (async)
10. appointment-service -> scheduling-service: Commit the slot (async)
11. appointment-service -> notification-service: Appointment confirmed (async)

**Slot already taken**

1. appointment-service -> scheduling-service: Hold the slot (async)
2. scheduling-service -> appointment-service: Slot already taken (async)
3. appointment-service -> appointment-service: Cancel the pending appointment and offer the next free slots (compensate)

**Deposit payment times out**

1. payment-service -> payment-provider: Charge the deposit (sync)
2. payment-service -> payment-provider: Reconcile later with the same key (sync)
3. appointment-service -> scheduling-service: Release the slot hold when the hold expires unpaid (compensate)
4. appointment-service -> payment-service: Refund in full if the payment succeeds after the hold expired (compensate)

## Open questions

- None
