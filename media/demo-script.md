# Demo script, 60 seconds

Shots below come from a real run on `origin/integration` (2026-10-10, after the claim-linter fix
#98), command and output unedited. The run was clean: no rejection, no retry.

Case **044**, "One Line in the Supplier Batch" (`examples/044`): the portal says the batch is
*Processed*; the customer asks about row SUP-17. Backup: case **006** (two similar transfers), run
the same way (`--case examples/006`, one `transfer_journal` read; captured before the linter fix, re-run if used).

Demo output goes to `/tmp/demo/...`, outside the repo, and is never committed: `ANSWERS/` holds
only the Reality Test answers (RULES.md section C). Nothing here is invented; the only open item
is the eval figure, which comes from eval round 5 and may be refreshed.

The live run takes 28.3 s. In the video, start it and cut to the finished output (say so in the
caption: "sped up"), or run it beforehand and show the saved output.

| Time | Shot (screen) | Say |
|---|---|---|
| 0:00-0:08 | `examples/044/history.md`, events 001-002 highlighted: "Batch ... status: Processed." and "I can't tell whether row SUP-17 ... was paid." | "A portal says the supplier batch is processed. The customer asks: was row SUP-17 paid? The quiet mistake is saying yes because the batch looks fine." |
| 0:08-0:18 | Terminal: `uv run agent run --case examples/044 --cut 2 --out /tmp/demo/044`. Output, real: `ingest 2 events · 0 attachments · cut at event-002`, `identity authenticated Authorised business user · Secure chat`, then `evidence 1 finding · a collection-level status is asserted while a member line's status is unclear or contradicts it` | "Before the model reasons, code checks the evidence and flags it: a batch status is being used to answer about one row." |
| 0:18-0:28 | Same output, next lines: `decide tool_call business_service (...Line-level status of row SUP-17 (paid, rejected, pending or returned)...)`, `verify ✓ approved`, `execute business_service → done` | "The model proposes one read-only lookup. Code checks it, approves it, runs it." |
| 0:28-0:36 | Same output: `decide reply · Secure chat`, `verify ✓ approved`, then `● DONE  1 action · 0 escalations · 28.3s` | "The reply is checked by code before it is sent. It passes, with no escalation." |
| 0:36-0:42 | `/tmp/demo/044/ANSWER.md`, "Customer reply": "I've checked row SUP-17 ... It was rejected, not paid. The reason given is that the beneficiary details didn't match the receiving bank's records. The 'Processed' status covers the batch as a whole ... I haven't changed or resent anything." Then `trace.log`, the `finding-1` and `== verdict ==` blocks. | "The customer gets the true answer: rejected, and why. Nothing changed." |
| 0:42-0:50 | Voice, played aloud. Terminal: `uv run python -m agent.voice --out /tmp/voice-demo2 /tmp/voice-demo/in.mp3`, then play `/tmp/voice-demo2/reply.mp3`. Real run (about 40 s, shown sped up): a caller asks whether a £420 transfer to Alder and Reed Workshop was sent; it is treated as an unverified message (voice does not prove identity); `transfer_journal` returns pending; the verifier blocked one draft that said "confirmed" with no result behind it. Decision line: `REQUESTED — Asked transfer_journal for a result. No result yet.` | "The same loop takes a phone call, and won't say a payment was sent without a result." |
| 0:50-0:55 | Terminal: `uv run python -m eval` summary. Source: eval round 5, `claude-opus-5-5`, 50 practice cases (`--judgement --report`). Re-capture if a later round changes the numbers. | "On 50 practice cases: 98% of first actions match the bank's, and 9/10 judgement cases are handled safely." |
| 0:55-1:00 | Title card: repo name | "A tricky case in. The agent catches what is wrong, acts safely, and shows why." |

Spoken length: 137 words (60 s at a calm pace, 140 words or fewer). Confirm with a stopwatch.

## Voice moment

The 0:42 row is a real run (audio kept outside the repo; do not commit `reply.mp3`). It needs `ELEVENLABS_API_KEY`.

## Before recording

- [ ] Time it with a stopwatch.
