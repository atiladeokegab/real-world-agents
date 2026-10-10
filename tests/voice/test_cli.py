from agent.voice.__main__ import main


def test_text_path_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    def fake(path, out=None):
        (tmp_path / "ANSWER.md").write_text("## Customer message\nChannel: x\n\nDone.\n")
        return tmp_path

    assert main("where is my transfer", run_case=fake) == "Done."
