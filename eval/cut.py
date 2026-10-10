"""Decision-point cut: how many events the agent may see."""
import re
from pathlib import Path

EVENT = re.compile(r'<a id="event-\d+"></a>(.*?)(?=<a id="event-|\Z)', re.S)


def cut_index(history: Path) -> int:
    """Events before the service agent's first internal note; that note is the agent's own first act."""
    events = EVENT.findall(Path(history).read_text())
    for i, e in enumerate(events):
        ch = re.search(r"\*\*Channel:\*\* (.*)", e).group(1)
        fr = re.search(r"\*\*From:\*\* (.*)", e).group(1)
        if ch == "Internal note" and "agent" in fr.lower():
            return i
    # ponytail: no internal note (cases 027, 028, 045): hide the last two events (act + confirmation)
    return max(1, len(events) - 2)
