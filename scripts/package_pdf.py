#!/usr/bin/env python3
"""
package_pdf.py — Convert draft_clean.md to draft.pdf using the makePdf layout.

Requires: pandoc, latexmk, and a LaTeX engine (pdflatex or xelatex).
Zero Python dependencies beyond the stdlib.

Before pandoc, markdown is normalized so that:
  - end_references markers [1] / [R01] become clickable links to #ref-N
  - each References entry is its own paragraph with a clickable URL
  - external_links markdown [text](url) stays as hyperref links
  - header-includes.tex: cas-sc-like wide geometry, setspace, float fractions, hyperref

Layout written into <run_dir> (makePdf contract):
  draft.tex, draft.pdf, Makefile, .latexmkrc, build/
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def require_gate_pass(run_dir: Path, *, force: bool) -> None:
    """Refuse packaging unless verification_report.md shows overall PASS."""
    if force:
        print("WARNING: --force set; skipping gate PASS check (debug only).", file=sys.stderr)
        return
    report = run_dir / "verification_report.md"
    if not report.exists():
        raise SystemExit(
            f"ERROR: missing {report.name}. Run verify_run.py (or run_gate_and_package.py) first. "
            "Use --force only for debugging."
        )
    text = report.read_text(encoding="utf-8")
    if re.search(r"Overall Gate Status:\s*\*\*PASS\*\*", text) or re.search(
        r"# Verification & De-Slop Report \(`PASS`\)", text
    ):
        return
    if re.search(r"\bFAIL\b", text) or "Overall Gate Status:** **FAIL**" in text:
        raise SystemExit(
            f"ERROR: gate did not PASS ({report}). Refusing PDF packaging. "
            "Fix SEVERE findings and re-run verify_run.py, or use run_gate_and_package.py."
        )
    raise SystemExit(
        f"ERROR: could not confirm PASS in {report}. Refusing PDF packaging."
    )


LATEXMKRC = """\
# Keep auxiliary files (.aux, .log, .out, .fls, …) in build/;
# PDFs stay next to the .tex sources.
$aux_dir = 'build';
$pdf_mode = 1;
$interaction = 'nonstopmode';
"""

MAKEFILE = """\
# Compile all .tex files in this directory.
# PDFs → here; aux/log/out → build/
#
#   make          build all PDFs
#   make clean    remove auxiliary files from build/
#   make distclean  remove build/ entirely

TEXFILES := $(wildcard *.tex)
PDFS := $(TEXFILES:.tex=.pdf)

.PHONY: all clean distclean

all: $(PDFS)

%.pdf: %.tex .latexmkrc
\tlatexmk -pdf $<

clean:
\tlatexmk -c -auxdir=build $(TEXFILES)

distclean: clean
\trm -rf build
"""

REF_HEADING_RE = re.compile(r"(?im)^##\s+References\s*$")
REF_LINE_RE = re.compile(r"^\[(\d+|R\d+)\]\s+(.+)$")
URL_AT_END_RE = re.compile(r"(https?://\S+?)\s*$")
# Citation markers like [1] or [R01], but not markdown links [text](url)
CITE_MARKER_RE = re.compile(r"\[(\d+|R\d+)\](?!\()")


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_tools() -> None:
    missing = [t for t in ("pandoc", "latexmk") if shutil.which(t) is None]
    if missing:
        raise SystemExit(
            f"ERROR: missing required tools: {', '.join(missing)}. "
            "Install pandoc and a TeX distribution that provides latexmk."
        )


def write_build_config(run_dir: Path) -> None:
    (run_dir / ".latexmkrc").write_text(LATEXMKRC, encoding="utf-8")
    (run_dir / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    (run_dir / "build").mkdir(exist_ok=True)


def find_markdown(run_dir: Path, draft: Path | None) -> Path:
    if draft is not None:
        return draft
    for name in ("draft_clean.md", "draft.clean.md", "narration.voice_strip.md"):
        candidate = run_dir / name
        if candidate.exists():
            return candidate
    raise SystemExit(f"ERROR: no draft_clean.md found under {run_dir}")


def _split_label_url(rest: str) -> tuple[str, str | None]:
    """Split 'Label text. https://...' into (label, url)."""
    m = URL_AT_END_RE.search(rest)
    if not m:
        return rest.strip(), None
    url = m.group(1)
    # Strip trailing sentence punctuation only; keep ')' that closes '(' in the path.
    while url and url[-1] in ".,;\"'":
        url = url[:-1]
    if url.endswith(")") and url.count("(") < url.count(")"):
        url = url[:-1]
    label = rest[: m.start()].strip().rstrip(".")
    return label, url


def _format_ref_block(rid: str, label: str, url: str | None) -> str:
    """One reference as its own markdown block with PDF-friendly anchors + links."""
    lines = [
        f"[]{{#ref-{rid}}}",
        f"**[{rid}]** {label}" + ("." if label and not label.endswith((".", "!", "?")) else ""),
    ]
    if url:
        # Explicit markdown link → pandoc \\href{} (handles () in Wikipedia paths)
        lines.append("")
        lines.append(f"[{url}]({url})")
    return "\n".join(lines)


def preprocess_markdown_for_pdf(md: str) -> str:
    """
    Normalize end_references and bare URL lines for LaTeX/PDF.

    - Body [1] / [R01] → [[1]](#ref-1) (clickable jump to References)
    - References entries each get their own paragraph, anchor, and <url> autolink
    - Existing [text](url) markdown links are left alone
    """
    split = REF_HEADING_RE.split(md, maxsplit=1)
    if len(split) == 1:
        # No References section: still turn body markers into no-ops if present
        return md

    body, refs_raw = split[0], split[1]

    entries: list[tuple[str, str, str | None]] = []
    for raw_line in refs_raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = REF_LINE_RE.match(line)
        if not m:
            # Keep freeform lines as their own paragraphs
            entries.append(("", line, None))
            continue
        rid, rest = m.group(1), m.group(2)
        label, url = _split_label_url(rest)
        entries.append((rid, label, url))

    known_ids = {rid for rid, _, _ in entries if rid}

    def cite_sub(match: re.Match[str]) -> str:
        rid = match.group(1)
        if known_ids and rid not in known_ids:
            return match.group(0)
        return f"[[{rid}]](#ref-{rid})"

    body = CITE_MARKER_RE.sub(cite_sub, body)

    ref_blocks: list[str] = []
    for rid, label, url in entries:
        if not rid:
            ref_blocks.append(label)
            continue
        ref_blocks.append(_format_ref_block(rid, label, url))

    refs_md = "## References\n\n" + "\n\n".join(ref_blocks) + "\n"
    return body.rstrip() + "\n\n" + refs_md


def header_includes_path() -> Path:
    return skill_root() / "templates" / "makePdf" / "header-includes.tex"


def main() -> int:
    parser = argparse.ArgumentParser(description="Package draft_clean.md as draft.pdf (makePdf layout).")
    parser.add_argument("run_dir", help="Run directory containing draft_clean.md")
    parser.add_argument("--draft", help="Override path to the markdown draft")
    parser.add_argument("--title", default=None, help="Optional PDF title metadata")
    parser.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    parser.add_argument(
        "--keep-preprocessed",
        action="store_true",
        help="Also write draft_clean.pdf.md (normalized markdown fed to pandoc)",
    )
    parser.add_argument(
        "--require-pass",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require verification_report.md overall PASS before packaging (default: True)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="DEBUG ONLY: skip gate PASS check. Skills forbid this for release/done.",
    )
    args = parser.parse_args()

    ensure_tools()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"ERROR: not a directory: {run_dir}", file=sys.stderr)
        return 2

    # Default: require PASS. --force skips (debug only).
    require_gate_pass(run_dir, force=bool(args.force) or not args.require_pass)

    md_path = find_markdown(run_dir, Path(args.draft).expanduser().resolve() if args.draft else None)
    write_build_config(run_dir)

    raw_md = md_path.read_text(encoding="utf-8")
    pdf_md = preprocess_markdown_for_pdf(raw_md)
    if args.keep_preprocessed:
        (run_dir / "draft_clean.pdf.md").write_text(pdf_md, encoding="utf-8")

    tex_path = run_dir / "draft.tex"
    pdf_path = run_dir / "draft.pdf"
    header = header_includes_path()
    if not header.exists():
        print(f"ERROR: missing pandoc header includes at {header}", file=sys.stderr)
        return 2

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".md",
        prefix="draft_clean_pdf_",
        dir=run_dir,
        delete=False,
    ) as tmp:
        tmp.write(pdf_md)
        tmp_path = Path(tmp.name)

    try:
        pandoc_cmd = [
            "pandoc",
            str(tmp_path),
            "-o",
            str(tex_path),
            "--standalone",
            "-f",
            "markdown+autolink_bare_uris",
            "-t",
            "latex",
            f"--pdf-engine={args.engine}",
            f"--include-in-header={header}",
            # Single-column article; A4 + left-aligned equations (cas-sc sample options)
            "-V",
            "documentclass=article",
            "-V",
            "classoption=a4paper",
            "-V",
            "classoption=fleqn",
            "-V",
            "colorlinks=true",
            "-V",
            "linkcolor=blue",
            "-V",
            "urlcolor=blue",
        ]
        if args.title:
            pandoc_cmd.extend(["-V", f"title={args.title}"])

        print(f"Converting {md_path.name} → draft.tex (citations + references normalized) …")
        subprocess.run(pandoc_cmd, check=True, cwd=run_dir)

        # Always rebuild PDF from the fresh .tex (ignore stale draft.pdf).
        print("Compiling draft.tex → draft.pdf (aux → build/) …")
        subprocess.run(["latexmk", "-g", "-pdf", "draft.tex"], check=True, cwd=run_dir)
    finally:
        tmp_path.unlink(missing_ok=True)

    for pattern in ("*.aux", "*.log", "*.out", "*.fls", "*.fdb_latexmk", "*.toc", "*.synctex.gz"):
        for stray in run_dir.glob(pattern):
            dest = run_dir / "build" / stray.name
            dest.parent.mkdir(exist_ok=True)
            shutil.move(str(stray), str(dest))

    if not pdf_path.exists():
        print("ERROR: draft.pdf was not produced.", file=sys.stderr)
        return 1

    print(f"OK: {pdf_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: command failed with exit {exc.returncode}: {exc.cmd}", file=sys.stderr)
        raise SystemExit(1) from exc
