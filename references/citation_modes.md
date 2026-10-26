# Citation modes

Set `citation_mode` in `brief.yaml`. Applies to `video_narration`, `longform_article`, and `case_study`.

## `none` — Sidecar only (default)

- Prose: no `[n]` markers, no URLs.
- Full sources: `receipts.md` only.
- Best for spoken VO and clean essays where links would interrupt reading.

## `end_references` — End references

- Prose: numbered markers `[1]`, `[2]`, … (or receipt IDs `[R01]` if you prefer).
- End of `draft_clean.md`: a `## References` section listing each marker with outlet, date, and URL.
- Prefer **one reference per line** (blank lines between entries are fine; `package_pdf.py` also splits them for PDF).
- `receipts.md` remains the audit ledger (quotes, caveats, status).
- `verify_run.py` requires a `## References` heading when this mode is set.

### Markdown authoring (simple form)

```markdown
NCM reports twenty-one times faster wall-clock generation on LM1B [1].

## References

[1] Kumbong et al., Next-Concept Modeling (2026). https://arxiv.org/abs/2610.14162
[2] Hazy Research blog (2026). https://hazyresearch.stanford.edu/blog/2026-10-12-ncm
```

### What Stage 6 PDF does (`scripts/package_pdf.py` + makePdf)

`package_pdf.py` rewrites the markdown before pandoc/LaTeX so the PDF gets:

1. **Clickable in-text markers** — `[1]` becomes an internal link to the matching References entry.
2. **One reference per block** — each `[n] …` line is its own paragraph (no run-on bibliography).
3. **Clickable external URLs** — trailing `https://…` becomes a hyperref link on its own line (parentheses in paths, e.g. Wikipedia, are preserved).
4. **Visible link color** — `templates/makePdf/header-includes.tex` configures `hyperref` after load for internal + URL links.

You do not need to hand-write `[[1]](#ref-1)` in `draft_clean.md`; the packager adds that for PDF only.

## `external_links` — External links

- Prose: markdown links that open the source directly.
- Prefer short link text (`[Hazy Research blog](https://example.com)`) over bare URLs.
- `receipts.md` still holds verbatim quotes and dispute notes.
- Do not combine with heavy mechanical boldface (`H15`).
- Stage 6 PDF keeps these as clickable `hyperref` URLs (same header-includes).

Example:

```markdown
NCM adapts next-scale prediction from Visual Autoregressive Modeling
([Tian et al., VAR](https://blog.neurips.cc/2024/12/10/announcing-the-neurips-2024-best-paper-awards/)).
```

## Shared bans (all modes)

Receipt-theater phrases remain forbidden: *the record shows*, *sources confirm*, *as documented*, *according to multiple sources*, *verified reports*.
