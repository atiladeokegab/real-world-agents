"""Reality Test intake: turn whatever the organisers hand over into a folder of case folders.

normalise_input(path) -> cases_dir, auto-detecting:
1. a folder of case folders: used as it is (copied only if shared top-level files must be added);
2. a .zip / .tar / .tar.gz / .tgz: extracted to a temp dir, then detected again (one wrapping folder is skipped);
3. a folder of loose files: one case per file (named from the digits in its file name);
4. a single file holding many cases: split on "# Case 12" / "Case 12:" headings or "---", a JSON list or
   dict of cases, or one CSV row per case; if it can't be split, the whole file is one case;
5. shared top-level files (tool definitions, data) next to the cases: copied into every case's attachments/.

It never drops content and never raises: anything it can't read becomes one case per file. Every
generated case keeps its source verbatim in attachments/, and its text in index.md's "Initial request",
which is where ingest puts it in front of the model. Output is always a fresh temp dir, never the repo.
"""

import csv
import io
import json
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

ARCHIVES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")
BINARY = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".xlsx", ".xls", ".docx"}
TOOL_KEYS = ("tools", "tool_results", "records", "journal", "journals", "data")
CASE_HEADING = re.compile(r"^(?:#{1,3}\s*)?Case\s*#?\s*(\d+)\b[^\n]*$", re.I | re.M)
RULE = re.compile(r"^\s*-{3,}\s*$", re.M)
LIST_KEYS = ("cases", "items", "data", "records")


def _is_archive(p: Path) -> bool:
    return p.is_file() and p.name.lower().endswith(ARCHIVES)


def _visible(p: Path) -> list[Path]:
    return sorted(c for c in p.iterdir() if not c.name.startswith((".", "_", "__MACOSX")))


def _digits(name: str) -> str | None:
    m = re.search(r"\d+", name)
    return str(int(m.group())) if m else None


def _text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _extract(archive: Path, dest: Path) -> Path:
    if archive.name.lower().endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            for m in z.infolist():  # never write outside dest
                target = (dest / m.filename).resolve()
                if dest.resolve() in target.parents or target == dest.resolve():
                    z.extract(m, dest)
    else:
        with tarfile.open(archive) as t:
            t.extractall(dest, filter="data")
    return dest


def _unwrap(p: Path) -> Path:
    """Skip wrapping folders: one folder and nothing else, which is not itself a case."""
    while True:
        kids = _visible(p)
        if len(kids) == 1 and kids[0].is_dir() and _visible(kids[0]) \
                and not any((kids[0] / n).exists() for n in ("index.md", "history.md", "question.md")):
            p = kids[0]
        else:
            return p


def _write_case(out: Path, number: str, title: str, text: str, source_name: str, source: bytes | None) -> Path:
    case = out / number
    case.mkdir(parents=True, exist_ok=True)
    if re.search(r"^##\s+(Initial request|Case details)\b", text, re.M):
        index = text  # already in the practice format: keep it as it is
    else:
        index = f"# Case {number}: {title}\n\n## Initial request\n\n{text.strip() or f'See the attached file {source_name}.'}\n"
    (case / "index.md").write_text(index, encoding="utf-8")
    (case / "attachments").mkdir(exist_ok=True)
    if source is not None:  # the original, untouched, for the model and the judges
        (case / "attachments" / source_name).write_bytes(source)
    return case


def _numbered(chunks: list[tuple[str | None, object]]) -> list[tuple[str, object]]:
    """Use the cases' own numbers when they are all present and distinct, else 1..n."""
    nums = [n for n, _ in chunks]
    if all(nums) and len(set(nums)) == len(nums):
        return [(n, c) for n, c in chunks]
    return [(str(i), c) for i, (_, c) in enumerate(chunks, 1)]


def _split_text(text: str) -> list[tuple[str | None, str]]:
    heads = list(CASE_HEADING.finditer(text))
    if len(heads) >= 2:
        preamble = text[:heads[0].start()].strip()
        parts = [(m.group(1), text[m.start():(heads[i + 1].start() if i + 1 < len(heads) else len(text))])
                 for i, m in enumerate(heads)]
        # a preamble before the first case is shared context: keep it on every case
        return [(n, f"{preamble}\n\n{body}" if preamble else body) for n, body in parts]
    pieces = [p.strip() for p in RULE.split(text) if p.strip()]
    if len(pieces) >= 2:
        return [(None, p) for p in pieces]
    return [(None, text)]


def _item_text(item) -> tuple[str, dict]:
    """A JSON case: its text for index.md, and any tool/record content to attach as tools.json."""
    if isinstance(item, str):
        return item, {}
    if not isinstance(item, dict):
        return json.dumps(item, indent=2, ensure_ascii=False), {}
    tools = {k: v for k, v in item.items() if k.lower() in TOOL_KEYS}
    rest = {k: v for k, v in item.items() if k not in tools}
    lines = [f"{k}: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}" for k, v in rest.items()]
    return "\n".join(lines), tools


def _json_items(data) -> list[tuple[str | None, object]]:
    if isinstance(data, list):
        return [(_digits(str(i.get("id") or i.get("case") or i.get("case_id") or "")) if isinstance(i, dict) else None, i)
                for i in data]
    if isinstance(data, dict):
        for key in LIST_KEYS:
            if isinstance(data.get(key), list) and data[key]:
                return _json_items(data[key])
        if data and all(_digits(str(k)) for k in data) and all(isinstance(v, (dict, str)) for v in data.values()):
            return [(_digits(str(k)), v) for k, v in data.items()]
    return [(None, data)]


def _split_file(f: Path) -> list[tuple[str | None, str, dict]]:
    """(number, text, tools) per case found in one file."""
    suffix = f.suffix.lower()
    if suffix in BINARY:
        return [(_digits(f.stem), "", {})]
    raw = _text(f)
    if suffix == ".json":
        try:
            return [(n, *_item_text(item)) for n, item in _json_items(json.loads(raw))]
        except ValueError:
            pass
    if suffix == ".csv":
        rows = list(csv.DictReader(io.StringIO(raw)))
        if rows:
            out = []
            for row in rows:
                ident = next((row[k] for k in row if k and re.fullmatch(r"(case)?_?(id|no|number)|case", k.strip(), re.I)), "")
                out.append((_digits(ident or ""), "\n".join(f"{k}: {v}" for k, v in row.items()), {}))
            return out
    return [(n, t, {}) for n, t in _split_text(raw)]


def _whole_file_case(f: Path, out: Path, number: str) -> Path:
    """One file is one case: its text in index.md, the original attached."""
    text = "" if f.suffix.lower() in BINARY else _text(f)
    return _write_case(out, number, f"from {f.name}", text, f.name, f.read_bytes())


def _split_into_cases(f: Path, out: Path) -> list[Path]:
    """One file holding one or many cases (shape 4)."""
    found = _split_file(f)
    if len(found) == 1:
        return [_whole_file_case(f, out, found[0][0] or _digits(f.stem) or "1")]
    cases = []
    for number, (text, tools) in _numbered([(n, (t, tl)) for n, t, tl in found]):
        case = _write_case(out, number, f"from {f.name}", text, f"{f.stem}-case-{number}.txt", text.encode())
        if tools:
            (case / "attachments" / "tools.json").write_text(json.dumps(tools, indent=2, ensure_ascii=False))
        cases.append(case)
    return cases


DATA_WORDS = re.compile(r"tool|api|record|journal|data|schema", re.I)
DOC_NAMES = re.compile(r"^(readme|licen[cs]e|index|changelog|contributing|notice|authors)\b", re.I)
DOC_WORDS = re.compile(r"doc|guide|about|instruction|overview|notes|description|rules", re.I)


def _is_doc(f: Path) -> bool:
    """Dataset documentation (README, LICENSE, a guide): never shared into cases as evidence.
    The practice README even describes outcomes. Data and tool files are always shared."""
    if DATA_WORDS.search(f.name):
        return False
    return bool(DOC_NAMES.match(f.name)) or (f.suffix.lower() in (".md", ".rst", ".html", ".htm")
                                            and bool(DOC_WORDS.search(f.stem)))


def _shareable(files: list[Path]) -> list[Path]:
    docs = [f.name for f in files if _is_doc(f)]
    if docs:
        print(f"intake: not shared into cases (dataset documentation): {', '.join(docs)}")
    return [f for f in files if not _is_doc(f)]


CASE_FILES = {"index.md", "history.md", "question.md"}


def _stray(case: Path) -> list[Path]:
    """Files ingest would not show the model as text: extra top-level files (only via a fallback call)
    and files in subfolders of attachments/ (skipped)."""
    top = [f for f in case.iterdir() if f.is_file() and f.name not in CASE_FILES and not f.name.startswith(".")]
    att = case / "attachments"
    nested = [f for f in att.rglob("*") if f.is_file() and f.parent != att] if att.is_dir() else []
    return top + nested


def _needs_fixing(case: Path) -> bool:
    return bool(_stray(case))


def _surface_files(case: Path) -> int:
    """Copy (never move) stray files into attachments/, so their content reaches the model as text."""
    att = case / "attachments"
    att.mkdir(exist_ok=True)
    stray = _stray(case)
    for f in stray:
        name = f.name if f.parent == case else "_".join(f.relative_to(att).parts)
        target = att / name
        if target.exists():
            target = att / f"{f.parent.name}_{name}"
        shutil.copy2(f, target)
    return len(stray)


def _add_shared(cases: list[Path], shared: list[Path]) -> None:
    for case in cases:
        (case / "attachments").mkdir(exist_ok=True)
        for s in shared:
            # ingest reads only files directly in attachments/, so a shared folder is flattened into it
            for f in ([s] if s.is_file() else sorted(p for p in s.rglob("*") if p.is_file())):
                name = f.name if f == s else "_".join(f.relative_to(s.parent).parts)
                shutil.copy2(f, case / "attachments" / name)


def _from_dir(src: Path, out: Path) -> tuple[str, list[Path]]:
    kids = _visible(src)
    folders = [k for k in kids if k.is_dir() and any(f.is_file() for f in k.rglob("*"))]
    files = [k for k in kids if k.is_file()]
    if folders:  # shape 1, with any loose top-level data/tool files shared into every case
        shared = _shareable(files)
        if not shared and not any(_needs_fixing(k) for k in folders):
            return "folder of case folders", folders
        cases = [Path(shutil.copytree(k, out / k.name)) for k in folders]
        fixed = sum(_surface_files(c) for c in cases)
        _add_shared(cases, shared)
        return ("folder of case folders" + (f" + {len(shared)} shared file(s)" if shared else "")
                + (f", {fixed} file(s) copied into attachments/" if fixed else "")), cases
    archives = [f for f in files if _is_archive(f)]
    if archives:
        inner = Path(tempfile.mkdtemp(prefix="intake-x-"))
        for a in archives:
            _extract(a, inner / a.name.split(".")[0])
        rest = [f for f in files if f not in archives]
        for f in rest:
            shutil.copy2(f, inner / f.name)
        return _from_dir(_unwrap(inner), out)
    if len(files) == 1:  # shape 4
        return "one file", _split_into_cases(files[0], out)
    numbered = [f for f in files if _digits(f.stem)]
    shared = _shareable([f for f in files if not _digits(f.stem)]) if numbered else []
    per_case = numbered or [f for f in files if not _is_doc(f)] or files  # shape 3; a README is not a case
    cases = [_whole_file_case(f, out, n) for n, f in _numbered([(_digits(f.stem), f) for f in per_case])]
    _add_shared(cases, shared)
    return f"folder of {len(per_case)} loose file(s)" + (f" + {len(shared)} shared" if shared else ""), cases


def _fallback(src: Path, out: Path) -> tuple[str, list[Path]]:
    """Last resort: one case per readable file, content verbatim."""
    files = [src] if src.is_file() else [f for f in sorted(src.rglob("*")) if f.is_file()]
    cases = []
    for i, f in enumerate(files, 1):
        try:
            text = "" if f.suffix.lower() in BINARY else _text(f)
            cases.append(_write_case(out, str(i), f"from {f.name}", text, f.name, f.read_bytes()))
        except OSError:
            continue
    return "fallback: one case per file", cases


def normalise_input(path) -> Path:
    """The folder of case folders eval.submit runs. Prints what it found; never raises on content."""
    src = Path(path)
    if not src.exists():
        print(f"intake: {src} does not exist")
        return src
    # Cases sit under a folder named like the input: ingest takes the case's track from its parent's name.
    base = Path(tempfile.mkdtemp(prefix="intake-"))
    out = base / (re.sub(r"(\.tar)?\.[^.]+$", "", src.name) or "cases")
    try:
        if _is_archive(src):
            inner = _unwrap(_extract(src, Path(tempfile.mkdtemp(prefix="intake-x-"))))
            out = base / inner.name if inner.name and not inner.name.startswith("intake-x-") else out
            shape, cases = _from_dir(inner, out)
            shape = f"archive {src.name} → {shape}"
        elif src.is_file():
            shape, cases = "one file", _split_into_cases(src, out)
        else:
            inner = _unwrap(src)
            out = base / inner.name
            shape, cases = _from_dir(inner, out)
    except Exception as exc:  # never fail: one case per file
        print(f"intake: could not read {src} as cases ({type(exc).__name__}: {exc}); one case per file")
        shutil.rmtree(base, ignore_errors=True)
        out.mkdir(parents=True)
        shape, cases = _fallback(src, out)
    out.mkdir(parents=True, exist_ok=True)
    root = cases[0].parent if cases else out  # shape 1 unchanged: the given (or extracted) folder itself
    print(f"intake: {shape}; {len(cases)} case(s) in {root}")
    return root
