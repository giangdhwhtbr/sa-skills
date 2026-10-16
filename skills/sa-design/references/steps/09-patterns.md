---
number: 9
key: patterns
title: Core patterns
markdown: 09-patterns.md
data: patterns.yaml
schema: patterns.schema.yaml
inputs: [logical.yaml]
options:
  split:
    values: [one-per-pattern, combined]
    default: one-per-pattern
    affects: "one-per-pattern = a separate section and view for security, observability and resilience; combined = one view for all three"
rules: [PT-01, PT-02]
---

# Step 09 - Core patterns

## Purpose

Describe the three microservices patterns every service relies on: security, observability and resilience. Each is a short numbered flow over the logical components, so reviewers see how a request is protected, traced and kept from failing in a chain.

## Inputs

- `logical.yaml`: the components each pattern passes through (client, gateway, identity provider, services, broker).

## Propose

- **Security (zero trust)**: the user signs in with the identity provider and gets a token; every call carries it; the gateway validates it and limits the rate; each service checks roles and resources again through one shared library, so no request is trusted for being inside the network; calls between services use encrypted connections and carry the caller's identity; secrets come from a secrets store, never from code.
- **Observability**: every service sends traces, metrics and structured logs through a standard telemetry SDK; trace context travels across synchronous calls and through the outbox for events; alarms notify the on-call team; one business transaction can be followed by its trace ID.
- **Resilience**: every outbound call passes a timeout, a retry with backoff and jitter, a circuit breaker and a bulkhead; when the circuit is open, a fallback answers with cached data or a clear message; health checks restart unhealthy instances; failed messages go to a dead-letter queue.
- Under `one-per-pattern`, give each pattern its own section (and its own view in a presentation); under `combined`, one section with three sub-flows.

## Key questions

1. Where is authorization enforced? Recommended: token validation at the gateway and role and resource checks in every service through one shared library; the gateway alone is not enough.
2. What must be traceable end to end? Recommended: the core flow from step 08, including its asynchronous steps.
3. Which outbound calls need protection? Recommended: every call to another service or an external system; tune timeouts per dependency.

## Write

- `09-patterns.md`: one section per pattern (Summary, numbered flow, decisions), Open questions.
- `patterns.yaml`: `patterns` with `id` (`security`, `observability`, `resilience`), `summary`, numbered `steps` (`from`, `to`, `text`).

## Checklist

- PT-01: security, observability and resilience are each described.
- PT-02 (judgement, when `split = one-per-pattern`): each pattern has its own section and view.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "R1-R5: timeout -> retry with jitter -> circuit breaker -> bulkhead -> callee; R6: fallback when the circuit is open."
- Bad: one box labelled "Security, logging and retries handled by the platform".
