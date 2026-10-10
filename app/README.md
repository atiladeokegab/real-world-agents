# Scale customer app (frontend branch, demo)

A phone-sized banking app for the demo: home (balance and activity), a payment detail, and the
Scale assistant in the bottom-right. Conversations are scripted from the organisers' practice
cases (Banking 002, 001, 015, 023). Each one plays out as a live case history in history.md style,
then a reply read aloud by an ElevenLabs voice (pre-generated in `audio/`).

```bash
python3 -m http.server 8765 --directory app
```

Then open http://localhost:8765.

## Live voice chat (ElevenLabs Conversational AI)

The 🎙 button in the composer starts a real voice call with a "Scale Assistant"
ElevenLabs agent — the customer speaks, the agent answers aloud, and the transcript
appears as chat bubbles. Serve the app with `app/server.py` instead:

```bash
# 1. one-off: create the agent (needs your key once, never committed)
ELEVENLABS_API_KEY=... python3 app/create_agent.py   # prints an agent_id

# 2a. public agent (set "public" in the ElevenLabs dashboard):
ELEVENLABS_AGENT_ID=agent_... python3 app/server.py

# 2b. private agent (key stays server-side, the page gets a signed url):
ELEVENLABS_API_KEY=... ELEVENLABS_AGENT_ID=agent_... python3 app/server.py
```

Or skip the server: `http://localhost:8765/?agent=agent_...` works for a public
agent on the plain `http.server` too. With no agent configured, the mic button
says voice isn't set up and everything else is unchanged. The SDK loads from a
CDN (`@elevenlabs/client`, pinned) only when a call starts.
