#!/usr/bin/env python3
"""
run_gate_and_package.py — Hard-refuse wrapper for verify_and_deslopify.

1. Run verify_run.py <run_dir> --stage final
2. If exit != 0: print GATE FAILED banner, refuse packaging, exit 1
3. If exit == 0: call package_pdf.py with remaining args

Preferred user-facing entrypoint. Do not call package_pdf.py alone for release.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
VERIFY = SCRIPTS / "verify_run.py"
PACKAGE = SCRIPTS / "package_pdf.py"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify run (must PASS) then package draft.pdf. Hard refuse on gate FAIL."
    )
    parser.add_argument("run_dir", help="Run directory containing draft_clean.md")
    parser.add_argument(
        "--force-package",
        action="store_true",
        help="DEBUG ONLY: pass --force to packager (skills forbid this for 'done').",
    )
    args, passthrough = parser.parse_known_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"ERROR: not a directory: {run_dir}", file=sys.stderr)
        return 2

    print(f"=== GATE: {VERIFY.name} {run_dir} --stage final ===", flush=True)
    gate = subprocess.run(
        [sys.executable, str(VERIFY), str(run_dir), "--stage", "final"],
    )
    if gate.returncode != 0:
        banner = (
            "\n"
            "============================================================\n"
            " GATE FAILED — refusing PDF / deliverable packaging\n"
            f" Fix SEVERE findings in {run_dir / 'verification_report.md'}\n"
            " then re-run this wrapper. Drafts left on disk for repair.\n"
            "============================================================\n"
        )
        print(banner, file=sys.stderr)
        report = run_dir / "verification_report.md"
        if report.exists():
            print(report.read_text(encoding="utf-8"))
        return 1

    pkg_cmd = [sys.executable, str(PACKAGE), str(run_dir), *passthrough]
    if args.force_package:
        pkg_cmd.append("--force")
    else:
        if "--require-pass" not in passthrough and "--no-require-pass" not in passthrough:
            pkg_cmd.append("--require-pass")

    print(f"=== PACKAGE: {PACKAGE.name} ===", flush=True)
    pkg = subprocess.run(pkg_cmd)
    return pkg.returncode


if __name__ == "__main__":
    raise SystemExit(main())
