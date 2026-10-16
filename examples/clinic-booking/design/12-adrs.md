# Architecture decisions

## Summary

Seven decisions answer the five pain points; each names the alternatives and the trade-off accepted.

## Decisions

- Decisions phrased against real alternatives
- Every pain point is answered by at least one decision

## Details

### One service per subdomain

- Decision: Split the platform into 8 services, one per subdomain
- Instead of: One modular deployable; A service per aggregate
- Trade-off: More services to run, deploy and monitor
- Why: A change touches one service and releases independently
- Pain points: pp-monolith-releases

### Slots held and committed by the scheduling service

- Decision: Scheduling is the only owner of slots; booking holds a slot for 10 minutes, then commits it
- Instead of: Lock rows in a shared database; Optimistic booking with later conflict resolution
- Trade-off: A hold can expire while the patient pays
- Why: A slot can only be held once, which ends double bookings
- Pain points: pp-double-booking

### Orchestrated booking saga

- Decision: The appointment service orchestrates booking as a saga with compensation
- Instead of: Choreography with events only
- Trade-off: The appointment service becomes a central component
- Why: One place shows and recovers every booking
- Pain points: pp-double-booking

### Outbox and idempotency keys

- Decision: Every state change writes an outbox row in the same local transaction; every command carries an idempotency key
- Instead of: Two-phase commit; Dual writes
- Trade-off: Eventual consistency; consumers must deduplicate
- Why: No message is lost and retries are safe
- Pain points: pp-outage-spread

### One API gateway with web and mobile routes

- Decision: One managed gateway is the only entry point, with separate web and mobile routes
- Instead of: Clients calling services directly; A GraphQL layer
- Trade-off: No response composition at the edge
- Why: Self-service channels with one security and rate-limit point; read models combine data
- Pain points: pp-phone-only

### Isolate partner calls

- Decision: Every partner call goes through timeouts, retries, circuit breakers and bulkheads, with fallbacks
- Instead of: Synchronous calls without protection
- Trade-off: More code paths and tuning per partner
- Why: A hanging partner no longer stops booking in every clinic
- Pain points: pp-outage-spread

### Event-driven reminders

- Decision: The notification service sends confirmations and reminders from appointment events
- Instead of: Reminders sent by staff; A nightly batch export
- Trade-off: Another service to run
- Why: Reminders go out on time without staff effort
- Pain points: pp-no-shows

## Open questions

- None
