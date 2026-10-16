# Use cases

## Summary

Fourteen use cases cover every function: seven for patients, three for receptionists and four for clinic administrators. External systems take part where they act.

## Decisions

- Booking always includes paying the deposit
- The insurance check extends booking for services that need it
- Every function from step 02 is covered by at least one use case

## Details

| Use case | Actors | Includes / extends |
|---|---|---|
| Find a doctor | patient | - |
| Pay the deposit | patient, payment-provider | - |
| Book an appointment | patient | uc-pay-deposit |
| Check insurance cover | patient, insurer | uc-book-appointment |
| View my appointments | patient | - |
| Reschedule or cancel | patient | - |
| Receive a reminder | patient, messaging-provider | - |
| Manage doctor schedules | receptionist | - |
| Check in a patient | receptionist | - |
| Handle a cancellation and refund | receptionist, payment-provider | - |
| Manage clinics and services | clinic-admin | - |
| Manage staff and roles | clinic-admin, corporate-idp | - |
| View utilisation reports | clinic-admin | - |
| Configure reminder templates | clinic-admin | - |

## Open questions

- None
