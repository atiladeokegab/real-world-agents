from types import SimpleNamespace

from agent.voice.speech import speak, transcribe


class Fake:
    speech_to_text = SimpleNamespace(convert=lambda file, model_id: SimpleNamespace(text="hello"))
    text_to_speech = SimpleNamespace(convert=lambda voice, **kw: iter([b"ab", b"cd"]))


def test_roundtrip(tmp_path):
    a = tmp_path / "a.mp3"
    a.write_bytes(b"x")
    assert transcribe(a, Fake()) == "hello"
    assert speak("hi", tmp_path / "o.mp3", Fake()).read_bytes() == b"abcd"
