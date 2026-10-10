import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import pytest

KEYS = ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_EXTRACTION", "ANTHROPIC_API_KEY_DECISION")


@pytest.fixture(autouse=True)
def placeholder_key(monkeypatch):
    """eval.submit refuses to start without a key (#143). These tests fake every case, so a
    placeholder satisfies the check and no request is ever made."""
    if not any(__import__("os").environ.get(k) for k in KEYS):
        monkeypatch.setenv("ANTHROPIC_API_KEY_EXTRACTION", "test-placeholder")
        monkeypatch.setenv("ANTHROPIC_API_KEY_DECISION", "test-placeholder")
