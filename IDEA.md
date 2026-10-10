# The idea

Grew from Faisal's pitch, with additions from eleven papers the team chose and Prometheus's review.

## Problem

A bank's back office gets a steady stream of small customer requests: was my transfer sent, why
was my card declined, cancel this Direct Debit, where is my payroll file. Each one needs a precise
next step, and the dangerous mistakes are quiet ones: acting on an unverified caller, claiming a
payment arrived when the records only show nothing was found, sending a transfer twice after a
timeout, or ploughing on when the customer is getting upset. Today's AI agents make exactly these
mistakes: they trust wrong values that look right, retry payments blindly, and report success when
they shouldn't.

## The idea

**An autonomous bank operations agent that decides the right next step on each case, and proves
it was safe to take.** The model proposes; plain code checks the evidence, the customer's
authority and the bank's rules before anything happens; every case ends with an answer, the
reasoning, and a full trace a regulator could follow.

## What we build

- Reads a case exactly as the organisers ship it (request, history, CSV/PDF/text attachments).
- **Checks the evidence in code first**: totals against CSV rows, names against records, batch
  against row status, duplicates, dates, limits.
- Works in a **short loop**: look things up, then at most one checked change, then reply.
- **Authority comes from code**: identity and role from the channel, never from the model; money
  and account changes only with verified identity, within mandate, no open conflict.
- **Never does a money action twice**: keys built from the intent, a log of every change,
  approvals used once, timeouts marked "uncertain" and escalated.
- **Knows when to stop**: a fixed handling for each kind of exception, and an escalation note a
  person can act on (who, what's verified, what conflicts, what was and wasn't done, the question,
  a safe holding reply). Escalates early when the customer is in distress, not at every sign of
  frustration.
- **Writes `ANSWERS/<case>/ANSWER.md`, `REASONING.md` and `trace.log`** for every case, in
  parallel, one failure never stopping the run.
- **Tests itself before 16:30**: the 50 practice cases cut at the decision point, plus the same
  cases with faults injected (wrong amounts, contradictions, timeouts, hidden instructions), and
  8–10 hand-labelled cases scored on the final outcome. Each failure is traced to the stage that
  caused it.
- **A phone entry point** (ElevenLabs) that feeds a spoken request into the same loop, built
  only after the first end-to-end run.

## What we don't build

- No model training, classifiers or RL; no vector database.
- No elaborate UI: the demo is the working CLI and a real trace.
- No second production run, no per-stage model tuning (cut for time).
- Nothing the rules don't score: more agents or more code earn nothing on their own.

## The demo, in one line

A tricky bank case goes in; the agent checks the evidence, catches what's wrong, takes the one
safe action or hands over with a clear note, and the trace shows why.

## Areas and owners

Each person owns their area's directories outright (AGENTS.md §6). The core is the shared
contracts; only the lead changes it. Full design: `AGENT_SPEC.md`.

| Area | Directories | Owner | Issues |
|---|---|---|---|
| core | `agent/__init__.py`, `agent/core/`, `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore`, `tests/__init__.py`, `tests/conftest.py`, `tests/core/` | — | — |
| ingest | `agent/ingest/`, `tests/ingest/` | — | — |
| checks | `agent/checks/`, `tests/checks/` | — | — |
| brain | `agent/llm/`, `tests/llm/` | — | — |
| tools | `agent/tools/`, `tests/tools/` | — | — |
| eval | `eval/`, `tests/eval/` | — | — |
| voice | `agent/voice/`, `tests/voice/` | — | — |
| design | `docs/design.md`, `docs/mockup/` | — | — |
| submission | `README.md`, `ANSWERS/`, `media/` | — | — |
| examples (shared data) | `examples/` | — | — |
