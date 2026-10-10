from agent.voice.case import build_case, handle


def test_unverified_by_default_and_reply_read_back(tmp_path):
    seen = {}

    def fake(path, out=None):
        seen["history"] = (path / "history.md").read_text()
        (tmp_path / "ANSWER.md").write_text("# Case\n\n## Customer message\nChannel: Secure chat\n\nYour transfer was sent.\n\n## Not done\n- none\n")
        return tmp_path

    assert handle("Was my transfer sent?", run_case=fake) == "Your transfer was sent."
    assert "External message" in seen["history"] and "Was my transfer sent?" in seen["history"]


def test_verified_call(tmp_path):
    assert "Verified call" in (build_case("hi", verified=True, root=tmp_path) / "history.md").read_text()
