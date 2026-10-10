# Answer — Case 004

## Decision

ESCALATED — Handed to Direct Debit disputes / Payments servicing team: The customer is getting more frustrated (event-002, event-004). She is asking for a same-day Direct Debit Guarantee refund of £900 and cancellation of the Harbour Lets DD. Identity is unverified, so no change can be made and no account or payment status can be shared. Her claim that the £900 is an error conflicts with the case record, where the collection matches the 24 Aug advance notice (event-001). The real problem looks like rent paid twice: the £1,000 standing order is still active and a new £900 DD was set up to replace it (finding-1).

## What we received

`index.md`, `history.md`, `attachments/dd_advance_notice_2026-08-24.eml`, `attachments/standing_order_on_file.json`, `attachments/statement_extract_sep.csv` · 3 attachments · 4 events · identity: unverified Bank customer (In-app chat (personal banking))

## Actions

None.

## Customer reply

Channel: In-app chat (personal banking)

I understand this is frustrating, and I'm sorry. I've passed your request to refund the £900 Direct Debit and cancel it to our Direct Debit team. Before we can make any change or discuss your payments, we need to confirm your identity. Please contact us through the secure portal or on a verified call. A colleague will reply here.

## Not done

- Did not raise a DD indemnity claim (mandate_journal.dispute): identity is unverified and the amount matches the advance notice — because the case was handed to a person
- Did not cancel the DD mandate (mandate_journal.cancel): identity is unverified — because the case was handed to a person
- Did not cancel or amend the £1,000 standing order: not requested, and identity is unverified — because the case was handed to a person
- Did not share any account or payment details with the unverified customer — because the case was handed to a person
- Did not promise a refund or any timescale — because the case was handed to a person
- no change made to the account — because the case was handed to a person

## Evidence used

- `event-001`
- `event-002`
- `event-003`
- `event-004`

## Handover

**Take it:** Direct Debit disputes / Payments servicing team

**Urgency:** Today

**Type:** Emotional

**Verified:**
- Case record (event-001) shows a £1,000 standing order on 1 Sep to HARROW & VALE RE HARBOUR LETS LTD CA, ref RENT 27 ELM RD. It is still active for 1 Oct.
- Case record (event-001) shows a £900 DD collection on 3 Sep from H&V COLLECT / HARBOUR LETS. The mandate was created 20 Aug 2026 via an originator invite.
- Originator advance notice dated 24 Aug says £900 on or around 3 Sep, then monthly. The collection matches the notice (event-001).
- Customer identity is NOT verified on this channel.
- identity unverified via channel, role Bank customer

**Only claimed:**
- Customer says she never agreed to £900 and her rent is £1,000 (event-002).
- Customer says the collection is an error and the Guarantee requires an immediate refund (event-004).
- Customer wants the £900 refunded today and the DD cancelled (event-002).
- September rent taken twice £1,000 on the 1st and £900 on the 3rd (Customer, event-002)
- £900 Direct Debit authorised by customer Customer says she never agreed to £900 (Customer, event-002)
- Rent amount is £1,000; the landlord has the amount wrong (Customer, event-002)
- £900 Direct Debit collection is an error Customer says it is an error and that the guarantee requires an immediate refund (Customer, event-004)
- Direct Debit mandate H&V COLLECT / HARBOUR LETS created 20 Aug 2026 via originator invite (Harrow & Vale Bank plc (case record), event-001)
- Direct Debit advance notice sent 24 Aug: £900.00 to be collected on or around 3 September, then monthly (Harrow & Vale Bank plc (case record), event-001)
- 3 Sep Direct Debit collection amount matches advance notice £900.00 matches the notice (Harrow & Vale Bank plc (case record), event-001)
- Standing order to HARROW & VALE RE HARBOUR LETS LTD CA, ref RENT 27 ELM RD status £1,000 monthly on the 1st, set up Feb 2025, still active for 1 Oct (Harrow & Vale Bank plc (case record), event-001)

**Conflicts:**
- event-002/event-004 vs event-001: customer says the £900 was not agreed and is an error. The record shows a mandate created 20 Aug and an advance notice of £900 that matches the collection.
- finding-1: possible duplicate rent. The SO (£1,000, 1st) and the DD (£900, 3rd) both pay Harbour Lets. The notice told her to cancel the SO before the first collection.
- finding-1 anomaly/duplicates: the case text describes a possible duplicate payment/instruction (event-002)
- event-002 conflicts with event-001: Customer says she never agreed to £900 vs 20 Aug 2026 via originator invite
- event-002 conflicts with event-001: Customer says she never agreed to £900 vs 24 Aug: £900.00 to be collected on or around 3 September, then monthly
- event-002 conflicts with event-001: £1,000; the landlord has the amount wrong vs 24 Aug: £900.00 to be collected on or around 3 September, then monthly
- event-004 conflicts with event-001: Customer says it is an error and that the guarantee requires an immediate refund vs £900.00 matches the notice

**We did:**
- Reviewed the case record, the attachments and the duplicate-payment finding.
- Sent a holding reply only, with no account or payment status disclosed.

**We did not:**
- Did not raise a DD indemnity claim (mandate_journal.dispute): identity is unverified and the amount matches the advance notice.
- Did not cancel the DD mandate (mandate_journal.cancel): identity is unverified.
- Did not cancel or amend the £1,000 standing order: not requested, and identity is unverified.
- Did not share any account or payment details with the unverified customer.
- Did not promise a refund or any timescale.
- no change made to the account

**Question for you:** Once the customer's identity is verified, does a Direct Debit Guarantee indemnity claim apply to the £900 collected on 3 Sep, given that it matches the 24 Aug advance notice? Or should the double rent payment be handled by cancelling the DD or the SO (as the customer prefers) and asking Harbour Lets to return the overpayment?

**Safe to send now:** I understand this is frustrating, and I'm sorry. I've passed your request to refund the £900 Direct Debit and cancel it to our Direct Debit team. Before we can make any change or discuss your payments, we need to confirm your identity. Please contact us through the secure portal or on a verified call. A colleague will reply here.

## What failed

Nothing.
