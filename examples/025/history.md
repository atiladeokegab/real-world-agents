# Case 025 history — Why a Card Attempt Was Declined

Total events: 6

<a id="event-001"></a>
## 2025-09-05 09:00:00 UTC — event 001

- **Channel:** External message
- **From:** North Quay Books payment terminal
- **To:** Mara Ellison

Payment not accepted. Please contact your bank.

<a id="event-002"></a>
## 2025-09-05 09:47:00 UTC — event 002

- **Channel:** Verified call
- **From:** H&V agent
- **To:** Mara Ellison

I’ve completed the required identification checks. Please tell me which declined attempt you want me to investigate; I won’t ask you to share any secret codes.

<a id="event-003"></a>
## 2025-09-05 10:34:00 UTC — event 003

- **Channel:** Verified call
- **From:** Mara Ellison
- **To:** H&V agent

I’m calling to find out why my £18.40 payment at North Quay Books was declined. Please check that particular attempt.

<a id="event-004"></a>
## 2025-09-05 11:21:00 UTC — event 004

- **Channel:** Internal note
- **From:** H&V agent
- **To:** H&V card authorisation journal

I’m searching the journal for Mara Ellison’s North Quay Books authorisation attempt for £18.40, using the merchant and amount she identified. I’ll check the recorded response for that attempt.

<a id="event-005"></a>
## 2025-09-05 12:08:00 UTC — event 005

- **Channel:** Internal note
- **From:** H&V card authorisation journal
- **To:** H&V agent

Matching authorisation found: declined because available balance was insufficient to cover the £18.40 authorisation at the time of the attempt.

<a id="event-006"></a>
## 2025-09-05 12:55:00 UTC — event 006

- **Channel:** Secure portal
- **From:** H&V
- **To:** Mara Ellison

Case HV-025: The North Quay Books card attempt for £18.40 was declined because your available balance was insufficient to cover the authorisation at the time. No new payment has been made, and we can’t guarantee that a future attempt will be successful.
