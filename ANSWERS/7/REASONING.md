# Reasoning — Case 007

## Facts and claims

- Claim: Miya Yagisawa received deposit return as lead tenant Deposit came back to my account today because I was the lead tenant (Customer, In-app chat (personal banking), `event-002`)
- Claim: Customer account credit received 22 Sep 10:05 +£1,260.00 from OAKFIELD PM CLIENT A/C, ref DEP RETURN 7 ISFIELD RD (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Deposit amount held £1,800, £450 per tenant (Customer, In-app chat (personal banking), `event-002`)
- Claim: Deposit deductions retained by landlord £540 for damage, cleaning and plumbing (plumbing Salvatore's fault) (Customer, In-app chat (personal banking), `event-002`)
- Claim: Jack Elson share amount requested £375.00 (Customer, In-app chat (personal banking), `event-002`)
- Claim: Jack Elson share amount in deposit_split.csv amount column 375.00 (Customer, Attachment: deposit_split.csv, `event-002`)
- Claim: Jack Elson share per-tenant share after deductions per agency statement £337.50 (Oakfield Property Management Ltd (Somma Patel), Attachment: agency_deposit_statement.pdf, `event-001`)
- Claim: Jack Elson share calculation note in deposit_split.csv 450 - 75 - 37.50 (equals £337.50) (Customer, Attachment: deposit_split.csv, `event-002`)
- Claim: Salvatore Russell share amount requested £247.50 (450 - 75 - 37.50 - 90 plumbing); agency statement also shows £247.50 (Customer, In-app chat (personal banking), `event-002`)
- Claim: Emerald Creagh share amount requested £337.50; agency statement also shows £337.50 (Customer, In-app chat (personal banking), `event-002`)
- Claim: Miya Yagisawa share amount to keep £337.50 (Customer, In-app chat (personal banking), `event-002`)
- Claim: Requested split total implied by deposit_split.csv £1,297.50 (247.50 + 375.00 + 337.50 + 337.50); per finding-1 does not reconcile with £540 deductions stated in agency statement (Customer, Attachment: deposit_split.csv, `event-002`)
- Claim: Deposit return amount returned after £540 deductions per agency statement £1,260.00 returned to lead tenant account 22/09/2026 (Oakfield Property Management Ltd (Somma Patel), Attachment: agency_deposit_statement.pdf, `event-001`)
- Claim: Salvatore Russell payee Confirmation of Payee result Match (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Jack Elson payee Confirmation of Payee result Match (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Emerald Creagh payee Confirmation of Payee result No match (ANNM) - account name held is E CREAGH-DOYLE (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Deductions agreed by tenants Everyone agreed the deductions in writing; it's all worked out, just needs sending (Customer, In-app chat (personal banking), `event-004`)
- Claim: Deductions agreed per agency statement Agreed in writing by all four tenants on 18 September 2026: garden £300 shared, plumbing £90 S. Russell only, cleaning £150 shared (Oakfield Property Management Ltd (Somma Patel), Attachment: agency_deposit_statement.pdf, `event-001`)
- Claim: Customer account balance before today £412.30 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)

## Findings

- **finding-1 · amounts** (conflict) — stated total £540.00 (attachment:agency_deposit_statement.pdf) does not match the £1,297.50 implied by deposit_split.csv (). Addressed.

## Policy checks

- Identity: unverified (In-app chat (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

quiet_wrong_value → don't use it; re-query once, else escalate

## Alternatives rejected

None.

## Uncertainties

- Correct amount for Jack Elson: customer and CSV amount say £375.00, but agency statement and the CSV's own calculation give £337.50 (£37.50 difference)
- Whether the customer confirms the corrected amount for Jack before any payment is made
- Requested split totals £1,297.50 against £1,260.00 received (finding-1); not reconciled
- Whether the Emerald Creagh account (name held E CREAGH-DOYLE, CoP no match) belongs to the intended payee; customer has not been told about the CoP result or responded to it
- Which event the agency_deposit_statement.pdf and cop_results.json were supplied in, and whether the statement is authentic
- Whether the customer has reviewed payment warnings and authorises each payment
- Whether any payments have already been made
- Identity is unverified, so no payment can be set up and no account or payment status (including the CoP result) can be shared until the customer verifies through the secure portal or a verified call.
- ask-1: Jack's requested £375.00 conflicts with the agency statement and the CSV's own working (£337.50). The requested split totals £1,297.50, against £1,260.00 per the agency statement. finding-1's comparison of £540 deductions with the £1,297.50 split is really this £37.50 overstatement. The customer must confirm the corrected amount.
- ask-1: Emerald Creagh's CoP came back no match (name held E CREAGH-DOYLE). This can only be raised in detail once the customer is verified, and she must confirm the account before any payment.
- ask-2: The customer wants the payments sent today. This can't be committed to until she is verified, Jack's amount is confirmed and the Emerald payee is resolved.
- No tool in the catalogue sends a new payment. The customer will probably have to authorise these payments herself. Event-003 overpromised help with paying.
- The agency statement hasn't been checked for authenticity, and we don't know which event it was supplied in.
- exception 'quiet_wrong_value' handling (don't use it; re-query once, else escalate): request_info -> escalate
