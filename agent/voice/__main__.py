"""Demo: uv run python -m agent.voice <audio-file-or-text>   (audio needs ELEVENLABS_API_KEY; text works without)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent.voice import case, speech


def main(arg: str, out: Path | None = None, run_case=None, client=None) -> str:
    p = Path(arg)
    is_audio = p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"} and p.exists()
    text = speech.transcribe(p, client) if is_audio else arg
    print(f"Heard: {text}")
    reply = case.handle(text, out=out, run_case=run_case)
    print(f"Reply: {reply}")
    if client or os.environ.get("ELEVENLABS_API_KEY"):
        print(f"Spoken reply: {speech.speak(reply, Path('reply.mp3') if out is None else out / 'reply.mp3', client)}")
    return reply


if __name__ == "__main__":
    load_dotenv()
    main(" ".join(sys.argv[1:]))
