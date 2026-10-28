# Guide for agents

This repository is an Agent Skill. `SKILL.md` is the source of truth.

## Keep it portable

- Do not hard-code a single host (Cursor, Claude Code, Codex, etc.).
- Prefer relative paths from the skill root: `scripts/verify_run.py`, `scripts/package_pdf.py`, `presets/`, `references/`.
- Final user-facing artifact for a full run is `draft.pdf`. Markdown `draft_clean.md` is the editable source.

## Filenames

- Use `draft_clean.md` (underscore). Do not invent `draft.clean.md` for new runs.
- Aux LaTeX files belong in `build/` only (makePdf contract).

## Citation modes

Brief field `citation_mode` is one of:

- `none` — sidecar only
- `end_references` — `[n]` markers + `## References`
- `external_links` — markdown links to URLs

See `references/citation_modes.md`.

## Changing rules

- Style/defect taxonomy: `references/style_and_slop_rules.md`
- Deterministic scanners must stay in sync in `scripts/verify_run.py`
- Credit `blader/humanizer` when adapting wording from its patterns

## Hard refuse / done criteria

- Prefer `scripts/run_gate_and_package.py` for shipping. Never claim done if the wrapper exits non-zero.
- Never call `scripts/package_pdf.py` alone for release; packager `--force` is debug-only.
- Style/defect taxonomy includes **M4** (contrastive cadence), **M5** (dispute theater), and **M6** (JP→EN calques); metaphors are zero-tolerance (M1–M2).
