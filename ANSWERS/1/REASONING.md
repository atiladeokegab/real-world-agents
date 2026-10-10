# Reasoning — Case 001

## Facts and claims

- Claim: £2,600 credit received_from Faster Payment from L FARRELL (Meridian Bank), ref VAN, 21 Sep 14:10 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: £1,850 debit paid_to BARCLAYCARD (customer's own card, payee on file since 2022), 21 Sep 16:40, before recovery request (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: £2,600 payment reported_by_sending_bank_as APP purchase scam - vehicle not delivered; Meridian case ref MER-FR-2026-081734; payer says seller said van would be delivered Tuesday, no van, seller not answering (Meridian Bank plc Fraud Operations (relaying payer L Farrell), Interbank funds recovery request (attachment), `event-001`)
- Claim: Account hold amount £750.00 held (all available funds) on 23 Sep 17:56 by system; balance £750.00 (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: £2,600 payment was_for Sale of customer's old Ford Transit via marketplace; buyer collected it Monday and paid by transfer while standing on his drive (Customer (Marcus Bell), Phone (personal banking), `event-004`)
- Claim: Marketplace listing states Ford Transit Custom 2017, £2,600, collection only, no delivery; marked SOLD 21 Sep 2026 (Customer (exported listing), Attachment customer_evidence_listing.txt, `event-004`)
- Claim: Marketplace chat with 'Lou F.' shows Buyer arranged Monday 2pm viewing, arrived 21 Sep 13:52, said sending money ref VAN at 14:06; seller confirmed receipt, V5C green slip and both keys handed over at 14:11 (Customer (exported messages), Attachment customer_evidence_messages.txt, `event-004`)
- Claim: Customer evidence customer_says_holds Messages, listing and V5 handover (Customer (Marcus Bell), Phone (personal banking), `event-004`)
- Claim: £2,600 proceeds used_for Most of it paid off his credit card (Customer (Marcus Bell), Phone (personal banking), `event-004`)
- Claim: Customer rent amount_and_due £900, due tomorrow (Customer (Marcus Bell), Phone (personal banking), `event-006`)
- Claim: Customer profile history 6 years with bank, no fraud markers, no contact in 12 months, no other inbound payments from unknown parties in 90 days (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Recovery request notes No police reference supplied; no previous reports against payee account; reported by payer 23 Sep 16:40 (Meridian Bank plc Fraud Operations, Interbank funds recovery request (attachment), `event-001`)

## Findings

None.

## Policy checks

- Identity: unverified (Phone (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 2 of 2 asks closed
- Verifier: ✓ approved the final proposal

## Exception and handling

conflicting_records → report both, claim neither; route the check to the owning team

## Alternatives rejected

None.

## Uncertainties

- Whether the payer's claim (vehicle not delivered) or the customer's account (collected Monday) is true; outcome of the scam review
- Whether the customer's exported listing and chat are genuine and whether 'Lou F.' is the same person as payer L FARRELL
- V5C handover evidence mentioned by customer has not been provided
- Whether any or all of the £750 hold can be released or partly released before the review ends, and who has authority to approve that
- Status of H&V's response to Meridian (due within 2 working days of 23 Sep)
- Whether the customer has other funds or needs hardship/vulnerability support for the rent due tomorrow
- Whether Meridian or the payer has supplied a police reference or further evidence
- How the customer's evidence will be shared with Meridian and what the timeline is
- ask-1: the agent already explained the reason for the hold on the call (event-003). Any further detail is left to fraud operations, because the system shows identity as unverified even though event-002 is tagged ID&V passed.
- ask-2: not done. Releasing the hold needs a fraud operations decision and there is no tool for it. Escalated as urgent because the rent is due tomorrow.
- Whether the buyer 'Lou F.' is the same person as the payer L FARRELL, and whether the exported evidence is genuine, are both unknown.
- The V5C evidence has not been provided yet.
- Whether H&V has replied to Meridian yet is unknown.
