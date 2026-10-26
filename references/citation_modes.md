# Citation modes

Set `citation_mode` in `brief.yaml`. Applies to `video_narration`, `longform_article`, and `case_study`.

## `none` — Sidecar only (default)

- Prose: no `[n]` markers, no URLs.
- Full sources: `receipts.md` only.
- Best for spoken VO and clean essays where links would interrupt reading.

## `end_references` — End references

- Prose: numbered markers `[1]`, `[2]`, … (or receipt IDs `[R01]` if you prefer).
- End of `draft_clean.md`: a `## References` section listing each marker with outlet, date, and URL.
- `receipts.md` remains the audit ledger (quotes, caveats, status).
- `verify_run.py` requires a `## References` heading when this mode is set.

Example:

```markdown
NCM reports twenty-one times faster wall-clock generation on LM1B [1].

## References

[1] Kumbong et al., Next-Concept Modeling (2026). https://arxiv.org/abs/2610.14162
```

## `external_links` — External links

- Prose: markdown (or LaTeX href) links that open the source directly.
- Prefer short link text (`[Hazy Research blog](https://…)`) over bare URLs.
- `receipts.md` still holds verbatim quotes and dispute notes.
- Do not combine with heavy mechanical boldface (`H15`).

Example:

```markdown
NCM adapts next-scale prediction from Visual Autoregressive Modeling
([Tian et al., VAR](https://blog.neurips.cc/2024/12/10/announcing-the-neurips-2024-best-paper-awards/)).
```

## Shared bans (all modes)

Receipt-theater phrases remain forbidden: *the record shows*, *sources confirm*, *as documented*, *according to multiple sources*, *verified reports*.
