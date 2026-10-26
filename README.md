# verify_and_deslopify

An open-source **Research → Sidecar Receipts → Draft → Literalize & De-Slop → Deterministic Verification Gate** skill and harness for AI coding/writing agents (Cursor, Claude Code, Codex, Windsurf, OpenCode), with an **optional** LaTeX/PDF packaging step.

AI text often commits one of these cardinals sins:

1. **Deep-research tools write like compliance memos:** models leak **"receipt theater"** into the prose (*"as documented by Reuters," "the record shows"*).
2. **De-slop / humanizer skills hallucinate during rewrites:** models invent unsupported agency, change quotes, or simply keep hallucinated metaphors that make no sense (the **WHO THE HELL WRITES LIKES THIS** failure mode).

`verify_and_deslopify` separates the **epistemic channel** (`receipts.md`) from the **prose channel** (`draft_clean.md`) and enforces both with a zero-dependency Python gate (`scripts/verify_run.py`).

**Deliverable choice:**

| Path | Final artifact | What you need |
| --- | --- | --- |
| **Markdown (default)** | `draft_clean.md` (+ gate report) | Python 3.10+ only |
| **LaTeX / PDF (optional)** | `draft.tex` + `draft.pdf` (makePdf layout) | Also `pandoc`, `latexmk`, and a TeX engine (`pdflatex` or `xelatex`) with usual packages |

Stay on markdown unless you have a TeX distribution installed. The gate and de-slop pass are the same either way.

---

## What makes this different

1. **Sidecar receipts** — hard facts live in `receipts.md`; prose does not perform verification unless you opt into a citation mode.
2. **Literalize-first metaphor hygiene (`M1–M3`)** — ban invented agency; never replace a bad metaphor with a cleverer one.
3. **Targeted anti-slop rules (`H1, H5, H11, H15–H18, H23, H25`)** — adapted from [`blader/humanizer`](https://github.com/blader/humanizer).
4. **Deterministic gate** — `verify_run.py` hard-fails on ungrounded numbers/quotes, banned filler, formatting tells, and missing strip reports.
5. **Optional PDF packaging** — if TeX is installed, `package_pdf.py` emits `draft.pdf` with clickable in-text `[n]` jumps, one-reference-per-block bibliography, and clickable external URLs.

---

## Formats and citation modes

Formats (presets in `presets/`):

| Format | Typical use |
| --- | --- |
| `video_narration` | Spoken documentary / video-essay VO (~178 WPM) |
| `longform_article` | Investigative essay / feature / Substack |
| `case_study` | Engineering or business post-mortem |

Citation modes (`citation_mode` in `brief.yaml` — available for **all three** formats):

| `citation_mode` | Name | Prose behavior |
| --- | --- | --- |
| `none` | **Sidecar only** (default) | No markers, no URLs in prose |
| `end_references` | **End references** | `[1]`, `[2]`, … markers → final `## References` section |
| `external_links` | **External links** | Markdown links that point straight at source URLs |

---

## Proof: harness vs. no harness

### `video_narration` — same Lou Pearlman / Backstreet Boys beat

| Without harness | With harness (`verify_and_deslopify`) |
| --- | --- |
| Pearlman didn’t merely manage the Backstreet Boys. He structured himself as a sixth member — paid as if he’d been hitting the high notes. Management fees. Production fees. Entities stacked like a layer cake. Power of attorney. Flights on *his* airline interests. Savings steered into *his* investment programs. Vertical integration with a fatherly hug. When the Boys checked the math, “thank you, Big Poppa” became “why do we have three hundred thousand dollars while you have a mansion?” Four members sued in the late 1990s over accounting and “excessive” takes. Settlements followed. Years later Brian Littrell put the exit bluntly: they each paid about five million dollars *to get rid of him*. Not a buyout — a reverse hostage situation with platinum plaques. | Pearlman told Entertainment Weekly he was the sixth Backstreet Boy — always had been, always would be. The contracts backed that appetite. Reporting around the band’s lawsuit said Pearlman’s cut ran around forty-three percent of the Boys’ net earnings, with Trans Continental sitting on key trademarks. The band sued for about ten million dollars. By then they had grossed an estimated two hundred million. Brian Littrell’s camp had already noticed a smaller number: roughly three hundred thousand dollars reaching the members for all that work while Pearlman and his companies collected millions. They settled. Years later, Littrell told CBS each of them paid about five million dollars to get Pearlman out of their lives. That is a rare arrangement: the talent buys the exit. |

**Why the harness column wins for VO:** it keeps the money spine and named attributions, and drops invented-agency stacks (*layer cake*, *fatherly hug*, *reverse hostage situation with platinum plaques*).

### `longform_article` — same NCM “what concept means” beat

| Without harness | With harness (`verify_and_deslopify`) |
| --- | --- |
| **NCM** does neither token-by-token append nor full-sequence denoising. It learns a **hierarchy of discrete codes**—short and coarse first, longer and finer later—then generates **one level at a time**, predicting **all codes within a level in parallel** ([arxiv:2610.14162](https://arxiv.org/abs/2610.14162)). NCM’s “concept” is not a philosophical claim about human ideas. In the authors’ usage, it is the information carried by the **coarse levels of a learned code hierarchy**—an architectural term of art, not a cognitive theory ([Hazy Research blog](https://hazyresearch.stanford.edu/blog/2026-10-12-ncm)). | What “concept” means in NCM — The name can mislead. The authors define “concept” narrowly: the information carried by the coarse levels of a learned code hierarchy. That is a claim about representation order, not a claim that the model thinks in human ideas. Mechanically, NCM is two stages. First, a multiscale residual vector-quantized autoencoder learns to encode a length-L token sequence into K discrete levels whose lengths increase until the last level matches L. Nested dropout pushes early levels to carry useful structure on their own. Second, that tokenizer is frozen and a transformer learns to predict each level from the cumulative reconstruction of earlier ones. At inference, levels are produced in order; a decoder turns the finished reconstruction back into tokens. The method borrows from vision. Visual Autoregressive Modeling—a NeurIPS 2024 Best Paper—replaced raster-scan next-token image generation with coarse-to-fine next-scale prediction and reported large ImageNet gains plus roughly twenty-times-faster inference versus its autoregressive baseline. |

**Why the harness column wins for articles:** same facts, but no study-guide boldface (`H15`), no "X, but not (or also) Y" prose. 

---

## Repository layout

```text
verify_and_deslopify/
├── SKILL.md
├── README.md
├── LICENSE
├── AGENTS.md
├── topics.txt                 # Suggested GitHub topics (apply after remote create)
├── references/
│   ├── style_and_slop_rules.md
│   └── citation_modes.md
├── presets/
│   ├── video_narration.yaml
│   ├── longform_article.yaml
│   └── case_study.yaml
├── templates/
│   └── makePdf/               # Makefile, latexmkrc, header-includes.tex (hyperref)
└── scripts/
    ├── verify_run.py          # Deterministic gate (stdlib only)
    └── package_pdf.py         # draft_clean.md → draft.pdf (pandoc + latexmk + linkify)
```

---

## Installation

```bash
# Cursor
ln -s ~/verify_and_deslopify ~/.cursor/skills/verify_and_deslopify

# Claude Code
ln -s ~/verify_and_deslopify ~/.claude/skills/verify_and_deslopify

# Codex / OpenCode / universal Agent Skills folder
ln -s ~/verify_and_deslopify ~/.agents/skills/verify_and_deslopify
```

**Always needed:** Python 3.10+ (for `scripts/verify_run.py`).

**Only for the LaTeX/PDF path:** `pandoc`, `latexmk`, and `pdflatex` or `xelatex` (plus a normal TeX Live / MiKTeX package set). If those are missing, stop at `draft_clean.md`.

---

## Quickstart

### Prompt: markdown only (no TeX)

Use this when you want a verified, de-slopped draft and do **not** have LaTeX installed (or do not want a PDF):

```text
Use verify_and_deslopify to write a 2,000-word longform_article on [TOPIC]
with angle [ANGLE], citation_mode end_references.
Put the run in runs/test_<id>/.
Stop after draft_clean.md and a passing verify_run.py — do not run package_pdf.py
and do not produce draft.tex or draft.pdf.
```

### Prompt: LaTeX / PDF (TeX installed)

Use this when `pandoc`, `latexmk`, and a TeX engine are available:

```text
Use verify_and_deslopify to write a 2,000-word longform_article on [TOPIC]
with angle [ANGLE], citation_mode end_references.
Put the run in runs/test_<id>/.
After verify_run.py passes, run package_pdf.py so the final deliverable is
draft.pdf (with draft.tex and makePdf aux files under build/).
```

### Brief file instead of a free-form prompt

Copy a preset to `runs/test_<id>/brief.yaml`, set `subject` / `angle` / `citation_mode`, then:

```text
Run verify_and_deslopify on runs/test_<id>/brief.yaml
Stop at draft_clean.md (markdown only).
```

or:

```text
Run verify_and_deslopify on runs/test_<id>/brief.yaml
Finish with draft.pdf via package_pdf.py.
```

### Gate only

```bash
python3 scripts/verify_run.py runs/test_<id> --stage final
```

### PDF only (after `draft_clean.md` exists; requires TeX)

```bash
python3 scripts/package_pdf.py runs/test_<id>
```

## Credits

- **Sidecar receipts & metaphor-strip (`M1–M3`):** from spoken narration / VO hygiene workflows.
- **Anti-slop patterns (`H1, H5, H11, H15–H18, H23, H25`):** adapted from [blader/humanizer](https://github.com/blader/humanizer) (MIT), based on Wikipedia’s [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
- **Optional PDF layout:** makePdf skill contract (`.tex` / `.pdf` at run root, aux in `build/`), only when TeX tools are installed.

## License

MIT
