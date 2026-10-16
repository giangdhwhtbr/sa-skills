# Core patterns

## Summary

Three patterns apply to every service: security follows zero trust, observability follows one booking across all services, and resilience contains partner failures so they never stop booking in every clinic.

## Decisions

- Authorization is checked in every service through one shared library, not only at the gateway
- The core booking flow is traced end to end, including its asynchronous steps
- Every call to a partner is protected; the insurer has a fallback

## Details

### Security

Zero trust: tokens from the identity provider, checked at the gateway and again in every service

1. patient-mobile -> identity-provider: Sign in and get a token; staff federate through the corporate identity provider
2. patient-mobile -> api-gateway: Every call carries the token
3. api-gateway -> appointment-service: The gateway validates the token and the service checks roles and resources

### Observability

Traces, metrics and structured logs from every service; one trace follows a booking

1. appointment-service -> message-broker: Trace context travels with commands and events through the outbox
2. appointment-service -> appointment-service: Metrics and alarms notify the on-call team

### Resilience

Timeouts, retries with jitter, circuit breakers and bulkheads on every outbound call

1. payment-service -> payment-provider: Timeout, retry with backoff and jitter, circuit breaker
2. insurance-service -> insurer: When the circuit is open, book without the check and verify later

## Open questions

- None
