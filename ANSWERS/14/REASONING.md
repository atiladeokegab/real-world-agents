# Reasoning — Case 014

## Facts and claims

- Claim: card payment 11 Sep 18:02 PAYGATE*NORTHGATE LET amount -£634.00 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: card payment 11 Sep 18:04 PAYGATE*NORTHGATE LET amount -£634.00 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: two PAYGATE*NORTHGATE LET payments possible duplicate (finding-1, duplicates check) case text describes a possible duplicate payment (evidence check (code), Internal account view, `event-001`)
- Claim: cause of duplicate customer explanation Customer clicked the agency's payment link twice after a 'page not responding' message (Customer (recorded in case record), Internal account view, `event-001`)
- Claim: agency refund promised Agency email dated 14 Sep: will refund £634 within 5-10 working days (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: holding deposit charged twice £634 each (Customer, In-app chat (personal banking), `event-002`)
- Claim: agency refund promised timing 5-10 working days, promised two days ago (Customer, In-app chat (personal banking), `event-002`)
- Claim: chargeback entitlement Customer believes he is entitled to a chargeback on the second payment (Customer, In-app chat (personal banking), `event-002`)
- Claim: funds needed for the actual flat deposit (Customer, In-app chat (personal banking), `event-002`)
- Claim: both payments visible to agent Agent can see both payments (Servicing agent, In-app chat (personal banking), `event-003`)
- Claim: card payments settlement status Both settled 2026-09-13, auth codes A71C02 and A71C09, MCC 6513 (card_transactions.csv attachment, In-app chat (personal banking), `event-001`)

## Findings

- **finding-1 · duplicates** (anomaly) — the case text describes a possible duplicate payment/instruction (event-001). Addressed.

## Policy checks

- Identity: unverified (In-app chat (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 1 of 1 ask closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether the agency's refund of £634 has been issued or received yet
- Which of the two payments (18:02 auth A71C02 or 18:04 auth A71C09) the agency will refund and which a chargeback would target
- Whether a chargeback is eligible/appropriate while the merchant has acknowledged the duplicate and promised a refund within 5-10 working days
- Whether the customer has funds for the actual deposit or needs other help in the meantime
- Whether the agency email attachment is genuine (it was provided via the case, not verified with the merchant)
- Exact date the agency's refund window ends
- ask-1 (chargeback on the second £634 payment) has not been started. Identity is unverified, and card_service.dispute is a risk-3 change that needs a verified Bank customer. After verification, the next steps are a card_service read and then a dispute request if it's eligible.
- finding-1 (possible duplicate): the internal view (event-001) and card_transactions.csv show two £634.00 PAYGATE*NORTHGATE LET payments 2 minutes apart (auth A71C02 and A71C09). The agency email says they will refund one of them. This hasn't been checked through any tool yet, and the email hasn't been confirmed with the merchant.
- It's not known whether the agency refund has been issued yet. A dispute could overlap with the refund the merchant promised, so card_service should be checked before any dispute is raised.
- The customer is frustrated but the trend is steady (event-002, event-004). He hasn't made a complaint or shown signs of vulnerability, so no handover is needed right now.
