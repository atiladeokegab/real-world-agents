# Reasoning — Case 004

## Facts and claims

- Claim: September rent taken twice £1,000 on the 1st and £900 on the 3rd (Customer, In-app chat (personal banking), `event-002`)
- Claim: £900 Direct Debit authorised by customer Customer says she never agreed to £900 (Customer, In-app chat (personal banking), `event-002`)
- Claim: Rent amount is £1,000; the landlord has the amount wrong (Customer, In-app chat (personal banking), `event-002`)
- Claim: £900 Direct Debit collection is an error Customer says it is an error and that the guarantee requires an immediate refund (Customer, In-app chat (personal banking), `event-004`)
- Claim: Direct Debit mandate H&V COLLECT / HARBOUR LETS created 20 Aug 2026 via originator invite (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Direct Debit advance notice sent 24 Aug: £900.00 to be collected on or around 3 September, then monthly (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: 3 Sep Direct Debit collection amount matches advance notice £900.00 matches the notice (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Standing order to HARROW & VALE RE HARBOUR LETS LTD CA, ref RENT 27 ELM RD status £1,000 monthly on the 1st, set up Feb 2025, still active for 1 Oct (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Advance notice email (dd_advance_notice_2026-08-24.eml) advises Cancel any rent standing order before the first collection to avoid paying twice; the DD Guarantee applies; ref HL-27ELM-0091 (Harbour Lets via H&V Collect (attachment), Attachment, `event-001`)
- Claim: Case payments duplicates check (finding-1) Case text describes a possible duplicate payment/instruction (Evidence check (code), Findings, `event-002`)

## Findings

- **finding-1 · duplicates** (anomaly) — the case text describes a possible duplicate payment/instruction (event-002). Addressed.

## Policy checks

- Identity: unverified (In-app chat (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

conflicting_records → report both, claim neither; route the check to the owning team

## Alternatives rejected

None.

## Uncertainties

- Whether the customer completed/authorised the DD mandate created via the originator invite on 20 Aug 2026
- Whether the customer received the 24 Aug advance notice email
- Which instruction (standing order or Direct Debit) the landlord intends rent to be paid by, and whether the DD was meant to replace the SO
- The correct rent amount under the tenancy (£1,000 per customer vs £900 per DD notice)
- Whether a DD Guarantee indemnity claim is valid when the amount collected matches the advance notice
- Whether Harbour Lets has been contacted or will refund the overpayment directly
- Whether the customer also wants the £1,000 standing order (next payment 1 Oct) cancelled or kept
- Whether the £900 is a duplicate of the September rent or a different charge
- ask-1 (DDG refund today) is not done. Identity is unverified, and the record shows the £900 matches the advance notice, so the indemnity may not apply. Passed to the DD team.
- ask-2 (cancel DD) is not done because identity is unverified. Passed to the DD team for after verification.
- We don't know whether the customer completed the 20 Aug mandate or received the 24 Aug notice.
- We don't know whether the customer wants the £1,000 standing order (next payment 1 Oct) kept or cancelled.
- We don't know the correct rent amount under the tenancy (£1,000 or £900).
