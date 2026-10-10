"""H&V customer app: serves the mobile app and a chat API backed by the Scale agent.

Run: uv run python -m app.server   →   http://localhost:8765
"""

import json
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anthropic
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

HERE = Path(__file__).parent
PORT = int(os.environ.get("APP_PORT", "8765"))
CHAT_MODEL = os.environ.get("APP_CHAT_MODEL", "claude-haiku-5-5")
CUSTOMER = "Elowen Marsh"
BANK = "Harrow & Vale Bank plc"
MAX_MESSAGE = 2000

# What each agent stage means to a customer.
STAGE_COPY = {
    "ingest": "Reading your message",
    "identity": "Confirming it's you",
    "evidence": "Checking the details for anything unusual",
    "extract": "Understanding what you need",
    "decide": "Working out the right next step",
    "verify": "Running our safety checks",
    "execute": "Checking your account records",
    "write": "Writing your answer",
}

CHAT_SYSTEM = f"""You are the assistant in the {BANK} (H&V) mobile app, talking to the signed-in customer, {CUSTOMER}.
Be warm, brief and plain: two short sentences at most.
You cannot see accounts, payments or records yourself. Whenever the customer asks about their money, a payment,
a card, a Direct Debit, a statement or anything that needs their records or a change, call `open_request` with
their request written clearly in their own voice, including every detail they gave (amounts, names, dates).
Don't promise outcomes. For greetings or general questions, just reply."""

OPEN_REQUEST = {
    "name": "open_request",
    "description": "Hand the customer's request to H&V's case agent, which checks records, applies the bank's rules and replies.",
    "input_schema": {
        "type": "object",
        "properties": {
            "request": {"type": "string", "description": "The customer's request in their own words, with every detail they gave."},
            "acknowledgement": {"type": "string", "description": "One short sentence telling the customer you're checking now."},
        },
        "required": ["request", "acknowledgement"],
    },
}

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def _client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY_DECISION") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("No Anthropic key: set ANTHROPIC_API_KEY_DECISION in .env")
    return anthropic.Anthropic(api_key=key, max_retries=4)


def _safe(text: str) -> str:
    """Customer words must never parse as case markup."""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return "\n".join(" " + l if l.lstrip().startswith(("#", "- **", "---")) else l for l in text.splitlines())


def build_case(request: str, context: str | None) -> Path:
    """An in-app message is a Secure chat event from the signed-in customer: the channel sets the trust."""
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    path = Path(tempfile.mkdtemp(prefix="app-case-"))
    body = _safe(request if not context else f"{request}\n\n(Asked from the app, about: {context})")
    (path / "index.md").write_text(
        f"# Case app-{now:%H%M%S}: In-app request\n\n## Case details\n\n- **Source role:** Bank customer\n"
        f"- **Bank:** {BANK}\n- **Created:** {stamp}\n\n## Initial request\n\n{body}\n", encoding="utf-8")
    (path / "history.md").write_text(
        f"# Case app history — In-app request\n\nTotal events: 1\n\n"
        f'<a id="event-001"></a>\n## {stamp} — event 001\n\n'
        f"- **Channel:** Secure chat\n- **From:** {CUSTOMER}\n- **To:** H&V service agent\n\n{body}\n", encoding="utf-8")
    return path


def _answer(out: Path) -> dict:
    """The parts of the agent's files the customer sees."""
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    answer = (out / "ANSWER.md").read_text(encoding="utf-8")
    m = re.search(r"## Customer (?:reply|message)\n\n?(?:Channel:[^\n]*\n\n)?(.*?)\n*(?:\n## |\Z)", answer, re.S)
    reply = m.group(1).strip() if m else ""
    team = None
    h = re.search(r"\*\*Take it:\*\*\s*([^\n]+)|- who:\s*([^\n]+)", answer)
    if h:
        team = (h.group(1) or h.group(2)).strip()
    return {
        "state": run.get("state") or run.get("outcome"),
        "escalated": bool(run.get("escalated")),
        "reply": reply or "Thanks for your message. A member of our team will pick this up and reply here.",
        "team": team,
        "seconds": run.get("seconds"),
    }


def _run_job(job_id: str, request: str, context: str | None) -> None:
    from agent.core.loop import run_case  # the agent, imported on first use

    def on_stage(stage: str, text: str) -> None:
        with JOBS_LOCK:
            steps = JOBS[job_id]["steps"]
            blocked = text.lstrip().startswith("✗")
            label = "A safety check caught something, so the answer was rewritten" if blocked else STAGE_COPY.get(stage, stage)
            if all(s["label"] != label for s in steps):  # each step once, in the order first reached
                steps.append({"stage": stage, "label": label, "blocked": blocked})

    try:
        out = run_case(build_case(request, context), Path(tempfile.mkdtemp(prefix="app-answer-")), on_stage=on_stage)
        result = _answer(out)
    except Exception as exc:  # the loop writes a fallback, so this is a server-side failure
        result = {"state": "failure", "escalated": True, "team": None, "seconds": None,
                  "reply": "Sorry, something went wrong on our side. We've passed your message to our team, who will reply here.",
                  "error": str(exc)}
    with JOBS_LOCK:
        JOBS[job_id].update(done=True, result=result)


def chat(messages: list[dict], context: str | None) -> dict:
    """Small talk is answered here; anything about the customer's money opens a request with the agent."""
    clean = [{"role": m["role"], "content": str(m["content"])[:MAX_MESSAGE]}
             for m in messages[-12:] if m.get("role") in ("user", "assistant") and m.get("content")]
    if not clean or clean[-1]["role"] != "user":
        raise ValueError("the last message must come from the customer")
    system = CHAT_SYSTEM + (f"\nThe customer opened the chat from: {context}." if context else "")
    resp = _client().messages.create(model=CHAT_MODEL, max_tokens=400, system=system, tools=[OPEN_REQUEST], messages=clean)
    tool = next((b for b in resp.content if b.type == "tool_use" and b.name == "open_request"), None)
    if not tool:
        text = " ".join(b.text for b in resp.content if b.type == "text").strip()
        return {"reply": text or "How can I help?"}
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"steps": [], "done": False, "result": None, "request": tool.input["request"]}
    threading.Thread(target=_run_job, args=(job_id, tool.input["request"], context), daemon=True).start()
    return {"reply": tool.input.get("acknowledgement") or "Let me check that for you now.", "job": job_id}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            return self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        m = re.fullmatch(r"/api/job/([0-9a-f]{12})", self.path)
        if m:
            with JOBS_LOCK:
                job = JOBS.get(m.group(1))
                if not job:
                    return self._json(404, {"error": "unknown request"})
                return self._json(200, {"steps": job["steps"], "done": job["done"], "result": job["result"]})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 64_000:
                return self._json(413, {"error": "message too long"})
            data = json.loads(self.rfile.read(length) or b"{}")
            context = data.get("context")
            self._json(200, chat(data.get("messages") or [], str(context)[:300] if context else None))
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self.log_error("chat failed: %s", exc)
            self._json(502, {"error": "The assistant is unavailable right now. Please try again."})

    def log_message(self, fmt: str, *args) -> None:
        if "/api/job/" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"H&V app on http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
