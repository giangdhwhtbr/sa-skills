---
number: 10
key: architecture
title: Architecture (high-level and physical)
markdown: 10-architecture.md
data: architecture.yaml
schema: architecture.schema.yaml
inputs: [logical.yaml, patterns.yaml]
options:
  shared-layout:
    values: [true, false]
    default: true
    affects: "true = the high-level and physical views use the same groups in the same order so readers can map blocks between them"
rules: [AR-01, AR-02, AR-03]
---

# Step 10 - Architecture (high-level and physical)

## Purpose

Map the logical components to the services of the chosen cloud, and describe two views: the high-level microservices architecture and the physical deployment and network. This is the first step that names cloud services, using `references/profiles/<cloud>.md`.

## Inputs

- `logical.yaml`: every component to map.
- `patterns.yaml`: the security, observability and resilience pieces that need a home (identity provider, secrets store, telemetry, alarms).
- The cloud profile named in `sa-config.yaml` (`cloud`).

## Propose

- **Mapping**: for every logical component of kind gateway, identity-provider, broker and datastore (and the patterns' pieces), the cloud service from the profile, with a note when there is a real choice.
- **Shared layout** (option `true`): use the same groups, in the same order, in both views, for example `Clients, Edge, Microservices, Data, Managed services, External systems`. The high-level view shows logical blocks; the physical view shows the same blocks as cloud resources inside regions, availability zones and subnets.
- **Physical and network**: number of regions and availability zones (two zones at least for the availability target); subnet tiers (public, app, data) with example address ranges; only the public tier has an internet route, the app tier goes out through NAT, the data tier has no internet route; security rules where each tier accepts traffic only from the tier before it; private endpoints to managed services; a VPN or private link for on-premises systems.
- The network topology belongs in this step: one physical view carries the tiers, routes and security rules, so no separate network view is needed.

## Key questions

1. Which cloud service implements each logical component? Recommended: the managed service from the profile unless a constraint in the brief says otherwise.
2. How many regions and availability zones? Recommended: one region and two zones unless the brief requires multi-region or data residency.
3. Should the high-level and physical views share one layout? Recommended: yes, so every block in one view can be found in the other.

## Write

- `10-architecture.md`: Summary, Decisions (mapping choices, zones, tiers), Details (mapping table; high-level view groups; physical view: regions, zones, tiers with routes and address ranges, security rules), Open questions.
- `architecture.yaml`: `cloud`, `mapping`, `high_level.groups`, `physical` (`regions`, `availability_zones`, `groups`, `tiers`, `security_rules`).

## Checklist

- AR-01: every gateway, identity-provider, broker and datastore component maps to a cloud service.
- AR-02 (when `shared-layout = true`): `high_level.groups` and `physical.groups` are the same list in the same order.
- AR-03: a tier named data has no internet route.
- DOC-01, DOC-02 (judgement): titles match the views; no text about how the layout was chosen in review.

## Good and bad

- Good: both views list Clients, Edge, Microservices, Data, Managed services, External systems from left to right; the physical view adds zones and tiers around the same blocks.
- Bad: the physical view groups resources by team or by cost centre, so no block can be matched to the high-level view.
