import pytest

from agent.tools import CATALOGUE
from agent.tools.mock import call, is_bank_system
from tests.tools.conftest import EXAMPLES, practice


def test_048_transfer_journal_answers_from_event_004():
    case, later = practice("048")
    assert [e.id for e in case.events] == ["event-001", "event-002"]
    r = call(CATALOGUE["transfer_journal"], {}, case, later)
    assert r.status == "ok" and r.source_event == "event-004"
    assert "No identifiable incoming credit" in r.data["note"]


@pytest.mark.parametrize("num,tool,event", [
    ("001", "transfer_journal", "event-004"), ("011", "standing_order_journal", "event-004"),
    ("014", "mandate_journal", "event-004"), ("024", "card_service", "event-004"),
    ("047", "business_service", "event-004"), ("032", "statements_service", "event-003"),
])
def test_matching_service_reads_the_journal_note(num, tool, event):
    case, later = practice(num)
    r = call(CATALOGUE[tool], {}, case, later)
    assert (r.status, r.source_event) == ("ok", event)


def test_044_row_status_comes_from_the_bank_portal():
    case, later = practice("044")
    r = call(CATALOGUE["business_service"], {}, case, later)
    assert r.status == "ok" and r.source_event == "event-004" and "Rejected" in r.data["note"]


def test_journal_note_beats_an_earlier_portal_message():
    case, later = practice("048")
    portal = later[0].model_copy(update={"id": "event-x", "channel": "Secure portal", "sender": "H&V payment team"})
    r = call(CATALOGUE["transfer_journal"], {}, case, [portal, *later])
    assert r.source_event == "event-004"


@pytest.mark.parametrize("sender,channel", [
    ("H&V service agent", "Secure portal"), ("H&V Business Support", "Business portal"), ("H&V", "Secure portal"),
    ("Elm Quay Property Services", "External message"), ("Leona Voss", "Secure chat"),
])
def test_people_and_customers_are_not_bank_systems(sender, channel):
    assert not is_bank_system({"sender": sender, "channel": channel})


def test_wrong_service_is_not_found():
    case, later = practice("048")
    r = call(CATALOGUE["card_service"], {}, case, later)
    assert r.status == "not_found" and r.source_event is None and "note" not in r.data


def test_unseen_case_is_pending_for_every_tool():
    case, _ = practice("048")
    for spec in CATALOGUE.values():
        r = call(spec, {}, case, [])
        assert r.status == "pending" and r.source_event is None and "note" not in r.data


def test_agent_notes_and_customer_text_never_returned():
    nums = sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir())
    for num in nums:
        case, later = practice(num)
        by_id = {e.id: e for e in later}
        for spec in CATALOGUE.values():
            r = call(spec, {}, case, later)
            if r.source_event:
                e = by_id[r.source_event]
                assert is_bank_system(e) and "agent" not in e.sender.lower()
                assert e.sender.startswith(("H&V", "Harrow & Vale")) or e.channel == "Internal note"
