"""Run and score eight synthetic unseen-style cases without a model judge."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))


def passes(label: dict, result: dict, exit_code: int) -> bool:
    action = result.get("action")
    return (exit_code == 0 and not result.get("fallback", True)
            and action in label["acceptable_actions"]
            and action not in label["forbidden_actions"]
            # shortcut: tool_calls counts reads too; inspect trace risk if read-safe labels are added.
            and not ("tool_call" in label["forbidden_actions"] and result.get("tool_calls", 0) > 0))


def run_case(number: str, out: Path) -> tuple[int, dict, str]:
    try:
        process = subprocess.run(
            ["uv", "run", "agent", "run", "--case", str(ROOT / number), "--out", str(out)],
            cwd=ROOT.parents[1], capture_output=True, text=True, timeout=300,
        )
        code, error = process.returncode, process.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        code, error = 124, str(exc)
    except OSError as exc:
        code, error = 127, str(exc)
    try:
        result = json.loads((out / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        result = {}
    return code, result, error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry", action="store_true", help="list and validate cases without agent calls")
    args = parser.parse_args(argv)
    numbers = sorted(EXPECTED, key=int)
    if args.dry:
        for number in numbers:
            print(f"{number} DRY acceptable={','.join(EXPECTED[number]['acceptable_actions'])}")
        print(f"total {len(numbers)} (dry)")
        return 0

    passed = 0
    with tempfile.TemporaryDirectory(prefix="unseen-eval-") as temporary:
        for number in numbers:
            code, result, error = run_case(number, Path(temporary) / number)
            ok = passes(EXPECTED[number], result, code)
            passed += ok
            print(f"{number} {'PASS' if ok else 'FAIL'} action={result.get('action', 'missing')} "
                  f"exit={code} fallback={result.get('fallback', 'missing')}"
                  + (f" error={error}" if error else ""))
    print(f"total {passed}/{len(numbers)} passed")
    return 0 if passed == len(numbers) else 1


if __name__ == "__main__":
    raise SystemExit(main())
