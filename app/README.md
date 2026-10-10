# H&V customer app (frontend branch)

The customer side of Scale: Elowen's Harrow & Vale mobile banking app. Home (balance and activity),
a payment detail, and an assistant in the bottom-right. The assistant chats normally; when the
customer asks about their money, it opens a request with the Scale agent (`run_case`), shows the
agent's progress in plain English, then the agent's real reply and status: answered, requested
(waiting on our team) or passed to a person.

Run from the repo root, with the keys in `.env`:

```bash
uv run python -m app.server
```

Then open http://localhost:8765. Every in-app message is a Secure chat event from the signed-in
customer, so the agent treats her as authenticated. Balances and transactions are sample data for
a fictional bank; the replies come from the real agent.
