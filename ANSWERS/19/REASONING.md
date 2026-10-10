# Reasoning — Case 019

## Facts and claims

- Claim: Payment HV26081210144802 debit £651.00 Faster Payment to CO-CLEAN SERVICES LTD on 12 Aug 2026, ref 'INV 4471 53 WINCHESTER', new payee, CoP match at the time, status Completed (Harrow & Vale Bank plc (case record), Internal account view, `event-001`)
- Claim: Co-Clean invoice 4471 also paid by managing agent Oakfield PM paid £651 to Co-Clean from rental funds on 15 Aug 2026 (Customer, Internal account view, `event-001`)
- Claim: Co-Clean refund agreed Co-Clean agreed on 17 Sep to refund £651 'on the next payment run' (Customer, Internal account view, `event-001`)
- Claim: Co-Clean refund not yet received Refund agreed but a week has passed without it arriving (Customer, In-app chat (personal banking), `event-002`)
- Claim: Payment of 12 Aug characterised as duplicate payment, which customer believes is what recalls are for (Customer, In-app chat (personal banking), `event-004`)
- Claim: Payment of 12 Aug possible duplicate (code finding-1) case text describes a possible duplicate payment/instruction (Evidence check (duplicates), findings, `event-001`)

## Findings

- **finding-1 · duplicates** (anomaly) — the case text describes a possible duplicate payment/instruction (event-001, event-004). Addressed.

## Policy checks

- Identity: unverified (In-app chat (personal banking))
- Authority: role Bank customer
- Risk level: no tool used
- Completion: 1 of 1 ask closed
- Verifier: ✓ approved the final proposal

## Exception and handling

missing_authority → request_info via a verified channel; no change

## Alternatives rejected

None.

## Uncertainties

- Whether a recall applies at all: the payment went to the correct, intended payee for a valid invoice (it was not a mistaken or misdirected payment), and the duplicate came from a separate payer (Oakfield PM)
- Whether Co-Clean's £651 refund has already been sent or received in the customer's account since 17 Sep
- When Co-Clean's next payment run is
- Whether Co-Clean would agree to return funds through a bank recall rather than its own refund, and whether that could end up refunding twice
- Whether Co-Clean might refund Oakfield PM instead of the customer
- The agency statement and Co-Clean email were supplied by the customer and have not been checked independently
- ask-1 (recall) not actioned: identity is unverified, so no change can be requested and no payment status can be shared. Next step is to verify through the secure portal or a verified call.
- finding-1 (possible duplicate): the payment of 12 Aug appears to have gone to the correct, intended payee for a real invoice. The second payment came from a separate payer (Oakfield PM), so a recall/return request may not apply and could lead to a double refund alongside Co-Clean's promised refund.
- Not yet known whether Co-Clean's £651 refund has been sent or has reached the customer's account since 17 Sep; this hasn't been looked up and couldn't be disclosed until she is verified.
- Co-Clean email and agency statement were supplied by the customer and haven't been checked independently. Possible risk that Co-Clean refunds Oakfield PM instead of her.
- Customer is frustrated (steady); this is acknowledged in the reply. No complaint has been made yet.
