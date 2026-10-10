"""Customer-facing and handover wording.

Exact words from docs/design.md §Copy, which is binding.
"""

HOLDING_REPLY = (
    "Thank you for your message. We've passed your request to {team}, who will review it "
    "and reply to you here. We haven't made any changes to your account while this is reviewed."
)

REQUEST_INFO_REPLY = "To make sure we act on the right request, please confirm: {question}"

PENDING_REPLY = "We've asked {team} to {check}. We'll reply here once they've confirmed."

DEFAULT_TEAM = "the operations team"

HANDOVER_HEADING = "## Handover"
HANDOVER_LABELS = {
    "who": "Take it",
    "urgency": "Urgency",
    "type": "Type",
    "why": "Why it was handed over",
    "verified": "Verified",
    "claimed": "Only claimed",
    "conflicts": "Conflicts",
    "did": "We did",
    "not_done": "We did not",
    "question": "Question for you",
    "holding_reply": "Safe to send now",
}
NONE = "none"
