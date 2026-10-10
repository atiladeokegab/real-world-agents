# Answer — Case 022

## Decision

ESCALATED — Handed to Card operations (stale linked authorisation investigation), with case desk supervisor copied for customer care: The customer is distressed, getting more frustrated and says she needs the money for groceries today. She wants the £600 AUTH-022 reservation released after the £520 FINAL-022 debit was booked. Under the procedure in event-010, case desk cannot release a hold. Only card operations can, after checking linkage and current network state. Her identity is also unverified on the system authority. Event-011 came through an unlabelled chat, not the authenticated session in event-007, so case desk should not share account details in its reply.

## What we received

`index.md`, `history.md`, `attachments/card-entries.csv`, `attachments/hotel-receipt.pdf` · 2 attachments · 11 events · identity: unverified Rois Fenwick (Customer chat)

## Actions

None.

## Answer to the question

Question: No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

I recommend escalating to card operations now, marked high urgency, and sending the customer a holding reply through the secure portal or a verified call. Case desk can't release the £600 AUTH-022 hold, the customer is distressed and getting more frustrated, and her latest message (event-011) came through a chat not marked as authenticated, so we shouldn't share balance details there. The ledger strongly suggests the £600 is a leftover hold, since only £520 (FINAL-022) is booked against AUTH-022, but whether it can be released, and whether that can happen today, isn't known until card operations finishes its checks. I'm confident about who should handle this and less sure about the timing.

## Customer reply

Channel: Customer chat

We understand this is urgent and that you need this money for groceries. We've passed your request about the £600 to our card operations team, which is the only team that can look at it. We'll contact you through your secure portal or a verified call once they've confirmed. Please use the secure portal or a verified call if you need to reach us in the meantime.

## Not done

- Did not release or promise to release the £600 hold, because case desk has no authority to do so (event-010)
- Did not promise the funds today, because timing depends on card operations checks
- Did not explain the balance breakdown (ask-2) to the customer, because identity is unverified on the latest channel
- Did not raise a card dispute; the merchant receipt matches the £520 debit — because the case was handed to a person
- no change made to the account — because the case was handed to a person

## Evidence used

- `event-002`
- `event-003`
- `event-004`
- `event-005`
- `event-006`
- `event-007`
- `event-008`
- `event-009`
- `event-010`
- `event-011`

## Handover

**Take it:** Card operations (stale linked authorisation investigation), with case desk supervisor copied for customer care

**Urgency:** Today

**Type:** Emotional

**Verified:**
- Ledger shows card_debit FINAL-022 GBP -520.00 booked 08:30, linked to AUTH-022 (event-002)
- Ledger shows authorisation_reservation AUTH-022 GBP 600.00 active as of 09:00 (event-003)
- Ledger balance snapshot GBP 980.00 and available balance snapshot GBP 380.00 at 09:00 (event-004, event-005)
- Procedure: case desk may request investigation but cannot release a hold; timing depends on card operations checks (event-010)
- identity unverified via channel, role Rois Fenwick

**Only claimed:**
- Customer says the hotel took £600 and £520 (£1,120) and that the stay cost £520 (event-007)
- Hotel receipt and email say the final card amount is GBP 520.00, payment reference FINAL-022, authorisation reference AUTH-022 (event-008, event-009)
- Internal card view records the account holder as Rois Fenwick and contact authentication as passed (event-006), but the system authority shows identity unverified
- Account SYN-ACCT-B022 opening_ledger GBP 1500.00, reference OPEN, booked (Brackenfold Bank, event-001)
- Account SYN-ACCT-B022 card_debit GBP -520.00, reference FINAL-022, linked authorisation AUTH-022, booked at 08:30 (Brackenfold Bank, event-002)
- Account SYN-ACCT-B022 authorisation_reservation GBP 600.00, reference AUTH-022, linked authorisation AUTH-022, status active as of 09:00 (Brackenfold Bank, event-003)
- Account SYN-ACCT-B022 ledger_balance GBP 980.00 snapshot at 09:00 (Brackenfold Bank, event-004)
- Account SYN-ACCT-B022 available_balance GBP 380.00 snapshot at 09:00 (Brackenfold Bank, event-005)
- Rois Fenwick account_holder_and_authentication Account holder is Rois Fenwick; current contact authentication recorded as passed (Brackenfold Bank card ledger, event-006)
- Alderclock Hotel charges amount_taken Hotel took £600 and £520, total £1,120 (Rois Fenwick, event-007)
- Alderclock Hotel stay SYN-HOTEL-022 final_amount_paid_by_card GBP 520.00, payment reference FINAL-022, authorisation reference AUTH-022, stay 2026-11-07 to 2026-11-10 (Alderclock Hotel, event-008)

**Conflicts:**
- event-007 (customer: £1,120 taken) vs event-002/event-003/event-004 (ledger: only £520 debited; £600 is an active reservation, not a debit)
- event-003 reservation recorded at 09:00, after the 08:30 final debit event-002; the reason is unknown
- event-006/event-007 show authenticated contact vs system authority identity unverified and event-011 unlabelled chat
- event-007 conflicts with event-008: Hotel took £600 and £520, total £1,120 vs GBP 520.00, payment reference FINAL-022, authorisation reference AUTH-022, stay 2026-11-07 to 2026-11-10
- event-007 conflicts with event-009: Hotel took £600 and £520, total £1,120 vs £520; stay ended this morning

**We did:**
- Reviewed ledger entries, card-entries.csv, the hotel receipt, the merchant email and the card servicing procedure
- Prepared this handover asking card operations to investigate AUTH-022

**We did not:**
- Did not release or promise to release the £600 hold, because case desk has no authority to do so (event-010)
- Did not promise the funds today, because timing depends on card operations checks
- Did not explain the balance breakdown (ask-2) to the customer, because identity is unverified on the latest channel
- Did not raise a card dispute; the merchant receipt matches the £520 debit
- no change made to the account

**Question for you:** Is AUTH-022 (GBP 600.00, active) a stale linked authorisation, given that FINAL-022 (GBP 520.00) is booked against it? Is it eligible for release after your linkage and network-state checks, and can it be released today? Please also confirm that the customer is authenticated on a verified channel before we explain the balance to her.

**Safe to send now:** We understand this is urgent and that you need this money for groceries. We've passed your request about the £600 to our card operations team, which is the only team that can look at it. We'll contact you through your secure portal or a verified call once they've confirmed. Please use the secure portal or a verified call if you need to reach us in the meantime.

## What failed

Nothing.
