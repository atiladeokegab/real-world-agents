import pytest

from agent.tools import execute, with_faults
from agent.tools._contracts import Proposal
from agent.tools.executor import Ledger
from tests.tools.conftest import practice


def tc(tool, **params):
    return Proposal(action="tool_call", tool=tool, params=params)


def test_clean_is_pass_through(tmp_path):
    case, later = practice("009")
    p = tc("transfer_journal")
    assert with_faults(None)(p, case, tmp_path, later) == execute(p, case, tmp_path, later)


def test_read_timeout(tmp_path):
    case, later = practice("009")
    assert with_faults("timeout")(tc("transfer_journal"), case, tmp_path, later).status == "timeout"


def test_write_timeout_after_commit_is_uncertain_and_not_repeated(tmp_path):
    case, later = practice("022")
    faulty = with_faults("timeout")
    p = tc("card_service.block", card="debit")
    assert faulty(p, case, tmp_path, later).status == "uncertain"
    assert execute(p, case, tmp_path, later).status == "uncertain"  # ledger: no second block
    assert len(Ledger(tmp_path, "022").entries) == 1


def test_wrong_amount_shifts_20_to_60_percent(tmp_path):
    case, later = practice("009")
    clean = execute(tc("transfer_journal"), case, tmp_path, later)
    r = with_faults("wrong_amount", seed=3)(tc("transfer_journal"), case, tmp_path, later)
    assert "£648.20" in clean.data["note"] and "£648.20" not in r.data["note"]
    shifted = float(r.data["note"].split("£")[1].split()[0].rstrip(".;,"))
    assert 0.2 <= abs(shifted / 648.20 - 1) <= 0.6
    assert r.source_event == clean.source_event


def test_dropped_row(tmp_path):
    case, later = practice("009")
    clean = execute(tc("transfer_journal"), case, tmp_path, later)
    r = with_faults("dropped_row")(tc("transfer_journal"), case, tmp_path, later)
    assert len(r.data["lines"]) == len(clean.data["lines"]) - 1


def test_env_switch(tmp_path, monkeypatch):
    case, later = practice("009")
    monkeypatch.setenv("AGENT_TOOL_FAULT", "timeout")
    assert execute(tc("transfer_journal"), case, tmp_path, later).status == "timeout"


def test_unknown_fault():
    with pytest.raises(ValueError):
        with_faults("gremlins")


def test_seed_is_deterministic(tmp_path):
    case, later = practice("009")
    a = with_faults("wrong_amount", seed=7)(tc("transfer_journal"), case, tmp_path, later)
    b = with_faults("wrong_amount", seed=7)(tc("transfer_journal"), case, tmp_path, later)
    assert a == b
