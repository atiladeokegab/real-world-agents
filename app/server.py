"""Scale demo app server (frontend branch only, never merged to integration).

Serves the static app exactly like `python3 -m http.server`, plus two small
endpoints that let the page start an ElevenLabs Conversational AI voice
session without shipping a key in the repo:

    GET /api/voice/config      -> {"agentId": ..., "private": bool}
    GET /api/voice/signed-url  -> ElevenLabs get-signed-url proxy (private agents)

Env vars (never committed):
    ELEVENLABS_AGENT_ID   public agent: this alone is enough
    ELEVENLABS_API_KEY    private agent: also needed, stays server-side
    PORT                  default 8765
"""

import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT_ID = os.environ.get("ELEVENLABS_AGENT_ID", "")
API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
SIGNED_URL_API = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/voice/config":
            return self._json({"agentId": AGENT_ID, "private": bool(API_KEY)})
        if path == "/api/voice/signed-url":
            return self._signed_url()
        return super().do_GET()

    def _signed_url(self):
        if not (API_KEY and AGENT_ID):
            return self._json({"error": "voice not configured"}, 503)
        req = urllib.request.Request(
            f"{SIGNED_URL_API}?agent_id={AGENT_ID}", headers={"xi-api-key": API_KEY}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return self._json(json.loads(r.read()))
        except urllib.error.HTTPError as e:
            return self._json({"error": f"ElevenLabs {e.code}"}, 502)
        except Exception as e:
            return self._json({"error": str(e)}, 502)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    print(f"Scale app on http://localhost:{port}")
    print("voice:", "configured" if AGENT_ID else "not configured (set ELEVENLABS_AGENT_ID)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
