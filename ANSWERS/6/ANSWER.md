# Answer — Case 006

## Decision

ESCALATED — Handed to Fraud & Financial Crime – Misdirected Payments / Funds Recovery team: This looks like a possible refund scam or money-mule attempt. A £750 FPS credit came from R JAMES (Meridian, SYN-SC-06-2/SYN-ACCT-06-2). An unknown mobile number has now asked the customer to send the money to a different account (SYN-SC-06-3/SYN-ACCT-06-1), and the CoP check on that account came back No match (ANNM). Meridian has not sent a funds-recovery request. The customer is 20, a student and flagged as vulnerable. She wants to send the money now, so the risk is that she pays it to a fraudster herself.

## What we received

`index.md`, `history.md`, `attachments/cop_check_text_details.json`, `attachments/inbound_payment_message.json`, `attachments/sms_screenshot.png` · 3 attachments · 4 events · identity: unverified Bank customer (In-app chat (personal banking))

## Actions

None.

## Customer reply

Channel: In-app chat (personal banking)

Thank you for checking with us first. Please don't send any money to the account in the text message, and please don't reply to that number. If money has to go back, we'll handle it ourselves through our funds-recovery process with the sender's bank, so you don't need to move anything yourself. We've passed this to our specialist team and we'll reply here.

## Not done

- Did not start or advise any transfer to the account in the text — because the case was handed to a person
- Did not raise a return_request: the customer is unverified, there is no Meridian recovery request and fraud review is needed first — because the case was handed to a person
- Did not confirm to the customer whether the payment is genuine or fraudulent — because the case was handed to a person
- Could not read sms_screenshot.png (image not extracted) — because the case was handed to a person
- no change made to the account — because the case was handed to a person

## Evidence used

- `event-001`
- `event-002`
- `event-003`
- `event-004`

## Handover

**Take it:** Fraud & Financial Crime – Misdirected Payments / Funds Recovery team

**Urgency:** Today

**Type:** Emotional

**Verified:**
- Credit +£750.00 FPS from R JAMES, Meridian Bank, ref RENT, 26 Sep 22:14, E2E MER26092622143198 (event-001, inbound_payment_message.json)
- No funds-recovery request received from Meridian (event-001)
- CoP check on the account in the text: No match, ANNM, checked 2026-09-28T09:52:40Z (event-001, cop_check_text_details.json)
- The return account in the text is not the originating payer account (event-001)
- identity unverified via channel, role Bank customer

**Only claimed:**
- Customer says the payment was sent by mistake and the texter said it was their rent (event-002)
- Customer says she has not touched the funds (event-002)
- Texter claims to be 'Ryan' / R James and asks for the money to go to 'my other account' (event-001, forwarded SMS)
- Customer's identity is unverified on this case (authority)
- Incoming payment credited +£750.00 Faster Payment from 'R JAMES' (Meridian Bank), ref 'RENT', 26 Sep 22:14 (Harrow & Vale Bank plc (case record), event-001)
- Funds recovery request received from Meridian No inbound funds-recovery request received (Harrow & Vale Bank plc (case record), event-001)
- Text message from unknown mobile requests return to A different account: SYN-SC-06-3, SYN-ACCT-06-1, R James (claims to be Ryan, payment meant for landlord) (Unknown texter ('Ryan'), event-001)
- CoP check on text details result No match (ANNM) - account name held is not 'R James' (Harrow & Vale Bank plc (case record), event-001)
- Payment was sent By accident, payer says it was their rent (Customer, event-002)
- Funds usage Customer has not touched the £750 (Customer, event-002)
- Return account differs from originating account Texter gave a different account from the one the payment came from (Customer, event-004)
- Payer account details R JAMES, SYN-SC-06-2 / SYN-ACCT-06-2, Meridian Bank; E2E MER26092622143198; recovery_request_received false (FPS inbound payment message, event-001)

**Conflicts:**
- The texter says the receiving account belongs to R James, but CoP says the account name is not R James (event-001)
- The texter asks for the money to go to a different account from the payer account on the FPS message (event-001, event-004)

**We did:**
- Reviewed the case record, the FPS inbound message and the CoP result
- Gave the customer no account or payment status beyond what she already knows

**We did not:**
- Did not start or advise any transfer to the account in the text
- Did not raise a return_request: the customer is unverified, there is no Meridian recovery request and fraud review is needed first
- Did not confirm to the customer whether the payment is genuine or fraudulent
- Could not read sms_screenshot.png (image not extracted)
- no change made to the account

**Question for you:** Should this £750 credit (E2E MER26092622143198) be held and sent back only to the originating Meridian account through the funds-recovery process, or does it need fraud or mule review first? And what should the customer be told to do about the texter?

**Safe to send now:** Thank you for checking with us first. Please don't send any money to the account in the text message, and please don't reply to that number. If money has to go back, we'll handle it ourselves through our funds-recovery process with the sender's bank, so you don't need to move anything yourself. We've passed this to our specialist team and we'll reply here.

## What failed

Nothing.
