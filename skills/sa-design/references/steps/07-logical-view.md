---
number: 7
key: logical-view
title: Logical view
markdown: 07-logical-view.md
data: logical.yaml
schema: logical.schema.yaml
inputs: [brief.yaml, subdomains.yaml, context-map.yaml]
options:
  vendors:
    values: [none, technology-hints, named-services]
    default: none
    affects: "none = no vendor or product names; technology-hints = generic technology words allowed; named-services = products may be named"
rules: [LV-01, LV-02]
---

# Step 07 - Logical view

## Purpose

Show the system as layers of logical components and how requests and events move between them, without committing to vendors or products. It answers "what parts exist and how do they talk?" and is the base for the patterns (step 09) and the cloud mapping (step 10).

## Inputs

- `brief.yaml`: actors (clients and external systems).
- `subdomains.yaml`: the services (one component per service).
- `context-map.yaml`: which services call or listen to which.

## Propose

Lay out the layers from left to right or top to bottom:
1. **Client layer**: one component per client type (web app, mobile app, admin portal).
2. **Edge**: an API gateway and an identity provider. Clients sign in with the identity provider and get a token; every request goes to the gateway, which validates the token and routes to the owning service. Give each client type its own route set on the gateway: this is the backend-for-frontend pattern without an extra service layer.
3. **Microservice layer**: one `service` component per service in `subdomains.yaml` (`service_id` set).
4. **Messaging and data**: a message broker or event bus for commands and events (sent through an outbox), and the data stores (database per service, cache, search index, object storage).
5. **External systems**: behind an anti-corruption layer.
Number the main flows (sign in, request with token, validate token, route, commands and events, own data, external calls).
By option: `none` uses generic names only ("message broker", "search index"); `technology-hints` allows generic technology words ("relational database"); `named-services` allows product names.

## Key questions

1. How do clients reach the services? Recommended: one API gateway with separate web and mobile routes (backend-for-frontend), validating the token from the identity provider; no separate aggregation tier unless screens need heavy composition.
2. Which interactions are synchronous and which asynchronous? Recommended: synchronous for queries and the start of a command; asynchronous events for everything that can complete later or fans out.
3. Where is data from several services combined? Recommended: in read models inside the services that need it, fed by events, rather than at the edge.

## Write

- `07-logical-view.md`: Summary (the layers), Decisions (gateway and per-client routes, sync vs async, where data is combined), Details (layer table and numbered flow list), Open questions.
- `logical.yaml`: `layers` with `components` (`id`, `name`, `kind`, `service_id` for services) and numbered `flows` (`from`, `to`, `kind`, `label`).

## Checklist

- LV-01 (when `vendors = none`): no vendor or product names.
- LV-02: every service in `subdomains.yaml` appears as a service component.
- DOC-01, DOC-02 (judgement).

## Good and bad

- Good: "Client -> API gateway (validates token, web and mobile routes) -> owning service; services exchange events through a message broker."
- Bad: a logical view naming the cloud's queue, database and gateway products, transport protocols and network links.
