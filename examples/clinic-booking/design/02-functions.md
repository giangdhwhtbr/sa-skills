# Main business functions

## Summary

Fifteen functions in three groups: patient-facing, clinic staff and administration. The list says what the platform must provide; the booking flow itself is described in the saga.

## Decisions

- Groups by kind of user: patient, clinic staff, administration
- Deposit payment and insurance check are separate patient functions
- Reports and reminder templates belong to administration

## Details

| Group | Function | Description |
|---|---|---|
| Patient functions | Find a clinic and doctor | Search by service, location and language |
| Patient functions | View available slots | See free slots per doctor and day |
| Patient functions | Book an appointment | Choose a slot and confirm the booking |
| Patient functions | Pay a deposit | Pay the booking deposit online |
| Patient functions | Check insurance cover | Check cover with the insurer before booking |
| Patient functions | Receive reminders | Get confirmation and reminders by SMS and email |
| Patient functions | View my appointments | See upcoming and past appointments |
| Patient functions | Reschedule or cancel | Move or cancel an appointment under the policy |
| Clinic staff functions | Manage doctor schedules | Publish working hours, leave and slot lengths |
| Clinic staff functions | Check in a patient | Mark arrival and no-shows |
| Clinic staff functions | Handle cancellations and refunds | Cancel for patients and refund deposits |
| Administration functions | Manage clinics and services | Clinics, doctors, services and prices |
| Administration functions | Manage staff and roles | Staff accounts and roles from the corporate directory |
| Administration functions | View utilisation reports | Utilisation, no-shows and revenue per clinic |
| Administration functions | Configure reminder templates | Texts and timing of reminders |

## Open questions

- None
