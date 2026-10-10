# Reasoning — Case 011

## Facts and claims

- Claim: Credit 21 Sep 09:40 to SYN-ACCT-11-1 is +£1,096.00 Faster Payment, payer name 'A KOWALCZYK', from Meridian SYN-SC-11-2 / SYN-ACCT-11-2, ref 'INV 2211 BOILER' (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Credit 22 Sep 14:20 to SYN-ACCT-11-1 is +£1,096.00 Faster Payment, payer name 'A KOWALCZYK', from Meridian SYN-SC-11-2 / SYN-ACCT-11-2, ref 'INV 2211 BOILER' (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Refund details SYN-SC-11-2 / SYN-ACCT-11-2 Confirmation of Payee result Match — name at bank 'M KOWALCZYK' (account type personal, checked 2026-09-23T10:05:33Z) (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Invoice INV 2211 payments were paid twice by mistake by a customer, £1,096 on Monday and again yesterday (Paul D., Business banking chat, `event-002`)
- Claim: Payer's refund instruction (relayed text) requests send it back to husband's account SYN-ACCT-11-2, SYN-SC-11-2, M Kowalczyk, 'that's what I paid from' (Paul D. (relaying text from client), Business banking chat, `event-002`)
- Claim: Payer name mismatch noted payer on credits shows 'A Kowalczyk'; refund name given is 'M Kowalczyk' (Servicing agent (Harrow & Vale Bank plc), Business banking chat, `event-003`)
- Claim: Kowalczyk relationship is Anna is the customer, Marek is her husband, it's their joint money (Paul D., Business banking chat, `event-004`)
- Claim: Account SYN-ACCT-11-2 ownership is account is Marek's but Anna uses it (per Anna, relayed by Paul) (Paul D., Business banking chat, `event-004`)
- Claim: Client text message (attachment) says Tue 22 Sep 19:02 from +44 7700 900 415 saved as 'Anna K - boiler job': paid twice, app glitched, send one back to husband's account SYN-ACCT-11-2, SYN-SC-11-2, M Kowalczyk, that's what I paid from (Paul D. (forwarded attachment), Business banking chat, `event-002`)
- Claim: CoP request account type (attachment) is personal (Harrow & Vale Bank plc (CoP result), Internal account view, `event-001`)

## Findings

None.

## Policy checks

- Identity: unverified (Business banking chat)
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 1 of 1 ask closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Why the payer name on the credits is 'A KOWALCZYK' when CoP returns 'M KOWALCZYK' for the same sort code/account; whether Anna is a joint holder or authorised user (CoP indicates personal account)
- Whether the text message genuinely came from the payer (Anna Kowalczyk) — sender number +44 7700 900 415 not verified; possible impersonation/redirection risk
- Whether the second payment is truly a duplicate (only one invoice INV 2211 outstanding, invoice amount £1,096)
- Which of the two credits (end-to-end IDs MER26092109401201 or MER26092214204811) is to be refunded
- Whether the payer's bank (Meridian) has raised a recall or the payer has disputed either payment
- Whether refunding to the originating account via a return of the original payment is preferable to a new payment
- Whether sufficient funds are available in SYN-ACCT-11-1 for the refund
- Whether Paul Devlin has authorised the refund payment through an appropriate channel/authentication
- Identity is unverified, so no refund or other change can be made. No payment or account status from tool results has been shared.
- ask-1 (the refund) is not done. It waits until Paul is verified through the secure portal or a verified call and confirms which credit to return.
- Name mismatch: the credits show 'A KOWALCZYK' and the refund details show 'M KOWALCZYK' (CoP match, personal account). The refund details are the same sort code and account the credits came from (event-001), which lowers the redirection risk. Whether Anna is a joint holder or authorised user is still unknown.
- The text message instruction came from an unverified number. It is recorded as a claim only and not acted on.
- Not checked yet: whether Meridian has raised a recall, whether funds are available, and whether a return of the original payment is better than a new payment. A transfer_journal lookup should follow once Paul is verified.
