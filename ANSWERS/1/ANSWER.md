# Answer — Case 001

## Decision

ESCALATED — Handed to Fraud Operations (inbound APP recovery requests), with Customer Support / Vulnerability team for the rent hardship: Meridian's recovery request (MER-FR-2026-081734) says the £2,600 was a purchase scam where the vehicle was never delivered. The customer's account and his exported evidence say the buyer collected the van in person on 21 Sep and paid from his drive. The system put a hold on all £750 of available funds. The customer is distressed and getting more upset, and his £900 rent is due tomorrow. Servicing has no tool or authority to release or part-release a fraud hold, and the reply to Meridian is due within 2 working days of 23 Sep 17:55.

## What we received

`index.md`, `history.md`, `attachments/account_hold_notice.txt`, `attachments/customer_evidence_listing.txt`, `attachments/customer_evidence_messages.txt`, `attachments/funds_recovery_request_MERIDIAN.txt` · 4 attachments · 6 events · identity: unverified Bank customer (Phone (personal banking))

## Actions

None.

## Customer reply

Channel: Phone (personal banking)

I understand your rent is due tomorrow and how worrying this is. I'm passing your case and the evidence you've described to our fraud operations team now as urgent, and asking them to look at the hold and your rent deadline. They'll contact you through your verified phone number or secure portal. Please keep the messages, listing and V5 slip ready to share.

## Not done

- Did not release or part-release the £750 hold (no tool or authority; this is a fraud operations decision) — because the case was handed to a person
- Did not promise that funds will be released or say when — because the case was handed to a person
- Did not share any further account or payment status beyond what was already said on the call, because the system shows identity as unverified
- Did not respond to Meridian — because the case was handed to a person
- Have not yet received or validated the V5C handover evidence — because the case was handed to a person
- no change made to the account — because the case was handed to a person

## Evidence used

- `event-001`
- `event-002`
- `event-003`
- `event-004`
- `event-006`

## Handover

**Take it:** Fraud Operations (inbound APP recovery requests), with Customer Support / Vulnerability team for the rent hardship

**Urgency:** Urgent

**Type:** Emotional

**Verified:**
- Credit of £2,600 by Faster Payment from L FARRELL (Meridian), ref VAN, 21 Sep 14:10 (event-001)
- Debit of £1,850 to BARCLAYCARD, his own card and a payee on file since 2022, at 21 Sep 16:40, before the recovery request (event-001)
- Recovery request received 23 Sep 17:55; system hold of £750.00 (all available funds) applied 23 Sep 17:56 (event-001, hold notice)
- Customer of 6 years, no fraud markers, no contact in 12 months, no other inbound credits from unknown parties in 90 days (event-001)
- Meridian request: no police reference supplied; no previous reports against the payee account
- The phone event (event-002) is tagged ID&V passed, but the system authority record shows identity as unverified. This needs to be reconciled before any account detail is discussed or changed.
- identity unverified via channel, role Bank customer

**Only claimed:**
- Customer says the payment was for his old Ford Transit sold on a marketplace, that the buyer collected it Monday 21 Sep and paid while on his drive, and that he holds the messages, the listing and the V5 handover (event-004)
- Exported listing: collection only, no delivery, marked SOLD 21 Sep 2026
- Exported chat with 'Lou F.': arrived 13:52, sending money ref VAN at 14:06, V5C green slip and both sets of keys handed over at 14:11
- Payer (via Meridian): the seller said the van would be delivered Tuesday; no van; seller not answering
- Rent of £900 is due tomorrow (event-006)
- £2,600 credit received_from Faster Payment from L FARRELL (Meridian Bank), ref VAN, 21 Sep 14:10 (Harrow & Vale Bank plc (case record), event-001)
- £1,850 debit paid_to BARCLAYCARD (customer's own card, payee on file since 2022), 21 Sep 16:40, before recovery request (Harrow & Vale Bank plc (case record), event-001)
- £2,600 payment reported_by_sending_bank_as APP purchase scam - vehicle not delivered; Meridian case ref MER-FR-2026-081734; payer says seller said van would be delivered Tuesday, no van, seller not answering (Meridian Bank plc Fraud Operations (relaying payer L Farrell), event-001)
- Account hold amount £750.00 held (all available funds) on 23 Sep 17:56 by system; balance £750.00 (Harrow & Vale Bank plc (case record), event-001)
- £2,600 payment was_for Sale of customer's old Ford Transit via marketplace; buyer collected it Monday and paid by transfer while standing on his drive (Customer (Marcus Bell), event-004)
- Marketplace listing states Ford Transit Custom 2017, £2,600, collection only, no delivery; marked SOLD 21 Sep 2026 (Customer (exported listing), event-004)
- Marketplace chat with 'Lou F.' shows Buyer arranged Monday 2pm viewing, arrived 21 Sep 13:52, said sending money ref VAN at 14:06; seller confirmed receipt, V5C green slip and both keys handed over at 14:11 (Customer (exported messages), event-004)
- Customer evidence customer_says_holds Messages, listing and V5 handover (Customer (Marcus Bell), event-004)

**Conflicts:**
- Meridian's payer statement (non-delivery, delivery promised for Tuesday) conflicts with the customer's account and exported evidence (collection in person, listing says collection only) (event-001 vs event-004)
- Authority record shows identity unverified, while event-002 is tagged [ID&V passed]
- event-001 conflicts with event-004: APP purchase scam - vehicle not delivered; Meridian case ref MER-FR-2026-081734; payer says seller said van would be delivered Tuesday, no van, seller not answering vs Sale of customer's old Ford Transit via marketplace; buyer collected it Monday and paid by transfer while standing on his drive
- event-001 conflicts with event-004: APP purchase scam - vehicle not delivered; Meridian case ref MER-FR-2026-081734; payer says seller said van would be delivered Tuesday, no van, seller not answering vs Ford Transit Custom 2017, £2,600, collection only, no delivery; marked SOLD 21 Sep 2026
- event-001 conflicts with event-004: APP purchase scam - vehicle not delivered; Meridian case ref MER-FR-2026-081734; payer says seller said van would be delivered Tuesday, no van, seller not answering vs Buyer arranged Monday 2pm viewing, arrived 21 Sep 13:52, said sending money ref VAN at 14:06; seller confirmed receipt, V5C green slip and both keys handed over at 14:11

**We did:**
- Read the case record, the hold notice, the Meridian recovery request and the customer's exported listing and chat
- Recorded the customer's explanation and the rent deadline

**We did not:**
- Did not release or part-release the £750 hold (no tool or authority; this is a fraud operations decision)
- Did not promise that funds will be released or say when
- Did not share any further account or payment status beyond what was already said on the call, because the system shows identity as unverified
- Did not respond to Meridian
- Have not yet received or validated the V5C handover evidence
- no change made to the account

**Question for you:** Based on the customer's evidence (listing marked collection only, chat showing in-person collection and V5C/keys handover, no police reference from the payer), can any or all of the £750 hold be released or part-released before his £900 rent falls due tomorrow? If not, what hardship support can we offer, and how and by when will his evidence go to Meridian for case MER-FR-2026-081734?

**Safe to send now:** I understand your rent is due tomorrow and how worrying this is. I'm passing your case and the evidence you've described to our fraud operations team now as urgent, and asking them to look at the hold and your rent deadline. They'll contact you through your verified phone number or secure portal. Please keep the messages, listing and V5 slip ready to share.

## What failed

Nothing.
