from agent.llm.contracts import Authority, Case, Event, Finding


def case_006(question=None):
    return Case(
        track="Banking & Financial Services",
        case_id="006",
        title="Two Similar Transfers",
        source_role="Bank customer",
        created="2025-07-29T09:00:00Z",
        initial_request="Mira wants to know whether two similar outgoing transfer entries are one instruction or two.",
        events=[
            Event(id="event-001", at="2025-07-29T09:00:00Z", channel="Secure portal", sender="Mira", recipient="H&V",
                  body="I see two payments of £84.20 to Northgrid Energy today. I only meant to send one. Can you stop the second?"),
            Event(id="event-002", at="2025-07-29T09:20:00Z", channel="Secure portal", sender="Mira", recipient="H&V",
                  body="This is really annoying, please sort it."),
        ],
        authority=Authority(identity="authenticated"),
        raw_files={"index.md": "## Outcome\nSECRET OUTCOME"},
        question=question,
    )


FINDING_DUP = Finding(id="finding-1", kind="anomaly", check="duplicates",
                      detail="two transfers, same payee and amount, same day", events=["event-001"])
