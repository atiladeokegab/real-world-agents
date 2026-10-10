# Answer — Case 007

## Decision

ESCALATED — Handed to the operations team: exception 'quiet_wrong_value' handling (don't use it; re-query once, else escalate): request_info -> escalate.

## What we received

`index.md`, `history.md`, `attachments/agency_deposit_statement.pdf`, `attachments/cop_results.json`, `attachments/deposit_split.csv` · 3 attachments · 4 events · identity: unverified Bank customer (In-app chat (personal banking))

## Actions

None.

## Customer reply

Channel: In-app chat (personal banking)

Thank you for your message. We've passed your request to the operations team, who will review it and reply to you here. We haven't made any changes to your account while this is reviewed.

## Not done

- no change made to the account — because the case was handed to a person

## Evidence used

- `event-001`
- `event-002`
- `event-004`

## Handover

**Take it:** the operations team

**Urgency:** Routine

**Type:** Technical

**Verified:**
- identity unverified via channel, role Bank customer

**Only claimed:**
- Miya Yagisawa received deposit return as lead tenant Deposit came back to my account today because I was the lead tenant (Customer, event-002)
- Customer account credit received 22 Sep 10:05 +£1,260.00 from OAKFIELD PM CLIENT A/C, ref DEP RETURN 7 ISFIELD RD (Harrow & Vale Bank plc (case record), event-001)
- Deposit amount held £1,800, £450 per tenant (Customer, event-002)
- Deposit deductions retained by landlord £540 for damage, cleaning and plumbing (plumbing Salvatore's fault) (Customer, event-002)
- Jack Elson share amount requested £375.00 (Customer, event-002)
- Jack Elson share amount in deposit_split.csv amount column 375.00 (Customer, event-002)
- Jack Elson share per-tenant share after deductions per agency statement £337.50 (Oakfield Property Management Ltd (Somma Patel), event-001)
- Jack Elson share calculation note in deposit_split.csv 450 - 75 - 37.50 (equals £337.50) (Customer, event-002)

**Conflicts:**
- finding-1 conflict/amounts: stated total £540.00 (attachment:agency_deposit_statement.pdf) does not match the £1,297.50 implied by deposit_split.csv ()
- event-002 conflicts with event-001: £375.00 vs £337.50
- event-002 conflicts with event-002: £375.00 vs 450 - 75 - 37.50 (equals £337.50)
- event-002 conflicts with event-001: 375.00 vs £337.50
- event-002 conflicts with event-002: 375.00 vs 450 - 75 - 37.50 (equals £337.50)
- event-002 conflicts with event-001: £1,297.50 (247.50 + 375.00 + 337.50 + 337.50); per finding-1 does not reconcile with £540 deductions stated in agency statement vs £1,260.00 returned to lead tenant account 22/09/2026

**We did:**
None.

**We did not:**
- no change made to the account

**Question for you:** Please establish: Correct amount for Jack Elson: customer and CSV amount say £375.00, but agency statement and the CSV's own calculation give £337.50 (£37.50 difference)

**Safe to send now:** Thank you for your message. We've passed your request to the operations team, who will review it and reply to you here. We haven't made any changes to your account while this is reviewed.

## What failed

Nothing.
