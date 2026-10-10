"""Customer-facing and handover wording.

Draft wording from AGENT_SPEC §4.5/§4.8 until docs/design.md §Copy is filled in (#10).
"""

HOLDING_REPLY = (
    "Thank you for your message. I've passed your request to {team}, who will review it "
    "and reply to you here. We haven't made any changes to your account while this is reviewed."
)

REQUEST_INFO_REPLY = "To make sure we act on the right request, please confirm {question}."

DEFAULT_TEAM = "the operations team"

HANDOVER_HEADING = "## Handover note"
HANDOVER_LABELS = {
    "who": "Take it",
    "urgency": "Urgency",
    "type": "Type",
    "why": "Why it was handed over",
    "verified": "Verified",
    "claimed": "Only claimed",
    "conflicts": "Conflicts",
    "did": "What the agent did",
    "not_done": "What the agent did not do",
    "question": "Question for you",
    "holding_reply": "Holding reply (safe to send now)",
}
NONE = "none"
