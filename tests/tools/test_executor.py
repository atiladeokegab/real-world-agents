from agent.tools import execute
from agent.tools._contracts import Proposal, ToolResult
from agent.tools.executor import Ledger, run
from tests.tools.conftest import practice


def tc(tool, **params):
    return Proposal(action="tool_call", tool=tool, params=params)


def counting(result_status="ok"):
    calls = []

    def backend(spec, params, case, events):
        calls.append(spec.name)
        return ToolResult(tool=spec.name, params=params, status=result_status, data={"n": len(calls)})
    return backend, calls


def test_read_from_practice_journal(tmp_path):
    case, later = practice("048")
    r = execute(tc("transfer_journal", query="incoming credit"), case, tmp_path, later)
    assert r.status == "ok" and r.source_event == "event-004"


def test_unseen_write_is_pending_never_done(tmp_path):
    case, _ = practice("022")
    r = execute(tc("card_service.block", card="debit card"), case, tmp_path)
    assert r.status == "pending"


def test_same_intent_runs_once(tmp_path):
    case, later = practice("005")
    backend, calls = counting()
    p = tc("transfer_journal.return_request", reference="T-1", amount="£250.00", payee="A Smith")
    first = run(p, case, tmp_path, later, backend)
    again = run(tc("transfer_journal.return_request", reference="t-1 ", amount="250", payee="a smith"),
                case, tmp_path, later, backend)
    assert calls == ["transfer_journal.return_request"] and again == first
    assert len(Ledger(tmp_path, "005").entries) == 1


def test_ledger_survives_a_new_process(tmp_path):
    case, later = practice("005")
    backend, calls = counting()
    p = tc("transfer_journal.return_request", reference="T-1", amount="250", payee="A")
    run(p, case, tmp_path, later, backend)
    Ledger(tmp_path, "005")  # re-read from disk
    run(p, case, tmp_path, later, backend)
    assert len(calls) == 1


def test_different_intent_on_same_target_is_blocked(tmp_path):
    case, later = practice("012")
    backend, calls = counting()
    run(tc("standing_order_journal.amend", reference="SO-9", amount="40", date="1 Aug"), case, tmp_path, later, backend)
    r = run(tc("standing_order_journal.cancel", reference="SO-9"), case, tmp_path, later, backend)
    assert r.status == "error" and r.data["blocked"] and len(calls) == 1


def test_write_timeout_is_uncertain_and_not_retried(tmp_path):
    case, later = practice("022")
    calls = []

    def slow(spec, params, case, events):
        calls.append(1)
        raise TimeoutError("card system")
    p = tc("card_service.block", card="debit")
    r = run(p, case, tmp_path, later, slow)
    assert r.status == "uncertain" and r.data["read_back"] == "card_service" and calls == [1]
    assert run(p, case, tmp_path, later, slow).status == "uncertain" and calls == [1]


def test_read_retries_once_then_times_out(tmp_path):
    case, later = practice("048")
    calls = []

    def slow(spec, params, case, events):
        calls.append(1)
        raise TimeoutError
    assert run(tc("transfer_journal"), case, tmp_path, later, slow).status == "timeout" and len(calls) == 2


def test_unknown_tool_and_non_tool_call_are_errors(tmp_path):
    case, later = practice("048")
    assert execute(tc("teleport"), case, tmp_path, later).status == "error"
    assert execute(Proposal(action="reply"), case, tmp_path, later).status == "error"


def test_change_asked_of_a_read_tool_is_refused(tmp_path):
    case, later = practice("006")
    r = execute(tc("transfer_journal", action="cancel", reference="T2"), case, tmp_path, later)
    assert r.status == "error" and "transfer_journal.return_request" in r.data["write_tools"]
    assert execute(tc("transfer_journal", action="lookup"), case, tmp_path, later).status != "error"
