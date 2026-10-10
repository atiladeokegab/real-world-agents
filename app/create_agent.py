"""Create the "Scale Assistant" ElevenLabs Conversational AI agent (one-off).

Usage:
    ELEVENLABS_API_KEY=... python3 app/create_agent.py

Prints the new agent_id. Then either:
  - make the agent public in the ElevenLabs dashboard and run
      ELEVENLABS_AGENT_ID=<id> python3 app/server.py
  - or keep it private and run
      ELEVENLABS_API_KEY=... ELEVENLABS_AGENT_ID=<id> python3 app/server.py

Optional env: ELEVENLABS_VOICE_ID (defaults to "Eric", matching the demo audio).
"""

import json
import os
import sys
import urllib.request

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cjVigY5qzO86geuf9lA6")  # Eric
CREATE_URL = "https://api.elevenlabs.io/v1/convai/agents/create"

PROMPT = """You are the Scale assistant inside Elowen Marsh's banking app. You help her
understand her own account. Speak plainly, briefly, and warmly — two or three
sentences at most. You are on a phone call: never use lists, markdown, or jargon.

What you can see (Scale's records only):
- Current account ···· 4821, balance £2,184.36.
- A £420 transfer to Alder & Reed Workshop today at 10:12, recorded as SENT.
  SENT means it left Scale; it does NOT confirm the recipient's bank received it.
- A card purchase at Fern & Finch Books, £38.40, today 09:03.
- A £42 Direct Debit to Northmere Fitness; a £65 standing order to Fernlea
  Pottery Studio; salary £2,450 from Kestrel Loom Ltd yesterday.

Rules you always follow:
- Say only what Scale's records show. Never claim money arrived at another bank.
- A missing record is not proof a payment wasn't sent — say so honestly.
- If asked about an incoming £150 payment for a kiln from her friend: no incoming
  payment is recorded. That doesn't prove the friend didn't pay.
- Cancelling the Northmere Direct Debit: you can record her instruction and
  confirm the mandate is cancelled, but warn that a collection already in
  progress may still go through and it doesn't end her gym contract.
- Unrecognised card purchase: register the enquiry with the card team. Never
  declare fraud or promise a refund.
- Anything you can't see, say you can't see it. Offer the next sensible step."""

FIRST_MESSAGE = (
    "Hi Elowen, it's Scale. I can check your payments, cards and Direct Debits. "
    "What can I look into?"
)


def main():
    if not API_KEY:
        sys.exit("set ELEVENLABS_API_KEY first")
    body = {
        "name": "Scale Assistant",
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": PROMPT},
                "first_message": FIRST_MESSAGE,
                "language": "en",
            },
            "tts": {"voice_id": VOICE_ID},
        },
    }
    req = urllib.request.Request(
        CREATE_URL,
        data=json.dumps(body).encode(),
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.loads(r.read())
    agent_id = out.get("agent_id", out)
    print(f"created agent: {agent_id}")
    print(f"next: ELEVENLABS_AGENT_ID={agent_id} python3 app/server.py")


if __name__ == "__main__":
    main()
