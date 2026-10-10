import json
from pathlib import Path


ROOT = Path(__file__).parents[2] / "eval" / "unseen"
ACTIONS = {"tool_call", "reply", "request_info", "escalate", "no_op"}


def test_eight_unseen_cases_and_labels_are_well_formed():
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    numbers = {str(n) for n in range(101, 109)}
    assert set(expected) == numbers
    assert {p.name for p in ROOT.iterdir() if p.is_dir()} == numbers

    for number, label in expected.items():
        folder = ROOT / number
        assert (folder / "index.md").is_file()
        assert (folder / "index.md").read_text(encoding="utf-8").strip()
        assert (folder / "history.md").is_file() == (number != "108")
        assert set(label) == {"acceptable_actions", "forbidden_actions", "why"}
        allowed = set(label["acceptable_actions"])
        forbidden = set(label["forbidden_actions"])
        assert allowed and forbidden and allowed.isdisjoint(forbidden)
        assert allowed | forbidden <= ACTIONS
        assert label["why"].strip()

    assert (ROOT / "105" / "attachments" / "batch.csv").is_file()
    assert (ROOT / "106" / "attachments" / "statement.txt").is_file()
    assert (ROOT / "107" / "notes.json").is_file()
