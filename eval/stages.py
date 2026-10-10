"""First wrong stage per failed case (AGENT_SPEC 4.10.5): the step where a failure shows is often not where it started."""


def first_failing_stage(row: dict, want_visible: int) -> str:
    """Stages in order: cut, findings, extraction, decision. Verifier and writer join when the full loop is scored."""
    if row.get("error"):
        return row["stage"] or "setup"  # the stage that was running when it raised
    if row.get("visible") not in (None, want_visible):
        return "cut"
    if row.get("expect") and row["expect"] not in row.get("checks", []):
        return "findings"
    return "decision"
