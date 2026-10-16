# Logical view

## Summary

Clients sign in with the identity provider and send every request with a token to the API gateway, which validates it and routes to the owning service. The gateway has separate web and mobile routes. Each of the 8 services owns its data; services exchange commands and events through a message broker; external systems sit behind an anti-corruption layer.

## Decisions

- One API gateway with web and mobile routes as the only entry point
- Queries are synchronous; the booking flow and notifications are asynchronous
- Slot search reads the directory's search index; data from several services is combined in read models

## Details

| Layer | Components |
|---|---|
| Client layer | Patient web app, Patient mobile app, Staff portal |
| Edge | API gateway with web and mobile routes, Identity provider |
| Microservice layer | Scheduling service, Appointment service, Directory service, Insurance service, Notification service, Reporting service, Payment service, Identity service |
| Messaging and data | Message broker, Database per service, Cache, Search index |
| External systems | Card payment provider, Insurer API, SMS and email provider, Corporate identity provider |

- 1. sign in, get token: patient-mobile -> identity-provider
- 2. request with token: patient-mobile -> api-gateway
- 3. validate token: api-gateway -> identity-provider
- 4. route to the owning service: api-gateway -> appointment-service
- 5. commands and events: appointment-service -> message-broker
- 6. own data: appointment-service -> service-databases
- 6. search index: directory-service -> search-index
- 7. charge and refund: payment-service -> payment-provider
- 7. cover check: insurance-service -> insurer
- 7. send reminders: notification-service -> messaging-provider
- 7. staff federation: identity-provider -> corporate-idp

## Open questions

- None
