"""§4.11 runner: `agent run` for one case, `agent collect` to check a whole answers folder."""

import json
from pathlib import Path

import typer

from agent.core.loop import run_case

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def run(case: Path = typer.Option(..., help="Case folder, e.g. examples/044"),
        question: str = typer.Option(None, help="Question the answer must address directly"),
        out: Path = typer.Option(None, help="Answer folder [default: ANSWERS/<case folder name>]"),
        cut: int = typer.Option(None, help="Practice runs: keep only the first N events")):
    """Run one case. Always writes an answer, the crash fallback included; exit 0."""
    typer.echo(run_case(case, out, question, cut))


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
        typer.echo(f"{d.name}  {r.get('action')}  {r.get('outcome')}  tools={r.get('tool_calls')}"
                   + ("  FALLBACK" if r.get("fallback") else ""))
    raise typer.Exit(1 if missing else 0)
