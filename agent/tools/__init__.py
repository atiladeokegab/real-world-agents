"""§4.3 tool catalogue and mock environment, §4.7 executor."""

from agent.tools.catalogue import CATALOGUE, SERVICES
from agent.tools.executor import run


def execute(proposal, case, ledger_dir, practice_events=[]):
    """Run one approved tool call (§4.7). Never raises; failures come back as a ToolResult status."""
    return run(proposal, case, ledger_dir, list(practice_events))


__all__ = ["CATALOGUE", "SERVICES", "execute"]
