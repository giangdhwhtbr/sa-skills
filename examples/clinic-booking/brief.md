# Sample brief: clinic booking platform (fictional)

A network of 40 outpatient clinics wants to replace its in-house appointment system.

**Today.** Each clinic keeps doctors' schedules in a spreadsheet that receptionists copy into a shared desktop application. Patients can only book by phone during opening hours. The application is one deployable with one database; every change needs a full regression and a weekend release. When the card-payment integration hangs, nobody can book in any clinic. Double bookings happen several times a week and no-shows are high because reminders are sent by hand.

**Target.**
- Patients find a clinic and doctor, see free slots, book online (web and mobile), pay a deposit, and get reminders by SMS and email. They can view, reschedule or cancel their appointments.
- Before booking certain services, the patient's insurance cover is checked with the insurer's API.
- Receptionists manage doctors' schedules, check patients in and handle cancellations and refunds.
- Clinic administrators manage clinics, services, staff and roles, reminder templates, and view utilisation reports.
- Staff sign in with the group's corporate identity provider; patients have their own accounts or book as guests.

**Quality targets.** 99.9% monthly availability; slot search under 1 second for 95% of requests; Monday 8:00 peaks reach 20 times the average load; patient data stays in the home region.

**External systems.** Card payment provider, insurer API, SMS and email provider, corporate identity provider.
