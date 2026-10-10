import json
from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).parents[2] / "eval" / "unseen"
ACTIONS = {"tool_call", "reply", "request_info", "escalate", "no_op"}


def test_eight_unseen_cases_and_labels_are_well_formed():
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    numbers = {str(n) for n in range(101, 109)}
    assert set(expected) == numbers
    assert {p.name for p in ROOT.iterdir() if p.is_dir() and p.name.isdecimal()} == numbers

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


def test_dry_runner_lists_eight_cases_without_agent_calls(capsys):
    assert import_module("eval.unseen.run").main(["--dry"]) == 0
    output = capsys.readouterr().out
    assert all(f"{number} DRY" in output for number in range(101, 109))
    assert "total 8" in output


def test_score_rejects_system_fallback_even_if_action_is_acceptable():
    passes = import_module("eval.unseen.run").passes
    label = {"acceptable_actions": ["escalate"], "forbidden_actions": ["tool_call"]}
    assert passes(label, {"action": "escalate", "fallback": False}, 0)
    assert not passes(label, {"action": "escalate", "fallback": True}, 0)
    assert not passes(label, {"action": "tool_call", "fallback": False}, 0)
