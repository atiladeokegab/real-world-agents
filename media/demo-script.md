# Demo script, 60 seconds (draft for #7)

Case: **044**, "One Line in the Supplier Batch" (`examples/044`). The portal says the batch is
*Processed*; the customer asks about row SUP-17. This shows the evidence checker's status finding
(batch status vs row status, AGENT_SPEC.md 4.2), the verifier verdict (4.6), the handover (4.8)
and the trace (4.9).

Rule for every shot: a real command and its real output. Anything not run yet is marked
`TODO: capture from real run`. No output below is invented; the spoken lines only restate what
the case files and the spec say.

Spoken length: about 140 words at a calm pace. Time it with a stopwatch before recording.

| Time | Shot (screen) | Say |
|---|---|---|
| 0:00-0:10 | `examples/044/history.md`, event 001 and 002 highlighted: "Batch ... status: Processed." and "I can't tell whether row SUP-17 was paid." | "A bank says the supplier batch is processed. The customer asks: was one payment, SUP-17, actually paid? The quiet mistake is saying yes because the batch looks fine." |
| 0:10-0:20 | Terminal: `uv run agent run --case examples/044 --out ANSWERS/044` then its printed result. `TODO: capture from real run` | "We hand the case to our agent. The model proposes. Plain code checks the evidence, the caller's authority and the bank's rules." |
| 0:20-0:35 | `ANSWERS/044/trace.log`, scroll to the evidence-checker finding. `TODO: capture from real run` (expected: a status finding, batch Processed vs row; confirm the exact text and event IDs on screen before speaking) | "Before the model reasons, code checks what it reads. Here it flags that the batch status and the row status are different things, with the event IDs." |
| 0:35-0:45 | Same trace.log, the verifier verdict line and the one tool call (journal lookup of SUP-17). `TODO: capture from real run` | "The verifier accepts one read-only lookup, and only because the finding is addressed. The portal shows SUP-17 rejected: beneficiary details did not match." |
| 0:45-0:50 | `ANSWERS/044/ANSWER.md`: the decision, the reply to the customer, the "not done" list. `TODO: capture from real run` | "The customer gets the real answer, and the agent lists what it did not do: it did not re-check the other rows or change anything." |
| 0:50-0:57 | Terminal: `uv run python -m eval` summary. `TODO: capture from real run` (placeholder numbers must not be spoken; read only what prints) | "We score ourselves on the 50 practice cases, with faults injected: <TODO: outcome number from the real run>." |
| 0:57-1:00 | Title card: repo name | "A tricky case in. The agent catches what is wrong, acts safely or hands over, and the trace shows why." |

## Optional 5 s voice moment (swap for the 0:50 shot only if time allows)

Terminal: `uv run python -m agent.voice "Was row SUP-17 in our supplier batch paid?"`, showing the
`Heard:` and `Reply:` lines it prints. `TODO: capture from real run` (voice is PR #36, not on
integration yet; text mode works without a key, audio needs `ELEVENLABS_API_KEY`).

## Backup case

Case 006 (two similar transfers, one completed and one pending, nothing cancelled) if 044's
finding does not read clearly in the real trace. Same shots, swap the case folder and the
highlighted lines.

## Before recording

- [ ] Run the e2e on 044 after merge of core loop, brain and ingest; fill every TODO from that run.
- [ ] Confirm the finding and verdict text on screen; edit the spoken lines to match them exactly.
- [ ] Read aloud with a timer; cut words, not shots, to land on 60 s.
