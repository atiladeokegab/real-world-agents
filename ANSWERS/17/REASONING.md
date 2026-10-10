# Reasoning — Case 017

## Facts and claims

- Claim: Bright Sparks Electrical Ltd 29 Sep reconciliation credits_per_customer_download £30,078.94 (Violetta (bookkeeper), Business banking chat, `event-002`)
- Claim: Bright Sparks Electrical Ltd 29 Sep reconciliation suspected_missing_credit £1,750 credit believed missing from bank statement; closing only works if credits were £31,828.94; 'something's been lost' (Violetta (bookkeeper), Business banking chat, `event-002`)
- Claim: CSV export 29 Sep requested_at 13:15:02 by user violetta.k (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Credits after 13:15 on 29 Sep posted +£1,750.00 at 14:02 (K WHITTLE, ref INV 4471); +£120.00 at 16:41 (A ROSS, ref INV 4480 PART) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Customer-quoted closing balance £55,527.48 matches running balance between 14:02 and 16:41 (read from screen mid-afternoon), not the balance at 13:15 export (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: 28 Sep activity same_pattern +£1,900.00 landed at 18:10 on 28 Sep, after customer's 13:20 export (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Customer's 29 Sep figures stated_as opening £32,113.84 (their 28 Sep close), supplier payments £8,415.30, credits £30,078.94, closing £55,527.48 (on-screen balance) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Investigation agent_action Agent will compare export with account's full-day activity (Servicing agent (Harrow & Vale Bank plc), Business banking chat, `event-003`)
- Claim: Complaint requested_if_unresolved Director wants a formal missing-funds complaint logged if not found today (Violetta, Business banking chat, `event-004`)

## Findings

None.

## Policy checks

- Identity: unverified (Business banking chat)
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

None.

## Alternatives rejected

None.

## Uncertainties

- Whether the customer accepts that the £1,750 (K WHITTLE, INV 4471) was posted at 14:02 after their 13:15 export, i.e. a timing difference and not a lost payment
- Whether a formal complaint should still be logged once the timing explanation is given; no confirmation from the director
- Whether the customer's 28 Sep close (£32,113.84) already includes the £1,900 P LEWIS credit posted at 18:10 on 28 Sep after their 13:20 export (the full-day file shows £32,113.84 as the balance after that credit)
- Official end-of-day closing balance for 29 Sep (full-day file ends at £55,647.48 after the 16:41 £120 credit; no statement closing figure given)
- Whether the £120 A ROSS credit (16:41) will be picked up in the customer's next reconciliation
- Whether the customer has an end-of-day/full-day export option that avoids intraday cut-off
- Identity is unverified, so the bank's account view (event-001) can't be shared yet. That includes the 14:02 £1,750 K WHITTLE credit, the 16:41 £120 credit and the 28 Sep £1,900 credit, which all suggest a timing difference rather than a lost payment.
- ask-1: we're working on it but haven't answered it. The explanation can be given once the customer verifies through the secure portal or a verified call.
- ask-2: complaint not logged yet. It depends on the customer verifying and on whether the director still wants it once the timing explanation is given. The complaint is conditional and hasn't been confirmed.
- No official end-of-day closing balance for 29 Sep is on record. The full-day file ends at £55,647.48.
- sentiment: customer has made a complaint: request_info -> escalate
