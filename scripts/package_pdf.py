#!/usr/bin/env python3
"""
package_pdf.py — Convert draft_clean.md to draft.pdf using the makePdf layout.

Requires: pandoc, latexmk, and a LaTeX engine (pdflatex or xelatex).
Zero Python dependencies beyond the stdlib.

Layout written into <run_dir> (makePdf contract):
  draft.tex, draft.pdf, Makefile, .latexmkrc, build/
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Package draft_clean.md as draft.pdf (makePdf layout).")
    parser.add_argument("run_dir", help="Run directory containing draft_clean.md")
    parser.add_argument("--draft", help="Override path to the markdown draft")
    parser.add_argument("--title", default=None, help="Optional PDF title metadata")
    parser.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    args = parser.parse_args()

    ensure_tools()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"ERROR: not a directory: {run_dir}", file=sys.stderr)
        return 2

    md_path = find_markdown(run_dir, Path(args.draft).expanduser().resolve() if args.draft else None)
    write_build_config(run_dir)

    tex_path = run_dir / "draft.tex"
    pdf_path = run_dir / "draft.pdf"

    pandoc_cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(tex_path),
        "--standalone",
        "-f",
        "markdown",
        "-t",
        "latex",
        f"--pdf-engine={args.engine}",
    ]
    if args.title:
        pandoc_cmd.extend(["-V", f"title={args.title}"])

    print(f"Converting {md_path.name} → draft.tex …")
    subprocess.run(pandoc_cmd, check=True, cwd=run_dir)

    # latexmk reads .latexmkrc (aux_dir=build).
    print("Compiling draft.tex → draft.pdf (aux → build/) …")
    subprocess.run(["latexmk", "-pdf", "draft.tex"], check=True, cwd=run_dir)

    # Move stray aux files if latexmk ignored aux_dir for any reason
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
