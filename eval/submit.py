"""Run numbered Reality Test cases concurrently and report their answers."""

import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


CASE_TIMEOUT = 150


def run_case(case: Path, out: Path):
    start = time.monotonic()
    result = subprocess.run(
        ["uv", "run", "agent", "run", "--case", str(case), "--out", str(out)],
        capture_output=True, text=True, timeout=CASE_TIMEOUT,
    )
    return case.name, result.returncode, time.monotonic() - start


def decision(answer: Path) -> str:
    lines = answer.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Decision":
            return next((value.strip() for value in lines[index + 1:] if value.strip()), "missing")
    return "missing"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases_dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("ANSWERS"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    if not args.cases_dir.is_dir():
        parser.error(f"not a directory: {args.cases_dir}")
    if args.workers < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--workers and --limit must be positive")

    cases = sorted((p for p in args.cases_dir.iterdir() if p.is_dir() and p.name.isdecimal()),
                   key=lambda p: (int(p.name), p.name))
    if args.limit is not None:
        cases = cases[:args.limit]
    args.out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda case: run_case(case, args.out / case.name), cases))

    print("case\texit code\tseconds\tdecision\tfallback")
    missing = 0
    for name, code, seconds in results:
        answer = args.out / name / "ANSWER.md"
        reasoning = args.out / name / "REASONING.md"
        if not answer.is_file() or not reasoning.is_file():
            missing += 1
        print(f"{name}\t{code}\t{seconds:.1f}\t{decision(answer) if answer.is_file() else 'missing'}\tn")
    print(f"total {len(cases)}; missing {missing}")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    print(f"HEAD {head.stdout.strip()}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
