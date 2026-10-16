# Brief

## Summary

A 40-clinic outpatient network replaces its phone-and-spreadsheet booking with online self-service for patients and one schedule source for staff. The design must end double bookings and phone-only booking, allow independent releases, and keep booking available when a partner system fails.

## Decisions

- Five pain points kept, ordered by business impact (recommended: 3-6 that the design must visibly answer)
- All four external systems listed now: payment, insurer, messaging, corporate identity
- Numbers set for availability, search latency, peak load and data residency
- Hard constraints: corporate staff sign-in and regional patient data

## Details

| Pain point | Description |
|---|---|
| pp-double-booking | Schedules live in per-clinic spreadsheets, so double bookings happen weekly |
| pp-phone-only | Patients can only book by phone during opening hours |
| pp-monolith-releases | One deployable and one database; every change needs a full regression and a weekend release |
| pp-outage-spread | When the card-payment integration hangs, nobody can book in any clinic |
| pp-no-shows | Reminders are sent by hand, so no-shows are high |

| Actor | Kind |
|---|---|
| Patient | person |
| Receptionist | person |
| Clinic administrator | person |
| Card payment provider | system |
| Insurer API | system |
| SMS and email provider | system |
| Corporate identity provider | system |

| NFR | Target |
|---|---|
| availability | 99.9% monthly |
| latency | slot search under 1 s for 95% of requests |
| peak load | Monday 8:00 peak at 20 times the average |
| data residency | patient data stays in the home region |

## Open questions

- Confirm the deposit and refund policy with the business
