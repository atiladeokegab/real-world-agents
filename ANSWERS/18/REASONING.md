# Reasoning — Case 018

## Facts and claims

- Claim: rent standing order current_amount_and_schedule £500.00 on the 1st to HARROW & VALE RE LIME PROPERTY CA, ref "862A BEV RD", since Feb 2026 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: customer account balance £96 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: customer account overdraft No overdraft (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: customer account income_pattern Salary credits stopped in July; since August irregular credits of £150–£300 labelled "AGENCY WORK" (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: rent standing order requested_new_amount £400 from next month (Customer, Phone (personal banking), `event-002`)
- Claim: customer employment_status Lost job in July; doing bits of agency work; cannot afford £500 at the minute (Customer, Phone (personal banking), `event-002`)
- Claim: rent standing order future_intention Will increase to £550 to catch up when back in proper work (Customer, Phone (personal banking), `event-002`)
- Claim: standing order change authority Agent states it can change the standing order as it is the customer's instruction, but wants to check a couple of things first (Servicing agent (Harrow & Vale Bank plc), Phone (personal banking), `event-003`)
- Claim: rent shortfall customer_acknowledgement Customer knows £400 is less than the rent and says they have told the agency they will sort it (Customer, Phone (personal banking), `event-004`)
- Claim: account activity Jul-Sep 2026 salary Final salary SALARY KP LOGISTICS LTD (FINAL) £1,640.00 on 2026-07-25 (account_activity_jul-sep.csv, Attachment, `event-001`)
- Claim: account activity Jul-Sep 2026 running_balance_gaps Running balances do not reconcile with listed rows (e.g. 2,428.40 + 210.00 shown as 1,913.15), implying unlisted debits (account_activity_jul-sep.csv, Attachment, `event-001`)

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

- Whether the landlord/letting agent (LIME PROPERTY) has agreed to accept £400; 'told the agency I'll sort it' does not establish agreement
- Whether 'the agency' in event-004 means the letting agent or the employment agency
- Current date and which payment date 'next month' refers to; whether the change can be made before the cut-off for the next 1st-of-month payment
- Whether the £96 balance plus expected agency income will cover even £400 on the next 1st; risk of failed payment
- Whether the customer wants a later increase to £550 scheduled now or will instruct it later
- Nature of unlisted debits causing running balances in the CSV not to reconcile
- Whether the customer has other priority debts/commitments and would accept financial difficulty support or referral (job loss, low balance indicate possible financial vulnerability)
- What checks the agent intended to make in event-003 and their outcome
- ask-1 (amend to £400) is not done. It needs identity confirmed in the system and a support conversation first
- ask-2 (make the change today) is not done. Whether it can happen before the next 1st-of-month cut-off depends on the support team's outcome
- We don't know if the letting agent has agreed to £400, or which 'agency' the customer meant
- The standing order record has not been looked up yet, so the current schedule comes only from the account view in event-001
- The attachment's running balances don't add up from the rows shown, which suggests debits that aren't listed
