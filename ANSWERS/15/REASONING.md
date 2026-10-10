# Reasoning — Case 015

## Facts and claims

- Claim: Faster Payment 28 Aug amount_and_payee −£4,980.00 to HARROW & VALE RE LIME PROPERTY CA, ref 'MOVE IN 14 GROVE' (advance tenancy payment); bank record does not show how agency allocated it (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: DD mandate H&V COLLECT / LIME PROPERTY created 2 Sep via originator invite (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Advance notice content 9 Sep originator copy: £4,980.00 to be collected 14 September, then £795.00 monthly (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: DD collection 14 Sep amount_status −£4,980.00 paid; account £3,100 overdrawn (arranged limit £1,000; unarranged portion incurs daily fee) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Customer did_not_read_advance_notice Customer says he did not read the advance notice email (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Move-in money paid_by Bank transfer two weeks ago (all move-in money) (Customer, Phone (personal banking), `event-002`)
- Claim: Monthly rent amount £795 (Customer, Phone (personal banking), `event-002`)
- Claim: Customer agreed_to_£4,980_DD Never agreed to £4,980 by direct debit (Customer, Phone (personal banking), `event-004`)
- Claim: Advance notice email (attachment) first_collection £4,980.00 on 14 Sep 2026 described as 'balance of your account as at 8 September', then £795.00 monthly on the 14th; ref LP-14GROVE-0208; sent to t.okoye@example.net (Lime Property via H&V Collect, Email (attachment), `event-001`)

## Findings

None.

## Policy checks

- Identity: unverified (Phone (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether Lime Property received and allocated the 28 Aug £4,980 Faster Payment to the tenancy account (possible double collection)
- Why the agency stated a £4,980 balance as at 8 September despite the earlier transfer
- Whether the customer authorised the DD mandate (completed originator invite) and its terms
- Whether the £4,980 collection is a DD Guarantee error (amount differed from what was agreed) given advance notice was sent 5 days before collection
- Tenancy agreement terms on move-in amounts and payment method
- Whether cancelling the mandate leaves the £795 monthly rent unpaid and customer's awareness of this
- Whether unarranged overdraft fees should be refunded/paused
- Status of any indemnity claim or contact with Lime Property / H&V Collect
- Customer's financial hardship situation given £3,100 overdraft
- ask-1: no refund or dispute raised. Identity is unverified in the system, and whether this qualifies under the Guarantee depends on the mandate terms and the advance notice
- ask-2: mandate not cancelled because identity is unverified. Cancelling would also stop the £795 monthly rent collections
- The call note in event-002 says '[ID&V passed]', but system authority says unverified. I followed the system
- Unknown whether Lime Property allocated the 28 Aug £4,980 transfer, so this could be a double collection
- The customer may be in financial difficulty because of the unarranged overdraft and daily fees
