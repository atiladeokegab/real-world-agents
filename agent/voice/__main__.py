"""Demo: uv run python -m agent.voice <audio-file-or-text>   (audio needs ELEVENLABS_API_KEY; text works without)."""

import argparse
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from agent.voice import case, speech


def main(arg: str, out: Path | None = None, run_case=None, client=None) -> str:
    out = Path(out) if out else Path(tempfile.mkdtemp(prefix="voice-out-"))
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    p = Path(arg)
    is_audio = p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"} and p.exists()
    text = speech.transcribe(p, client) if is_audio else arg
    print(f"Heard: {text}")
    reply = case.handle(text, out=out, run_case=run_case)
    print(f"Reply: {reply}")
    if client or os.environ.get("ELEVENLABS_API_KEY"):
        print(f"Spoken reply: {speech.speak(reply, out / 'reply.mp3', client)}")
    return reply


if __name__ == "__main__":
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("request", nargs="+", help="audio file or text")
    ap.add_argument("--out", type=Path, help="output dir (default: a new temp dir)")
    a = ap.parse_args()
    main(" ".join(a.request), a.out)
