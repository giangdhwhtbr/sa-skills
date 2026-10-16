# Subdomains

## Summary

The domain splits into 8 subdomains: 2 core, 4 supporting and 2 generic. Each subdomain is one service, so the design has 8 services and every business area has one owner.

## Decisions

- Scheduling and appointments are core: they decide whether a patient gets a slot
- Scheduling is split from appointments: schedules change daily and are owned by clinics
- Payments and identity are generic: integrate the provider and the corporate directory
- One service per subdomain (option service-per-subdomain = one)

## Details

| Subdomain | Type | Service | Functions |
|---|---|---|---|
| Scheduling | core | Scheduling service | view-available-slots, manage-doctor-schedules |
| Appointments | core | Appointment service | book-appointment, view-my-appointments, reschedule-or-cancel, check-in-patient, handle-cancellations-and-refunds |
| Clinic directory | supporting | Directory service | find-clinic-and-doctor, manage-clinics-and-services |
| Insurance verification | supporting | Insurance service | check-insurance |
| Notifications | supporting | Notification service | receive-reminders, configure-reminder-templates |
| Reporting | supporting | Reporting service | view-utilisation-reports |
| Payments | generic | Payment service | pay-deposit |
| Identity | generic | Identity service | manage-staff-and-roles |

## Open questions

- None
