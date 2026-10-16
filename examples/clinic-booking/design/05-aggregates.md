# Aggregate roots

## Summary

Each subdomain has one aggregate root except reporting, which only builds read models. Roots refer to each other by ID; Appointment is the hub of the core flow.

## Decisions

- DoctorSchedule owns slots and holds, so a slot can only be held once
- Reporting has no aggregate
- References by ID only (option detail = roots-only)

## Details

| Subdomain | Root |
|---|---|
| clinic-directory | Clinic |
| scheduling | DoctorSchedule |
| appointments | Appointment |
| insurance-verification | InsuranceCheck |
| notifications | Reminder |
| payments | Payment |
| identity | UserAccount |

| From | To | Via | Multiplicity |
|---|---|---|---|
| doctor-schedule | clinic | clinicId | * : 1 |
| appointment | doctor-schedule | scheduleId | * : 1 |
| appointment | user-account | patientId | * : 1 |
| payment | appointment | appointmentId | * : 1 |
| insurance-check | appointment | appointmentId | 1 : 1 |
| reminder | appointment | appointmentId | * : 1 |

## Open questions

- None
