"""§4.11 runner: `agent run` for one case, `agent collect` to check a whole answers folder."""

import json
import time
from pathlib import Path

import typer

from agent.core.loop import run_case
from agent.core.writer import STATES

REJECTED, FAILURE = (229, 83, 61), (176, 58, 140)  # docs/design.md: red for a rejection, magenta for a failure


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    return tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))


def _stage(stage: str, text: str) -> None:
    """§Copy: lower-case stage label padded to 10, colour only for rejections and failures."""
    fg = (REJECTED if stage == "verify" else FAILURE) if text.startswith("✗") else None
    typer.secho(f"{stage:<10}{text}", fg=fg)


app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def run(case: Path = typer.Option(..., help="Case folder, e.g. examples/044"),
        question: str = typer.Option(None, help="Question the answer must address directly"),
        out: Path = typer.Option(None, help="Answer folder [default: ANSWERS/<case folder name>]"),
        cut: int = typer.Option(None, help="Practice runs: keep only the first N events")):
    """Run one case: one line per stage, then the outcome line. Always writes an answer; exit 0."""
    start = time.monotonic()
    folder = run_case(case, out, question, cut, on_stage=_stage)
    r = json.loads((folder / "run.json").read_text())
    badge, glyph, colour = STATES[r["state"]]
    typer.secho(f"{glyph} {badge}  {r['summary']} · {time.monotonic() - start:.1f}s", fg=_rgb(colour), bold=True)


@app.command()
def collect(out: Path = typer.Option(Path("ANSWERS"), help="Folder holding one answer folder per case")):
    """One line per case from its run.json; exit 1 if any case has no ANSWER.md."""
    missing = 0
    for d in sorted(p for p in out.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if not (d / "ANSWER.md").is_file():
            missing += 1
            typer.echo(f"{d.name}  MISSING ANSWER.md")
            continue
        r = json.loads((d / "run.json").read_text()) if (d / "run.json").is_file() else {}
        badge, glyph, _ = STATES.get(r.get("state"), ("?", " ", ""))
        typer.echo(f"{d.name}  {glyph} {badge}  {r.get('summary', r.get('action'))}"
                   + ("  FALLBACK" if r.get("fallback") else ""))
    raise typer.Exit(1 if missing else 0)
