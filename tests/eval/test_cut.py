import json
from pathlib import Path

from eval.cut import cut_index

EX = Path(__file__).parents[2] / "examples"


def test_cut_points():
    assert cut_index(EX / "001/history.md") == 2  # events 1-2 visible, agent's note hidden
    assert cut_index(EX / "013/history.md") == 3
    assert cut_index(EX / "027/history.md") == 3  # no internal note: hide last two of five


def test_gold_covers_all_cases():
    g = json.loads((EX.parent / "eval/gold.json").read_text())
    assert sorted(g) == sorted(p.name for p in EX.glob("0*"))
