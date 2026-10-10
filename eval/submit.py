"""Run numbered Reality Test cases concurrently and report their answers."""

import argparse
import os
import signal
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent.core.writer import write_fallback


CASE_TIMEOUT = 150


def run_case(case: Path, out: Path):
    start = time.monotonic()
    try:
        process = subprocess.Popen(
            ["uv", "run", "agent", "run", "--case", str(case), "--out", str(out)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            _, stderr = process.communicate(timeout=CASE_TIMEOUT)
            code, error = process.returncode, stderr.strip()
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            code, error = 124, str(exc)
    except OSError as exc:
        code, error = 127, str(exc)
    return case, code, time.monotonic() - start, error


def fill_missing(case: Path, out: Path, error: str) -> bool:
    """Write a system fallback without changing an answer the agent already wrote."""
    if (out / "ANSWER.md").is_file() and (out / "REASONING.md").is_file():
        return False
    with tempfile.TemporaryDirectory(dir=out.parent) as temporary:
        fallback = Path(temporary)
        write_fallback(fallback, case, error or "agent exited without both output files", [])
        out.mkdir(parents=True, exist_ok=True)
        for name in ("ANSWER.md", "REASONING.md", "trace.log", "run.json"):
            if not (out / name).exists():
                os.replace(fallback / name, out / name)
    return True


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
    missing = fallback_count = 0
    for case, code, seconds, error in results:
        name = case.name
        folder = args.out / name
        try:
            fallback = fill_missing(case, folder, error)
        except Exception as exc:
            fallback = False
            print(f"{name}: fallback failed: {exc}")
        fallback_count += fallback
        answer = folder / "ANSWER.md"
        reasoning = folder / "REASONING.md"
        if not answer.is_file() or not reasoning.is_file():
            missing += 1
        print(f"{name}\t{code}\t{seconds:.1f}\t{decision(answer) if answer.is_file() else 'missing'}\t{'y' if fallback else 'n'}")
    print(f"total {len(cases)}; fallback {fallback_count}; missing {missing}")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    print(f"HEAD {head.stdout.strip()}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
