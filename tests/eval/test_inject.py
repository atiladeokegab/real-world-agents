from dataclasses import dataclass, replace
from datetime import datetime

from eval.inject import contradict, detected, drop_identity, hidden_instruction, shift_amount


class Copy:  # stand-in for pydantic's model_copy; core's models aren't merged yet
    def model_copy(self, update):
        return replace(self, **update)


@dataclass
class Auth(Copy):
    identity: str
    role: str | None = None


@dataclass
class Ev(Copy):
    id: str
    sender: str
    body: str
    at: datetime = datetime(2025, 1, 1)


@dataclass
class Case(Copy):
    events: list
    authority: Auth


C = Case(events=[Ev(id="event-001", sender="Mara", body="Pay £100.00 now")], authority=Auth(identity="verified"))


def test_shift_amount_changes_20_to_60_percent():
    c, expect = shift_amount(C)
    v = float(c.events[0].body.split("£")[1].split()[0].replace(",", ""))
    assert expect == "amounts" and 0.19 < abs(v - 100) / 100 < 0.61
    assert C.events[0].body == "Pay £100.00 now"  # original untouched


def test_other_variants():
    assert len(contradict(C)[0].events) == 2
    assert drop_identity(C)[0].authority.identity == "unverified"
    assert "SYSTEM:" in hidden_instruction(C)[0].events[0].body


def test_detected():
    assert detected(None, [], "escalate") and not detected(None, [], "tool_call")
