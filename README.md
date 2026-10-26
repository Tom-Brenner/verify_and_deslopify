# verify_and_deslopify

An open-source **Research → Sidecar Receipts → Draft → Literalize & De-Slop → Deterministic Verification Gate → PDF** skill and harness for AI coding/writing agents (Cursor, Claude Code, Codex, Windsurf, OpenCode).

Most AI writing pipelines fail in one of two ways:

1. **Deep-research tools write like compliance memos:** models leak **"receipt theater"** into the prose (*"as documented by Reuters," "the record shows"*).
2. **De-slop / humanizer skills hallucinate during rewrites:** models invent unsupported agency (*"the bleach-blond empire walks into custody"*) or mutate numbers and quotes.

`verify_and_deslopify` separates the **epistemic channel** (`receipts.md`) from the **prose channel** (`draft_clean.md`), enforces both with a zero-dependency Python gate (`scripts/verify_run.py`), and packages the accepted draft as **`draft.pdf`** (makePdf layout: `.tex` / `.pdf` at the run root, aux under `build/`).

---

## What makes this different

1. **Sidecar receipts** — hard facts live in `receipts.md`; prose does not perform verification unless you opt into a citation mode.
2. **Literalize-first metaphor hygiene (`M1–M3`)** — ban invented agency; never replace a bad metaphor with a cleverer one.
3. **Targeted anti-slop rules (`H1, H5, H11, H15–H18, H23, H25`)** — adapted from [`blader/humanizer`](https://github.com/blader/humanizer).
4. **Deterministic gate** — `verify_run.py` hard-fails on ungrounded numbers/quotes, banned filler, formatting tells, and missing strip reports.
5. **PDF as the deliverable** — `package_pdf.py` emits `draft.pdf` via pandoc + latexmk.

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

Sources: harness output from `runs/test1/draft_clean.md`; non-harness excerpt from a parallel draft that used mechanical boldface and inline URL citation theater.

| Without harness | With harness (`verify_and_deslopify`) |
| --- | --- |
| **NCM** does neither token-by-token append nor full-sequence denoising. It learns a **hierarchy of discrete codes**—short and coarse first, longer and finer later—then generates **one level at a time**, predicting **all codes within a level in parallel** ([arxiv:2610.14162](https://arxiv.org/abs/2610.14162)). NCM’s “concept” is not a philosophical claim about human ideas. In the authors’ usage, it is the information carried by the **coarse levels of a learned code hierarchy**—an architectural term of art, not a cognitive theory ([Hazy Research blog](https://hazyresearch.stanford.edu/blog/2026-10-12-ncm)). The design lineage is visual, not linguistic. NCM adapts **next-scale prediction** from Visual Autoregressive Modeling (VAR), a NeurIPS 2024 Best Paper… ([Tian et al., VAR](https://blog.neurips.cc/2024/12/10/announcing-the-neurips-2024-best-paper-awards/); [proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/9a24e284b187f662681440ba15c416fb-Paper-Conference.pdf)). Text has no natural “downsample,” so NCM must *learn* useful coarse representations… ([arxiv abstract](https://arxiv.org/abs/2610.14162)). | What “concept” means in NCM — The name can mislead. The authors define “concept” narrowly: the information carried by the coarse levels of a learned code hierarchy. That is a claim about representation order, not a claim that the model thinks in human ideas. Mechanically, NCM is two stages. First, a multiscale residual vector-quantized autoencoder learns to encode a length-L token sequence into K discrete levels whose lengths increase until the last level matches L. Nested dropout pushes early levels to carry useful structure on their own. Second, that tokenizer is frozen and a transformer learns to predict each level from the cumulative reconstruction of earlier ones. At inference, levels are produced in order; a decoder turns the finished reconstruction back into tokens. The method borrows from vision. Visual Autoregressive Modeling—a NeurIPS 2024 Best Paper—replaced raster-scan next-token image generation with coarse-to-fine next-scale prediction… NCM adapts residual multiscale quantization and next-scale prediction to text… A Hazy Research walkthrough shows a German-to-English sample climbing level by level to a final BLEU of 77.8… |

**Why the harness column wins for articles:** same facts, but no study-guide boldface (`H15`), no URL litter in the prose channel (`citation_mode: none` + sidecar receipts), and a full mechanical spine a reader can follow without clicking away mid-sentence.

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
│   └── makePdf/               # Makefile + latexmkrc copied into each run
└── scripts/
    ├── verify_run.py          # Deterministic gate (stdlib only)
    └── package_pdf.py         # draft_clean.md → draft.pdf (pandoc + latexmk)
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

**Host tools for Stage 6 PDF:** Python 3.10+, `pandoc`, `latexmk`, and `pdflatex` (or `xelatex`).

---

## Quickstart

### Full pipeline

```text
Use verify_and_deslopify to write a 2,000-word longform_article on [TOPIC]
with angle [ANGLE], citation_mode end_references (or none / external_links).
Put the run in runs/<slug>/ and finish with draft.pdf.
```

Or copy a preset to `runs/<slug>/brief.yaml`, set `subject` / `angle` / `citation_mode`, then:

```text
Run verify_and_deslopify on runs/<slug>/brief.yaml
```

### Gate only

```bash
python3 scripts/verify_run.py runs/my_topic --stage final
```

### PDF only (after `draft_clean.md` exists)

```bash
python3 scripts/package_pdf.py runs/my_topic
```

---

## Suggested GitHub topics

See `topics.txt`. Overlap with [`blader/humanizer`](https://github.com/blader/humanizer) plus verification/PDF tags:

`agent-skills`, `ai-writing`, `anti-slop`, `humanizer`, `claude-code`, `cursor`, `codex`, `llm`, `prompt-engineering`, `writing-tools`, `fact-checking`, `research`, `latex`, `pdf`

After you create the remote:

```bash
gh repo edit --add-topic agent-skills --add-topic ai-writing --add-topic anti-slop \
  --add-topic humanizer --add-topic claude-code --add-topic cursor --add-topic codex \
  --add-topic llm --add-topic fact-checking --add-topic research --add-topic latex --add-topic pdf
```

---

## Credits

- **Sidecar receipts & metaphor-strip (`M1–M3`):** from spoken narration / VO hygiene workflows.
- **Anti-slop patterns (`H1, H5, H11, H15–H18, H23, H25`):** adapted from [blader/humanizer](https://github.com/blader/humanizer) (MIT), based on Wikipedia’s [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
- **PDF layout:** makePdf skill contract (`.tex` / `.pdf` at run root, aux in `build/`).

## License

MIT
