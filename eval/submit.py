"""Run numbered Reality Test cases concurrently and report their answers."""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent.core.writer import STATES, write_fallback


CASE_TIMEOUT = 300


HEADING = re.compile(r"^#{1,6}\s*(questions?|decision points?|your task|what should\b.*?)\s*:?\s*$", re.I)


def find_question(case: Path) -> str | None:
    """A supplied question: a question/decision/task file, else a heading section in index.md (RULES.md section C gives no format)."""
    files = sorted(f for f in case.iterdir() if f.is_file() and f.suffix.lower() in {".md", ".txt"}
                   and f.name.lower() not in {"index.md", "history.md"}
                   and re.search(r"question|decision|task", f.name, re.I))
    found = [t for t in (f.read_text(encoding="utf-8", errors="replace").strip() for f in files) if t]
    if not found and (case / "index.md").is_file():
        body = None
        for line in (case / "index.md").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#"):
                if body:
                    found.append("\n".join(body).strip())
                body = [] if HEADING.match(line.strip()) else None
            elif body is not None:
                body.append(line)
        if body:
            found.append("\n".join(body).strip())
        found = [t for t in found if t]
    if not found:
        return None
    return found[0] if len(found) == 1 else "\n".join(f"{i}. {t}" for i, t in enumerate(found, 1))


def safe_question(case: Path) -> str | None:
    """Any failure reading a question means no question: it must never stop the run."""
    try:
        return find_question(case)
    except Exception as exc:
        print(f"WARNING: case {case.name}: could not read a question ({exc}); running without one", file=sys.stderr, flush=True)
        return None


def run_case(case: Path, out: Path):
    if (out / "ANSWER.md").exists() or (out / "REASONING.md").exists():
        return case, "skipped", 0.0, "existing output preserved; subprocess not rerun"
    start = time.monotonic()
    question = safe_question(case)
    try:
        process = subprocess.Popen(
            ["uv", "run", "agent", "run", "--case", str(case), "--out", str(out)]
            + (["--question", question] if question else []),
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
    lines = answer.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Decision":
            return next((value.strip() for value in lines[index + 1:] if value.strip()), "missing")
    return "missing"


def write_index(out: Path, head: str | None, seconds: dict[str, float] | None = None) -> None:
    """<out>/README.md: one row per case for the judges. Reads only what the run wrote; writes only this file."""
    folders = sorted((p for p in out.iterdir() if p.is_dir() and p.name.isdecimal()), key=lambda p: int(p.name))
    totals = dict.fromkeys([badge for badge, _, _ in STATES.values()] + ["unknown"], 0)
    lines = ["# Reality Test answers", "",
             "One row per case. Open a case for its full answer, reasoning and trace.", "",
             "| Case | State | Decision | Escalated | Fallback | Question | Seconds |",
             "| --- | --- | --- | --- | --- | --- | ---: |"]
    for folder in folders:
        try:
            result = json.loads((folder / "run.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = {}
        if not isinstance(result, dict):
            result = {}
        state = STATES[result["state"]][0] if result.get("state") in STATES else "unknown"
        totals[state] += 1
        answer = folder / "ANSWER.md"
        try:
            answer_text = answer.read_text(encoding="utf-8", errors="replace")
        except OSError:
            answer_text = ""
        line = decision(answer) if answer_text else "missing"
        if line == "missing":
            line = result.get("summary") or "unknown"
        line = line.split(" — ", 1)[1] if line.startswith(f"{state} — ") else line  # the badge has its own column
        line = " ".join(str(line).split()).replace("|", "\\|")
        flags = ["unknown" if key not in result else ("y" if result[key] else "n") for key in ("escalated", "fallback")]
        question = "y" if "## Answer to the question" in answer_text else ("n" if answer_text else "unknown")
        secs = (seconds or {}).get(folder.name, result.get("seconds"))
        secs = f"{secs:.1f}" if isinstance(secs, (int, float)) else "unknown"
        lines.append(f"| [{folder.name}]({folder.name}/ANSWER.md) | {state} | {line} | "
                     f"{flags[0]} | {flags[1]} | {question} | {secs} |")
    lines += ["", f"**Totals:** {len(folders)} cases · "
              + " · ".join(f"{name} {count}" for name, count in totals.items() if count or name != "unknown")]
    if head:
        lines += ["", f"**Commit:** `{head}`"]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    cases = sorted((p for p in args.cases_dir.iterdir()
                    if p.is_dir() and ((p / "index.md").is_file() or (p / "history.md").is_file())),
                   key=lambda p: (0, int(p.name), p.name) if p.name.isdecimal() else (1, p.name))
    if not cases:
        print(f"ERROR: no case folders found in {args.cases_dir}", file=sys.stderr)
        return 1
    numbers = {}
    used = set()
    for case in cases:
        match = re.search(r"[0-9]+", case.name)
        if match:
            number = str(int(match.group()))
            if number in used:
                print(f"ERROR: duplicate case number {number} in {args.cases_dir}", file=sys.stderr)
                return 1
            numbers[case] = number
            used.add(number)
    next_number = 1
    for case in cases:
        if case not in numbers:
            while str(next_number) in used:
                next_number += 1
            numbers[case] = str(next_number)
            used.add(numbers[case])
    if args.limit is not None:
        cases = cases[:args.limit]
    for case in cases:
        print(f"{case.name} -> {numbers[case]}", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda case: run_case(case, args.out / numbers[case]), cases))

    print("case\texit code\tseconds\tdecision\tfallback\tquestion")
    missing = fallback_count = 0
    for case, code, seconds, error in results:
        name = numbers[case]
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
        print(f"{name}\t{code}\t{seconds:.1f}\t{decision(answer) if answer.is_file() else 'missing'}\t{'y' if fallback else 'n'}\t{'y' if safe_question(case) else 'n'}")
    print(f"total {len(cases)}; fallback {fallback_count}; missing {missing}")
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = ""
    if head:
        print(f"HEAD {head}")
    write_index(args.out, head, {numbers[case]: secs for case, _, secs, _ in results})
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
