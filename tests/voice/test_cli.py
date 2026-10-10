from agent.voice.__main__ import main


def test_text_path_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    def fake(path, out=None):
        (tmp_path / "ANSWER.md").write_text("## Customer message\nChannel: x\n\nDone.\n")
        return tmp_path

    assert main("where is my transfer", tmp_path / "o", run_case=fake) == "Done."


def test_default_never_touches_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    seen = {}

    def fake(path, out=None):
        seen["out"] = out
        out.mkdir(parents=True)
        (out / "ANSWER.md").write_text("## Customer message\nChannel: x\n\nDone.\n")
        return out

    assert main("hi", run_case=fake) == "Done."
    assert list(cwd.iterdir()) == [] and not seen["out"].is_relative_to(cwd)
