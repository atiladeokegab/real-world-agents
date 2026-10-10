"""ElevenLabs speech-to-text and text-to-speech. The client is built lazily so tests need no key."""

import os
from pathlib import Path

VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # ElevenLabs' stock "George"


def _client():
    from elevenlabs.client import ElevenLabs
    return ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def transcribe(audio: Path, client=None) -> str:
    client = client or _client()
    with open(audio, "rb") as f:
        return client.speech_to_text.convert(file=f, model_id="scribe_v1").text


def speak(text: str, out: Path, client=None) -> Path:
    client = client or _client()
    audio = client.text_to_speech.convert(VOICE_ID, text=text, model_id="eleven_multilingual_v2", output_format="mp3_44100_128")
    Path(out).write_bytes(b"".join(audio))
    return Path(out)
