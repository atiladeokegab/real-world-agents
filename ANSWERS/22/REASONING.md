# Reasoning — Case 022

## Facts and claims

- Claim: Account SYN-ACCT-B022 opening_ledger GBP 1500.00, reference OPEN, booked (Brackenfold Bank, Card ledger record, `event-001`)
- Claim: Account SYN-ACCT-B022 card_debit GBP -520.00, reference FINAL-022, linked authorisation AUTH-022, booked at 08:30 (Brackenfold Bank, Card ledger record, `event-002`)
- Claim: Account SYN-ACCT-B022 authorisation_reservation GBP 600.00, reference AUTH-022, linked authorisation AUTH-022, status active as of 09:00 (Brackenfold Bank, Card ledger record, `event-003`)
- Claim: Account SYN-ACCT-B022 ledger_balance GBP 980.00 snapshot at 09:00 (Brackenfold Bank, Card ledger record, `event-004`)
- Claim: Account SYN-ACCT-B022 available_balance GBP 380.00 snapshot at 09:00 (Brackenfold Bank, Card ledger record, `event-005`)
- Claim: Rois Fenwick account_holder_and_authentication Account holder is Rois Fenwick; current contact authentication recorded as passed (Brackenfold Bank card ledger, Internal card view, `event-006`)
- Claim: Alderclock Hotel charges amount_taken Hotel took £600 and £520, total £1,120 (Rois Fenwick, Authenticated customer chat, `event-007`)
- Claim: Alderclock Hotel stay SYN-HOTEL-022 final_amount_paid_by_card GBP 520.00, payment reference FINAL-022, authorisation reference AUTH-022, stay 2026-11-07 to 2026-11-10 (Alderclock Hotel, Hotel receipt, `event-008`)
- Claim: Alderclock Hotel stay final_card_amount £520; stay ended this morning (Alderclock Hotel, Merchant email, bank support copied, `event-009`)
- Claim: Alderclock Hotel stay expected_cost Customer thought the stay cost £520 (Rois Fenwick, Authenticated customer chat, `event-007`)
- Claim: Card servicing procedure hold_release_authority Card operations can investigate a lingering linked authorisation and release an eligible stale hold after checking linkage and current network state; case desk may request investigation but cannot release a hold; timing depends on checks (Brackenfold Bank card operations, Internal procedure view, `event-010`)

## Findings

None.

## Policy checks

- Identity: unverified (Customer chat)
- Authority: role Rois Fenwick
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether the active £600 authorisation AUTH-022 is a stale hold eligible for release after the £520 FINAL-022 debit settled
- Current card network state of AUTH-022 and whether the merchant has already released or will release it
- Whether card operations has been asked to investigate, and outcome
- Whether release can happen today; timing depends on card operations checks
- Whether event-011 (unlabelled 'Customer chat', not marked authenticated) came from the authenticated session
- Why the reservation is recorded at 09:00, after the 08:30 final debit
- ask-1: release is for card operations only; whether the hold can be released, and whether that can happen today, depends on their linkage and network checks
- ask-2: the ledger points to the £600 being an active reservation rather than a second debit, but this isn't explained to the customer yet because the system authority shows identity unverified and event-011 isn't marked authenticated
- The reason the AUTH-022 reservation is recorded at 09:00, after the 08:30 final debit, is unknown
- Whether the merchant has already released AUTH-022 on the network is unknown
