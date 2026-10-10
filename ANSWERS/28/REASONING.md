# Reasoning — Case 028

## Facts and claims

- Claim: INT-028 instruction displayed_estimate EUR1,160 at indicative 1.1600 EUR/GBP; non-binding until execution (Brackenfold Bank international payments, Authenticated portal instruction, `event-001`)
- Claim: INT-028 instruction charge_option_and_disclosure Shared; possible intermediary/receiving-bank charges disclosed; customer confirmed the instruction (Brackenfold Bank international payments, Authenticated portal instruction, `event-001`)
- Claim: INT-028 instruction principal_and_fee Principal £1,000; separate sending-bank fee £5 (Brackenfold Bank international payments, Authenticated portal instruction, `event-001`)
- Claim: INT-028 execution executed_rate 1.1500 EUR per GBP, executed 2026-11-18 09:08+00:00 (Brackenfold Bank, Document (execution-advice.pdf), `event-002`)
- Claim: INT-028 execution gross_transferred EUR 1150.00 (GBP 1000.00 converted) (Brackenfold Bank, Document (execution-advice.pdf), `event-002`)
- Claim: INT-028 execution total_account_debit GBP 1005.00 (incl. GBP 5.00 sending-bank fee); charge option SHA (Brackenfold Bank, Document (execution-advice.pdf), `event-002`)
- Claim: INT-028 receipt gross_received EUR 1150.00 received 2026-11-18 09:50+00:00 (Synthetic Overseas Recipient Bank, Document (recipient-advice.pdf), forwarded by recipient, `event-004`)
- Claim: INT-028 receipt intermediary_deduction EUR 15.00 (Synthetic Overseas Recipient Bank, Document (recipient-advice.pdf), forwarded by recipient, `event-004`)
- Claim: INT-028 receipt net_credited EUR 1135.00 (Synthetic Overseas Recipient Bank, Document (recipient-advice.pdf), forwarded by recipient, `event-004`)
- Claim: recipient advice provenance Advice supplied by recipient's bank for payment received this morning (Osa Melwick, Recipient email forwarded with provenance, `event-005`)
- Claim: INT-028 receipt amount_received_vs_seen Recipient got EUR1,135, not the EUR1,160 the customer saw (Perrin Wessel, Authenticated customer chat, `event-006`)
- Claim: INT-028 missing_amount Customer thinks EUR25 went missing (Perrin Wessel, Authenticated customer chat, `event-006`)
- Claim: INT-028 entitled_amount Recipient should have received the original estimate (EUR1,160) (Perrin Wessel, Customer chat, `event-007`)

## Findings

None.

## Policy checks

- Identity: unverified (Customer chat)
- Authority: role Perrin Wessel
- Risk level: no tool used
- Completion: 3 of 3 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether any bank error occurred, or the EUR25 difference is fully explained by the rate difference (EUR10) and the intermediary deduction (EUR15) under SHA
- Which intermediary bank took the EUR15 deduction and whether it is consistent with the Shared charge option
- Whether the recipient-advice.pdf has been verified with the recipient bank (it was forwarded by the recipient via the customer)
- Whether event-007 came over an authenticated channel (labelled only 'Customer chat')
- Whether any compensation or goodwill policy applies to non-binding estimate differences or intermediary charges
- No evidence findings were computed by code for this case
- The system shows identity as unverified, and event-007 came over a 'Customer chat' not labelled as authenticated. So nothing is disclosed and no change is made until the customer comes back through the secure portal or a verified call.
- ask-1: the EUR25 gap seems fully explained by the documents (EUR10 from the rate: indicative 1.1600 vs executed 1.1500; plus the EUR15 intermediary deduction under SHA). It isn't explained here because identity isn't verified, so it's left for the next step after verification.
- ask-2: there's no compensation tool, and no policy in the records supports paying for a non-binding estimate difference or a disclosed SHA intermediary charge. Nothing should be promised. If the customer pursues it after verification, it could be logged as a complaint or review through case_journal.
- ask-3: the EUR1,160 estimate was marked indicative and non-binding until execution (event-001), so we shouldn't confirm the recipient was owed it. Left for the next step after verification.
- The recipient advice (event-004) reached us via the recipient and the customer, and hasn't been checked with the recipient bank. We don't know which intermediary took the EUR15.
- No transfer_journal lookup has been done yet. One could be done after verification to check INT-028's status.
