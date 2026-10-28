---
name: verify_and_deslopify
description: >-
  End-to-end sourced writing harness: brief -> live research & sidecar receipts
  -> voice-first draft -> literalize & de-slop pass -> deterministic verification
  gate + PDF packaging. Use whenever the user wants researched, fact-checked writing
  (video essay/narration, investigative article, case study, post-mortem, memo,
  or standalone de-slop + verification) that sounds human, keeps sources in a
  sidecar file instead of performing "receipt theater" in the prose, and passes
  a hard verification gate. Final deliverable is draft.pdf.
license: MIT
metadata:
  version: "1.0.0"
---

# verify_and_deslopify

A six-stage **Research → Verify → Draft → De-slop → Gate → PDF** harness for producing source-grounded, human-sounding prose across any format (video essays/VO, investigative articles, case studies, post-mortems, technical deep-dives, or memos).

**Core architectural rule:**
> **Verification lives in `receipts.md` + `verification_report.md`. Voice lives in `draft_clean.md`. The publishable artifact is `draft.pdf`.**
> Sources, URLs, verbatim quotes, and epistemic caveats never perform as "receipt theater" inside the prose unless a named source or broadcast *is* the literal event in the story — or the brief explicitly opts into a citation mode below.

---

## Modes of Operation

1. **Full Pipeline Mode (`research → verify → draft → strip → gate → pdf`):**
   Given a topic or `brief.yaml`, create a run folder under `runs/test_<id>/` (or a user-specified directory), research into `receipts.md`, outline in `plan.md`, write `draft.md`, strip into `draft_clean.md` + `strip_report.md`, then ship via `scripts/run_gate_and_package.py` (verify must PASS before `draft.pdf`).

2. **Standalone Audit / De-slop Mode (`strip → gate` on existing files):**
   Given an existing draft file (and optional `receipts.md`), run Stage 4 and Stage 5 (`scripts/verify_run.py --draft <file> [--receipts <file>]`). Optionally run Stage 6 to emit a PDF.

---

## Run Directory Contract

```text
<run_dir>/
  brief.yaml               # Stage 0
  receipts.md              # Stage 1: ALL claims, URLs, quotes, caveats (sidecar)
  plan.md                  # Stage 2
  draft.md                 # Stage 3: voice-first draft
  draft_clean.md           # Stage 4: de-slopped markdown (Windows-safe filename)
  strip_report.md          # Stage 4: span | defect | fix
  verification_report.md   # Stage 5: verify_run.py output
  draft.tex                # Stage 6: LaTeX source (makePdf)
  draft.pdf                # Stage 6: FINAL deliverable
  Makefile                 # Stage 6: makePdf makefile
  .latexmkrc               # Stage 6: aux files → build/
  build/                   # Stage 6: .aux .log .out .fls …
```

Filenames use underscores (`draft_clean.md`), not dots inside the stem, so Windows tooling does not confuse multi-extension names.

If `<run_dir>/draft_clean.md` or `draft.pdf` already exists, ask before overwriting or pick a new `test_<id>`.

---

## Citation modes (`citation_mode` in `brief.yaml`)

Available for every format preset (`video_narration`, `longform_article`, `case_study`):

| Value | Name (use this term) | What appears in prose | Where full sources live |
| --- | --- | --- | --- |
| `none` | **Sidecar only** (default) | No `[n]` markers, no URLs | `receipts.md` only |
| `end_references` | **End references** | Bracket markers `[1]`, `[2]`, … (or `[R01]`) pointing to a final `## References` section | Markers in prose; bibliography at document end; full notes still in `receipts.md` |
| `external_links` | **External links** | Markdown/HTML hyperlinks that open the source URL directly, e.g. `[Paper](https://…)` | Link targets in prose; full notes still in `receipts.md` |

Rules:
- Never use vague receipt theater (*"the record shows"*, *"sources confirm"*) in any mode.
- `end_references`: every marker must resolve to one entry under `## References` at the end of `draft_clean.md`.
- `external_links`: link text should be a short source name or claim label, not a raw pasted URL as the only readable text.
- `video_narration` can use citation modes for print/PDF export, but spoken VO still reads without saying "bracket one".

---

## Stage-by-Stage Workflow

```text
verify_and_deslopify checklist:
- [ ] Stage 0: Read or initialize brief.yaml (format + citation_mode)
- [ ] Stage 1: Research -> receipts.md + `python3 scripts/verify_run.py <run_dir> --stage receipts`
- [ ] Stage 2: Outline -> plan.md
- [ ] Stage 3: Voice-first draft -> draft.md
- [ ] Stage 4: Literalize & de-slop -> draft_clean.md + strip_report.md
- [ ] Stages 5–6: Gate+PDF -> `python3 scripts/run_gate_and_package.py <run_dir>` (must exit 0; hard refuse on FAIL)
```

### Stage 0 — Brief (`brief.yaml`)

Presets in `presets/`:
- `video_narration` — spoken cadence (~178 WPM), cold open → arc → coda
- `longform_article` — investigative essay / feature; sentence-case headings
- `case_study` — engineering / business post-mortem

Required keys:
- `subject`, `format`, `angle`, `target_word_count`, `tolerance_pct`, `tone`
- `citation_mode`: `none` | `end_references` | `external_links`
- `required_topics` / `forbidden_topics`

### Stage 1 — Research & Sidecar Receipts (`receipts.md`)

At run init, copy the placeholder so the model has a file **outside** the prose channel:

```bash
cp <skill_dir>/templates/receipts.md <run_dir>/receipts.md
```

Fill structured blocks (see template). Status may be `VERIFIED` | `DISPUTED` | `UNVERIFIED` | `ALLEGATION`.  
Never invent quotes, dates, or figures. Never announce “unverified” / “pleaded allegation” in `draft.md` — park Status/Caveat in `receipts.md` only. Then:

```bash
python3 <skill_dir>/scripts/verify_run.py <run_dir> --stage receipts
```

### Stage 2 — Plan (`plan.md`)

Opening hook + closing payoff; section word budgets; mapped `[Rxx]` IDs; at most one digression.

### Stage 3 — Voice-First Draft (`draft.md`)

1. Honor `citation_mode` (table above). Default `none` = zero claim IDs and zero URLs in prose.
2. Prefer `is / are / has / did` over copula avoidance.
3. Every number and quote must exist in `receipts.md`.

### Stage 4 — Literalize & De-Slop (`draft_clean.md` + `strip_report.md`)

Rewrite into `draft_clean.md`. Log every non-trivial change in `strip_report.md`.

Follow `references/style_and_slop_rules.md` (rules **M1–M5** and **H1, H5, H11, H15–H18, H23, H25**). Zero metaphors; no Not-X-But-Y; no dispute theater in prose.

### Stages 5–6 — Gate + PDF (hard refuse)

```bash
python3 <skill_dir>/scripts/run_gate_and_package.py <run_dir>
```

Must exit `0`. On FAIL the wrapper prints `GATE FAILED — refusing PDF / deliverable packaging`, exits non-zero, and does **not** produce/refresh `draft.pdf`. Fix SEVERE findings and re-run. Never call `package_pdf.py` alone for release; `--force` is debug-only.

On PASS the wrapper calls `package_pdf.py`, which writes `draft.tex`, compiles `draft.pdf`, drops `Makefile` + `.latexmkrc`, and keeps aux files under `build/`.

PDF link behavior (see `references/citation_modes.md` and `templates/makePdf/header-includes.tex`):

- `end_references`: in-text `[1]` markers become **clickable jumps** to the matching References entry; each reference is a **separate paragraph** with a **clickable URL**.
- `external_links`: markdown `[text](url)` links stay **clickable** in the PDF.
- Do not leave a run “done” if References still run together as one paragraph or if citation markers are inert text — re-run `package_pdf.py` after the packager upgrade.

**Definition of done:** `draft.pdf` exists at `<run_dir>/draft.pdf`, `verification_report.md` shows PASS, and `draft_clean.md` is the markdown source of the PDF.

Requires host tools: `pandoc`, `latexmk`, and `pdflatex` (or `xelatex`).

---

## Anti-patterns

- Shipping `draft_clean.md` as the “final” without Stage 6 PDF when the user asked for a finished document
- Using dotted stems like `draft.clean.md` (legacy only; prefer `draft_clean.md`)
- Mixing `end_references` markers with raw URL dumps (`external_links`) in the same piece unless the user asked for both
- Skipping `voice`/strip rules because citations were enabled
- Claiming PASS / done while `run_gate_and_package.py` (or `verify_run.py`) exits non-zero
- Calling `package_pdf.py` alone for release, or using `--force` to mark a run done
