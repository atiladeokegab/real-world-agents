# Reasoning — Case 013

## Facts and claims

- Claim: Direct Debit H&V COLLECT / NORTHGATE LETTINGS £750, 18 Sep status presented and returned unpaid, 'refer to payer' (available balance £710.40) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Direct Debit H&V COLLECT / NORTHGATE LETTINGS £750, 21 Sep status re-presented by originator and paid (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Salary credited 20 Sep (statement: £2,145.00 from Brighton & Co LLP) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Automated unpaid DD letter sent 19 Sep: 'A Direct Debit for £750.00 could not be paid' (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Unpaid-item fee charged by H&V none (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Next collection scheduled no further collection before 18 Oct (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Bank letter says rent direct debit failed on the 18th (Customer, In-app chat (personal banking), `event-002`)
- Claim: £750 payment to agency debited went out on the 21st (Customer, In-app chat (personal banking), `event-002`)
- Claim: Rent payment (per agency text, as relayed by customer) status 'failed'; customer should pay manually today to avoid arrears (Customer (relaying Northgate Lettings text), In-app chat (personal banking), `event-002`)
- Claim: Rent payment possible duplicate case text describes a possible duplicate payment/instruction (finding-1) (Evidence check (code), Findings, `event-002`)

## Findings

- **finding-1 · duplicates** (anomaly) — the case text describes a possible duplicate payment/instruction (event-002). Addressed.

## Policy checks

- Identity: unverified (In-app chat (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether Northgate Lettings has received/reconciled the 21 Sep re-presented £750 collection
- When the agency text was sent relative to the 21 Sep re-presentation (may predate it)
- Content and authenticity of agency_text_screenshot.png (image content not available); whether the request to pay manually is genuine or possible social engineering
- Whether the customer has already made a manual payment to the agency (risk of duplicate payment, finding-1)
- Customer's arrears status on the agency's ledger
- Whether the agency's payment details for any manual payment match the known mandate reference NL-9LIME-0442
- Identity is unverified, so the status of the 18 Sep and 21 Sep Direct Debit collections (event-001) is not shared. ask-1 is pending until identity is verified through the secure portal or a verified call.
- ask-2: we can't confirm whether a manual payment is needed until the customer is verified. The customer is told not to pay manually based only on the text and to check with Northgate Lettings through contact details they already hold. This addresses the possible duplicate payment (finding-1).
- We can't see the content of the agency text screenshot, so we don't know if the request to pay manually is genuine. It could be social engineering.
- We don't know whether Northgate Lettings has matched the 21 Sep collection to her account, or whether the customer has already made a manual payment.
- Event-003 said we'd check the mandate dates. That lookup is deferred because its result couldn't be shared until the customer is verified.
