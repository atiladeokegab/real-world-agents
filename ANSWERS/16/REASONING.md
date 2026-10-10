# Reasoning — Case 016

## Facts and claims

- Claim: Christine H. holds accounts Sole account 'Rental income' SYN-ACCT-16-1 and joint account SYN-ACCT-16-2 with spouse David H. (sort code SYN-SC-16-1) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Third-party authority TPA-2024-00931 scope Dawes & Co may request statements and balance information for SYN-ACCT-16-1 only. No payments, no detail changes, no information on any other account, including any joint account. Signed by Christine 12/03/2024, processed at York branch 14/03/2024, in force until cancelled in writing (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Joint account SYN-ACCT-16-2 third-party authority on file None. David H. has never signed one, and a joint account needs every account holder to sign (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Per-property rental statements held by bank No. Oakfield Property Management manages the properties, and the agency's system produces per-property statements (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Christine H. instructed Dawes & Co Christine has asked Dawes & Co to do her full tax return this year, so they need both accounts, including the joint one with David (Michael Dawes (accountant), Email (personal banking, third-party requests), `event-002`)
- Claim: Request requests Statements for the rental account and the joint account for the tax year to 5 Apr 2026, plus property-by-property rental statements for six lets (Michael Dawes (accountant), Email (personal banking, third-party requests), `event-002`)
- Claim: Sender email matches authority contact m.dawes@dawesandco.example matches the contact email on authority TPA-2024-00931 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)

## Findings

None.

## Policy checks

- Identity: unverified (Email (personal banking, third-party requests))
- Authority: role Third party
- Risk level: no tool used
- Completion: 3 of 3 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether Christine really instructed Dawes & Co to get joint account information. Only the accountant says so; nothing from Christine is on file
- Whether David H. (joint holder) consents to his account information going to Dawes & Co. No joint authority exists
- Whether authority TPA-2024-00931 is still in force and has not been cancelled in writing
- Whether the email really comes from Michael Dawes. The address matches the authority, but the sender has not been verified
- The exact statement period (presumably 6 Apr 2025 to 5 Apr 2026) and how statements should be delivered to the third party
- Whether Christine should be contacted, either to give joint authority with David or to redirect the per-property request to Oakfield Property Management
- Whether past releases ('as usual') covered only SYN-ACCT-16-1
- ask-1: TPA-2024-00931 covers statements for SYN-ACCT-16-1 only, but the sender hasn't been verified. The email address matches the authority, but that doesn't prove who sent it. Nothing is released until they come through a verified call or the secure portal. No tool here confirms the authority hasn't been cancelled in writing, so that needs checking once they're verified. The period (probably 6 Apr 2025 to 5 Apr 2026) and delivery method still need confirming.
- ask-2: There's no authority on file for joint account SYN-ACCT-16-2. David H. has never signed one, and the TPA expressly excludes joint accounts. Only the accountant says Christine gave this instruction (event-002), so it isn't treated as authority. Release needs a joint authority signed by both holders.
- ask-3: The bank holds no per-property statements. Oakfield Property Management produces them (event-001). I didn't name the agency, to avoid giving out customer details to an unverified sender.
- The message doesn't say which accounts exist or confirm anything about their status, because identity is unverified.
- 'As usual' suggests earlier releases, but I can't tell whether they covered only SYN-ACCT-16-1.
