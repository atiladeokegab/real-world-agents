# Answer — Case 029

## Decision

ESCALATED — Handed to Recovery team (hold review and recovery decision for IN-029 / HOLD-029), with a hardship review requested for the customer: The customer says they need money for food and is getting more frustrated (event-004, then event-005). They are asking for £3,200 to be restored, for the hold to be released and for the sender to be confirmed as repaid. Under event-002, recovery decisions and hold reviews belong to the recovery team. The case desk can only request status and a hardship review. Identity on this contact is also unverified: event-005 came in on the unauthenticated 'Customer chat', not the authenticated chat used for event-004.

## What we received

`index.md`, `history.md`, `attachments/ledger-and-reservations.csv`, `attachments/recovery-status.json` · 2 attachments · 5 events · identity: unverified Enna Prysett (Customer chat)

## Actions

None.

## Answer to the question

Question: No desk response to the final request is recorded. Using the complete history and supplied evidence, recommend the next action, recipient and communication, explaining uncertainty and confidence.

Hand the case to the recovery team at high urgency and ask for a hold review of HOLD-029 and a hardship review. Send only the holding reply, which gives no account details, through the customer's authenticated chat. The records show £1,200 reserved and £0.00 returned to the sender, not £3,200 taken. Confidence in those figures is high, but identity on event-005 is unverified, and the hold decision and any hardship support belong to the recovery team, so we can't promise either.

## Customer reply

Channel: Customer chat

Thank you for telling us you need money for food. We've passed your request to the team who handle this, and we've asked for help with essential spending to be looked at. A colleague will contact you through your secure chat or a verified call to go through your account with you. Please don't share passwords or security codes in this chat.

## Not done

- Did not restore any funds or release or reduce HOLD-029 (this is the recovery team's decision, event-002) — because the case was handed to a person
- Did not tell the customer the sender has been paid back (records show £0.00 booked return and decision pending) — because the case was handed to a person
- Did not share balance or recovery figures on the unverified channel — because the case was handed to a person
- Did not promise any hardship payment or amount — because the case was handed to a person
- no change made to the account — because the case was handed to a person

## Evidence used

- `event-001`
- `event-002`
- `event-003`
- `event-004`
- `event-005`

## Handover

**Take it:** Recovery team (hold review and recovery decision for IN-029 / HOLD-029), with a hardship review requested for the customer

**Urgency:** Today

**Type:** Emotional

**Verified:**
- Ledger SYN-ACCT-B029 (event-001, event-003): opening £500 + incoming IN-029 £2,000 - outgoing OUT-029 £600 = booked ledger £1,900
- Recovery reservation HOLD-029 for £1,200 is active (event-003)
- Available balance £700 = £1,900 ledger less the £1,200 reservation (event-003)
- Recovery status for IN-029: request_received, decision pending, requested £2,000, booked return £0.00 (event-003, retrieved 2026-11-19T09:15)
- Authentication passed on the authenticated chat used for event-004 (event-001)
- identity unverified via channel, role Enna Prysett

**Only claimed:**
- Customer says the bank took £3,200 (event-005). This looks like the £2,000 requested plus the £1,200 reserved added together, but that is not confirmed
- Customer asks us to confirm the sender has already been paid back (event-005)
- Customer says they need money for food while this is sorted (event-005)
- SYN-ACCT-B029 opening ledger amount £500 (OPEN, booked) (Brackenfold Bank account service, event-001)
- incoming payment IN-029 booked credit £2,000, disputed (Brackenfold Bank account service, event-001)
- outgoing payment OUT-029 booked debit £600 ordinary customer outgoing payment (Brackenfold Bank account service, event-001)
- SYN-ACCT-B029 ledger balance current booked ledger £1,900 (Brackenfold Bank account service, event-001)
- customer contact authentication passed (Brackenfold Bank account service, event-001)
- recovery request IN-029 status recovery requested for £2,000; request received; investigation pending (Synthetic Sender Bank, event-002)
- recovery IN-029 status / decision request_received; decision pending (retrieved 2026-11-19T09:15) (Brackenfold Bank recovery team, event-003)
- recovery reservation HOLD-029 reserved amount £1,200 active (Brackenfold Bank recovery team, event-003)

**Conflicts:**
- event-005 says £3,200 was taken; event-003 shows £1,200 reserved and £0.00 returned, with no £2,000 debit
- event-005 asks us to confirm the sender has been repaid; event-003 shows booked_return_amount £0.00 and decision pending
- event-005 came on the unauthenticated 'Customer chat'; event-004 came on the 'Authenticated customer chat'
- event-003 conflicts with event-005: £1,200 active vs £3,200 taken
- event-003 conflicts with event-005: £0.00 (nothing returned to sender yet) vs £3,200 taken

**We did:**
- Reconciled the ledger and reservation figures from event-001 and event-003
- Identified the hardship need and the worsening frustration
- Prepared a holding reply that discloses no account or payment status

**We did not:**
- Did not restore any funds or release or reduce HOLD-029 (this is the recovery team's decision, event-002)
- Did not tell the customer the sender has been paid back (records show £0.00 booked return and decision pending)
- Did not share balance or recovery figures on the unverified channel
- Did not promise any hardship payment or amount
- no change made to the account

**Question for you:** Can the recovery team review whether HOLD-029 (£1,200) can be reduced or partly released for essential spending while the IN-029 recovery decision is pending, and can a hardship review be opened for the customer? Please also contact the customer through the authenticated chat or a verified call. Explain that £1,200 is reserved, nothing has been returned to the sender yet, and £3,200 has not been taken.

**Safe to send now:** Thank you for telling us you need money for food. We've passed your request to the team who handle this, and we've asked for help with essential spending to be looked at. A colleague will contact you through your secure chat or a verified call to go through your account with you. Please don't share passwords or security codes in this chat.

## What failed

Nothing.
