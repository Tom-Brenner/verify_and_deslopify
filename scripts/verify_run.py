#!/usr/bin/env python3
"""
verify_run.py — Deterministic verification & anti-slop gate for verify_and_deslopify.

Zero external dependencies (Python 3.10+ stdlib only).
Checks:
  1. Stage artifacts & word-count contract (brief.yaml vs draft_clean.md / draft.md)
  2. Fact & quote grounding (numbers, years, currencies, percentages, and verbatim quotes
     in the draft must appear in receipts.md; zero orphan/mutated facts)
  3. Metaphor, agency & receipt-theater scanners (M1-M3)
  4. Targeted anti-slop & formatting scanners adapted from blader/humanizer:
     - H1:  Significance, legacy & trend inflation
     - H5:  Vague attributions & weasel words
     - H11: Synonym cycling / epithet chains (heuristic check + strip_report check)
     - H15: Mechanical boldface overuse
     - H16: Inline-header vertical lists (`- **Header:** ...`)
     - H17: Title Case in Markdown headings
     - H18: Decorative emojis
     - H23: Filler phrases & epistemic throat-clearing
     - H25: Generic positive / horizon conclusions (in closing paragraphs)
  5. Vendor citation residue (`oaicite`, `utm_source=chatgpt.com`, `[cite: 1]`)

Exit codes:
  0 — PASS (zero SEVERE findings)
  1 — FAIL (one or more SEVERE findings)
  2 — Usage / file error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Finding:
    rule_id: str
    severity: str  # "SEVERE" | "MEDIUM" | "ADVISORY"
    category: str
    span: str
    line: int
    message: str


# ---------------------------------------------------------------------------
# Minimal YAML subset parser (stdlib-only, handles brief.yaml flat + list keys)
# ---------------------------------------------------------------------------
def parse_simple_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data: dict = {}
    current_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_list_key:
            val = line[2:].strip().strip('"').strip("'")
            data.setdefault(current_list_key, []).append(val)
            continue
        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not rest or rest in {">-", "|"}:
                current_list_key = key
                data.setdefault(key, [])
            else:
                current_list_key = None
                val_str = rest.strip('"').strip("'")
                if val_str.lower() == "true":
                    data[key] = True
                elif val_str.lower() == "false":
                    data[key] = False
                elif val_str.lower() in {"null", "none", "~"}:
                    data[key] = None
                elif re.fullmatch(r"-?\d+", val_str):
                    data[key] = int(val_str)
                elif re.fullmatch(r"-?\d+\.\d+", val_str):
                    data[key] = float(val_str)
                else:
                    data[key] = val_str
    return data


# ---------------------------------------------------------------------------
# Rule Pattern Catalogs (M1-M3 + H1, H5, H15-H18, H23, H25 + Residue)
# ---------------------------------------------------------------------------

RECEIPT_THEATER_PATTERNS = [
    r"\bthe record shows\b",
    r"\bas the record reflects\b",
    r"\bpublic records confirm\b",
    r"\bas documented (?:in|by)\b",
    r"\baccording to multiple sources\b",
    r"\bverified reports (?:indicate|show|confirm)\b",
    r"\bsources confirm\b",
    r"\bas proof\b",
    r"\bfact-checkers note\b",
]

INVENTED_AGENCY_PATTERNS = [
    r"\bput (?:the )?word[s]? near (?:his|her|their) mouth\b",
    r"\bempire walks into\b",
    r"\bwrites the weather\b",
    r"\bfeels like losing oxygen\b",
    r"\bsharing oxygen\b",
    r"\buseful inventory\b",
    r"\bbalance sheet deciding\b",
    r"\bhistory whispers\b",
]

# H1: Significance, Legacy & Trend Inflation (cf. blader/humanizer #1)
H1_SIGNIFICANCE_PATTERNS = [
    r"\b(?:stands|serves|functions) as a (?:testament|reminder|catalyst|beacon|cornerstone)\b",
    r"\bis a (?:stark |powerful |enduring )?(?:testament|reminder) to\b",
    r"\bplays a (?:vital|significant|crucial|pivotal|key) role\b",
    r"\b(?:underscores|highlights) (?:its|the) (?:vital |crucial |ongoing )?(?:importance|significance|role)\b",
    r"\breflects broader (?:trends|shifts|movements)\b",
    r"\bsymbolizing (?:its|the) (?:ongoing|enduring|lasting)\b",
    r"\b(?:marks|marked|marking) a (?:pivotal|defining|watershed) moment\b",
    r"\bkey turning point\b",
    r"\bevolving landscape\b",
    r"\bindelible mark\b",
    r"\bsetting the stage for\b",
    r",\s*(?:highlighting|underscoring|emphasizing|showcasing|reflecting) (?:how|the|its)\b",
]

# H5: Vague Attributions & Weasel Authority (cf. blader/humanizer #5)
H5_WEASEL_PATTERNS = [
    r"\bindustry (?:reports|observers) (?:suggest|indicate|have noted|note|cite)\b",
    r"\bobservers have (?:cited|noted|pointed out)\b",
    r"\bexperts (?:argue|believe|agree|suggest|note)\b",
    r"\bsome critics (?:argue|claim|suggest|point out)\b",
    r"\bmany analysts (?:believe|argue|suggest)\b",
    r"\bstudies show that\b",
    r"\bseveral (?:sources|publications) (?:have )?(?:reported|noted|cited)\b",
]

# H23: Filler Phrases & Throat-Clearing (cf. blader/humanizer #23)
H23_FILLER_PATTERNS = [
    (r"\bin order to\b", "Replace 'in order to' with 'to'."),
    (r"\bdue to the fact that\b", "Replace 'due to the fact that' with 'because'."),
    (r"\bowing to the fact that\b", "Replace 'owing to the fact that' with 'because'."),
    (r"\bat this point in time\b", "Replace 'at this point in time' with 'now'."),
    (r"\bat the present time\b", "Replace 'at the present time' with 'now'."),
    (r"\bin the event that\b", "Replace 'in the event that' with 'if'."),
    (r"\b(?:has|have|had) the ability to\b", "Replace 'has the ability to' with 'can/could'."),
    (r"\bit is (?:important|worth) (?:to note|noting) that\b", "Delete throat-clearing filler; state the fact directly."),
    (r"\bit goes without saying\b", "Delete filler phrase."),
    (r"\bhere['\u2019]s the thing\b", "Delete LLM conversational glue ('Here's the thing')."),
    (r"\blet['\u2019]s (?:unpack|dive in|explore|break this down)\b", "Delete LLM signposting ('Let's unpack/dive in')."),
    (r"\bwithout further ado\b", "Delete signposting filler."),
    (r"\bat its core,\b", "Delete persuasive authority trope ('At its core,')."),
    (r"\bthe real question is\b", "Delete persuasive authority trope ('The real question is')."),
]

# H25: Generic Positive Conclusions (cf. blader/humanizer #25)
H25_CONCLUSION_PATTERNS = [
    r"\bthe future looks bright\b",
    r"\bexciting times lie ahead\b",
    r"\bjourney toward[s]? excellence\b",
    r"\ba major step in the right direction\b",
    r"\bcontinues to thrive\b",
    r"\bpoised for (?:continued )?(?:success|growth)\b",
    r"\bonly time will tell\b",
    r"\bremains to be seen how\b",
    r"\bultimately,\s+the story of .+ reminds us that\b",
]

# Vendor Citation Residue
RESIDUE_PATTERNS = [
    r"oaicite",
    r"utm_source=chatgpt\.com",
    r"\[cite:\s*\d+\]",
    r"\[attached_file:\d+\]",
    r"contentReference\[",
]

# Emoji regex (common decorative emoji blocks: Dingbats, Emoticons, Symbols/Pictographs, Transport)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]"
)

MINOR_TITLE_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
    "nor", "of", "on", "onto", "or", "over", "per", "so", "the", "to", "up",
    "via", "with", "yet",
}


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# ---------------------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------------------

def scan_regex_list(
    text: str,
    patterns: Iterable[str],
    rule_id: str,
    severity: str,
    category: str,
    message: str,
) -> list[Finding]:
    out: list[Finding] = []
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            out.append(
                Finding(
                    rule_id=rule_id,
                    severity=severity,
                    category=category,
                    span=m.group(0),
                    line=line_number_for_offset(text, m.start()),
                    message=message,
                )
            )
    return out


def scan_formatting_and_style(text: str, brief: dict, receipts_text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    fmt = str(brief.get("format", "longform_article"))
    allow_bold_in_vo = fmt != "video_narration"

    # Collect proper-cased tokens from receipts so sentence-case heading check doesn't false-positive on names/acronyms
    receipt_capitalized = set(re.findall(r"\b[A-Z][A-Za-z0-9_.-]+\b", receipts_text))

    # H15: Boldface overuse
    bold_spans = list(re.finditer(r"\*\*([^*]+)\*\*", text))
    if not allow_bold_in_vo and bold_spans:
        for m in bold_spans:
            findings.append(
                Finding(
                    rule_id="H15_BOLDFACE_IN_VO",
                    severity="SEVERE",
                    category="formatting",
                    span=m.group(0),
                    line=line_number_for_offset(text, m.start()),
                    message="Rule H15: Zero boldface allowed in video_narration prose.",
                )
            )
    elif len(bold_spans) > 4:
        findings.append(
            Finding(
                rule_id="H15_BOLDFACE_OVERUSE",
                severity="MEDIUM",
                category="formatting",
                span=f"{len(bold_spans)} bold spans found",
                line=line_number_for_offset(text, bold_spans[0].start()),
                message="Rule H15 (blader/humanizer #15): Mechanical boldface overuse (>4 bold spans in prose).",
            )
        )

    for idx, line in enumerate(lines, start=1):
        # H16: Inline-Header Vertical Lists (`- **Header:** ...` or `* **Header**: ...`)
        m_list = re.match(r"^\s*(?:[-*+]|\d+\.)\s+\*\*[^*]+\*\*\s*[:—-]", line)
        if m_list:
            findings.append(
                Finding(
                    rule_id="H16_INLINE_HEADER_LIST",
                    severity="SEVERE",
                    category="formatting",
                    span=line.strip()[:80],
                    line=idx,
                    message="Rule H16 (blader/humanizer #16): Inline-header vertical list ('- **Header:** ...'). Rewrite as prose or plain bullets.",
                )
            )

        # H17: Title Case in Headings
        m_head = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if m_head:
            heading_text = m_head.group(2).strip()
            words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", heading_text)
            if len(words) >= 3:
                non_initial = words[1:]
                content_words = [w for w in non_initial if w.lower() not in MINOR_TITLE_WORDS]
                unexplained_caps = [
                    w for w in content_words
                    if w[0].isupper() and not w.isupper() and w not in receipt_capitalized
                ]
                if len(content_words) >= 2 and len(unexplained_caps) / len(content_words) >= 0.6:
                    findings.append(
                        Finding(
                            rule_id="H17_TITLE_CASE_HEADING",
                            severity="MEDIUM",
                            category="formatting",
                            span=line.strip(),
                            line=idx,
                            message="Rule H17 (blader/humanizer #17): Heading uses Title Case. Convert to sentence case.",
                        )
                    )

        # H18: Emojis
        for m_emo in EMOJI_RE.finditer(line):
            emo = m_emo.group(0)
            if emo not in receipts_text:
                findings.append(
                    Finding(
                        rule_id="H18_EMOJI_DECORATION",
                        severity="SEVERE",
                        category="formatting",
                        span=emo,
                        line=idx,
                        message="Rule H18 (blader/humanizer #18): Decorative emoji found in prose/heading.",
                    )
                )

    return findings


def scan_h11_synonym_cycling(text: str) -> list[Finding]:
    """Heuristic detector for H11 (blader/humanizer #11): Repeated 'The <adj> <role/epithet>' subject openers."""
    findings: list[Finding] = []
    epithet_re = re.compile(
        r"(?:^|[.!?]\s+)(The\s+(?:[a-z]+-[a-z]+\s+|[a-z]+\s+){1,2}"
        r"(?:protagonist|central figure|visionary|pioneer|mogul|giant|titan|behemoth|stalwart|vocalist|executive|architect|trailblazer))\b",
        re.IGNORECASE,
    )
    for m in epithet_re.finditer(text):
        findings.append(
            Finding(
                rule_id="H11_SYNONYM_CYCLING",
                severity="MEDIUM",
                category="language",
                span=m.group(1),
                line=line_number_for_offset(text, m.start()),
                message="Rule H11 (blader/humanizer #11): Thesaurus epithet / synonym cycling ('The <adj> figure/giant/mogul'). Use the plain name or pronoun.",
            )
        )
    return findings


def scan_h25_conclusions(text: str) -> list[Finding]:
    """Scan the final 25% of the document (and full text for extreme clichés) for H25 generic upbeat endings."""
    findings: list[Finding] = []
    cutoff = max(0, int(len(text) * 0.70))
    tail_text = text[cutoff:]
    for pat in H25_CONCLUSION_PATTERNS:
        for m in re.finditer(pat, tail_text, flags=re.IGNORECASE):
            abs_pos = cutoff + m.start()
            findings.append(
                Finding(
                    rule_id="H25_GENERIC_POSITIVE_CONCLUSION",
                    severity="SEVERE",
                    category="conclusion",
                    span=m.group(0),
                    line=line_number_for_offset(text, abs_pos),
                    message="Rule H25 (blader/humanizer #25): Generic positive/horizon conclusion cliché. End on a specific verified fact or planned payoff.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Fact & Quote Grounding Gate (Draft vs receipts.md)
# ---------------------------------------------------------------------------

TRIVIAL_NUMBERS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12", "20", "24", "30", "60", "100"}


def normalize_num(token: str) -> str:
    return token.replace(",", "").strip()


def verify_fact_grounding(draft_text: str, receipts_text: str) -> tuple[list[Finding], dict]:
    """Ensure numbers, years, currency amounts, percentages, and verbatim quotes in draft exist in receipts.md."""
    findings: list[Finding] = []
    receipts_norm = receipts_text.replace(",", "")
    receipts_lower = receipts_text.lower()

    # 1. Check numeric tokens (years, percentages, decimals, multi-digit numbers, currency figures)
    num_pattern = re.compile(r"(?:[$€£¥]\s*\d+(?:[.,]\d+)?(?:\s*(?:million|billion|trillion))?|\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?%|\b(?:1[7-9]\d\d|20[0-3]\d)\b|\b\d{2,}\b)", re.IGNORECASE)
    checked_numbers = 0
    unverified_numbers: list[str] = []

    for m in num_pattern.finditer(draft_text):
        raw_tok = m.group(0).strip()
        # Extract core digits
        digits_match = re.search(r"\d+(?:\.\d+)?", normalize_num(raw_tok))
        if not digits_match:
            continue
        core_num = digits_match.group(0)
        if core_num in TRIVIAL_NUMBERS and "%" not in raw_tok and not any(c in raw_tok for c in "$€£¥"):
            continue
        checked_numbers += 1
        # Check if core_num appears as a number token in receipts
        if not re.search(rf"(?<!\d){re.escape(core_num)}(?!\d)", receipts_norm):
            unverified_numbers.append(raw_tok)
            findings.append(
                Finding(
                    rule_id="FACT_UNGROUNDED_NUMBER",
                    severity="SEVERE",
                    category="verification",
                    span=raw_tok,
                    line=line_number_for_offset(draft_text, m.start()),
                    message=f"Number/metric '{raw_tok}' appears in prose but is not grounded in receipts.md.",
                )
            )

    # 2. Check double-quoted verbatim strings (>= 4 words)
    quote_pattern = re.compile(r'"([^"\n]{15,})"|\u201c([^\u201d\n]{15,})\u201d')
    checked_quotes = 0
    unverified_quotes: list[str] = []

    for m in quote_pattern.finditer(draft_text):
        q = (m.group(1) or m.group(2) or "").strip()
        words = q.split()
        if len(words) < 4:
            continue
        checked_quotes += 1
        # Normalize whitespace and punctuation for substring match
        q_clean = re.sub(r"\s+", " ", q).lower().strip(" .,!?;:")
        r_clean = re.sub(r"\s+", " ", receipts_lower)
        if q_clean not in r_clean:
            unverified_quotes.append(q)
            findings.append(
                Finding(
                    rule_id="FACT_UNGROUNDED_QUOTE",
                    severity="SEVERE",
                    category="verification",
                    span=f'"{q[:60]}..."' if len(q) > 60 else f'"{q}"',
                    line=line_number_for_offset(draft_text, m.start()),
                    message="Verbatim quote in prose does not appear in receipts.md.",
                )
            )

    stats = {
        "checked_numbers": checked_numbers,
        "unverified_numbers": len(unverified_numbers),
        "checked_quotes": checked_quotes,
        "unverified_quotes": len(unverified_quotes),
    }
    return findings, stats


# ---------------------------------------------------------------------------
# Receipts Stage Check
# ---------------------------------------------------------------------------

def verify_receipts_file(receipts_text: str) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    urls = re.findall(r"https?://[^\s)>\]\"']+", receipts_text)
    entries = re.findall(r"^###\s+\[R\d+\]", receipts_text, flags=re.MULTILINE)
    if len(urls) < 2:
        findings.append(
            Finding(
                rule_id="RECEIPTS_THIN_SOURCES",
                severity="SEVERE",
                category="research",
                span=f"{len(urls)} URLs found",
                line=1,
                message="receipts.md must contain at least 2 source URLs before drafting.",
            )
        )
    if not entries and len(receipts_text.strip().splitlines()) < 10:
        findings.append(
            Finding(
                rule_id="RECEIPTS_UNSTRUCTURED",
                severity="MEDIUM",
                category="research",
                span="receipts.md",
                line=1,
                message="Prefer structured ### [R01] blocks in receipts.md for clear auditability.",
            )
        )
    return findings, {"urls_count": len(urls), "receipt_blocks": len(entries)}


# ---------------------------------------------------------------------------
# Main Runner & Report Generator
# ---------------------------------------------------------------------------

def build_markdown_report(
    *,
    stage: str,
    passed: bool,
    word_count: int,
    target_words: int | None,
    tolerance_pct: int,
    fact_stats: dict,
    receipt_stats: dict,
    findings: list[Finding],
) -> str:
    status_str = "PASS" if passed else "FAIL"
    severe_cnt = sum(1 for f in findings if f.severity == "SEVERE")
    med_cnt = sum(1 for f in findings if f.severity == "MEDIUM")

    lines = [
        f"# Verification & De-Slop Report (`{status_str}`)",
        "",
        f"- **Stage:** `{stage}`",
        f"- **Overall Gate Status:** **{status_str}** ({severe_cnt} severe, {med_cnt} medium)",
    ]
    if stage == "final":
        if target_words:
            lo = int(target_words * (1 - tolerance_pct / 100.0))
            hi = int(target_words * (1 + tolerance_pct / 100.0))
            lines.append(f"- **Word Count:** `{word_count}` words (target: `{target_words}`, allowed band: `{lo}–{hi}`)")
        else:
            lines.append(f"- **Word Count:** `{word_count}` words")
        lines.append(
            f"- **Fact & Quote Grounding:** `{fact_stats.get('checked_numbers', 0)}` non-trivial numbers checked "
            f"(`{fact_stats.get('unverified_numbers', 0)}` ungrounded); "
            f"`{fact_stats.get('checked_quotes', 0)}` verbatim quotes checked "
            f"(`{fact_stats.get('unverified_quotes', 0)}` ungrounded)"
        )
    lines.append(
        f"- **Sidecar Receipts:** `{receipt_stats.get('urls_count', 0)}` source URLs, "
        f"`{receipt_stats.get('receipt_blocks', 0)}` structured `[Rxx]` blocks"
    )
    lines.append("")

    if not findings:
        lines.extend([
            "## Findings",
            "",
            "Zero defects detected across fact grounding, receipt theater, metaphor/agency rules, and `blader/humanizer` checks (H1, H5, H11, H15–H18, H23, H25).",
            "",
        ])
    else:
        lines.extend([
            "## Findings",
            "",
            "| Severity | Rule ID | Line | Span | Explanation |",
            "| :--- | :--- | ---: | :--- | :--- |",
        ])
        for f in findings:
            safe_span = f.span.replace("|", "\\|").replace("\n", " ")
            safe_msg = f.message.replace("|", "\\|")
            lines.append(f"| **{f.severity}** | `{f.rule_id}` | {f.line} | `{safe_span}` | {safe_msg} |")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic verification & anti-slop gate for verify_and_deslopify.")
    parser.add_argument("run_dir", nargs="?", help="Path to run directory containing brief.yaml, receipts.md, draft_clean.md")
    parser.add_argument("--stage", choices=["receipts", "final"], default="final", help="Verification stage to run (default: final)")
    parser.add_argument("--draft", help="Standalone mode: explicit path to draft markdown/text file")
    parser.add_argument("--receipts", help="Standalone mode: explicit path to receipts.md file")
    parser.add_argument("--brief", help="Standalone mode: explicit path to brief.yaml file")
    parser.add_argument("--json", action="store_true", help="Also emit JSON summary to stdout")
    args = parser.parse_args()

    if not args.run_dir and not args.draft and not args.receipts:
        parser.error("Provide either <run_dir> or --draft / --receipts.")

    run_path = Path(args.run_dir).expanduser().resolve() if args.run_dir else None
    brief_path = Path(args.brief).expanduser().resolve() if args.brief else (run_path / "brief.yaml" if run_path else None)
    receipts_path = Path(args.receipts).expanduser().resolve() if args.receipts else (run_path / "receipts.md" if run_path else None)

    if args.draft:
        draft_path = Path(args.draft).expanduser().resolve()
    elif run_path:
        candidates = [
            run_path / "draft_clean.md",
            run_path / "draft.clean.md",  # legacy alias
            run_path / "narration.voice_strip.md",
            run_path / "draft.md",
        ]
        draft_path = next((p for p in candidates if p.exists()), candidates[0])
    else:
        draft_path = None

    brief = parse_simple_yaml(brief_path) if brief_path and brief_path.exists() else {}
    findings: list[Finding] = []
    receipt_stats = {"urls_count": 0, "receipt_blocks": 0}
    fact_stats = {"checked_numbers": 0, "unverified_numbers": 0, "checked_quotes": 0, "unverified_quotes": 0}

    # Check receipts.md
    receipts_text = ""
    if receipts_path and receipts_path.exists():
        receipts_text = receipts_path.read_text(encoding="utf-8")
        r_findings, receipt_stats = verify_receipts_file(receipts_text)
        findings.extend(r_findings)
    elif args.stage == "receipts":
        print(f"ERROR: receipts.md not found at {receipts_path}", file=sys.stderr)
        return 2

    if args.stage == "receipts":
        passed = not any(f.severity == "SEVERE" for f in findings)
        report_md = build_markdown_report(
            stage="receipts",
            passed=passed,
            word_count=0,
            target_words=None,
            tolerance_pct=10,
            fact_stats=fact_stats,
            receipt_stats=receipt_stats,
            findings=findings,
        )
        print(report_md)
        return 0 if passed else 1

    # Stage == final
    if not draft_path or not draft_path.exists():
        print(f"ERROR: Draft file not found at {draft_path}", file=sys.stderr)
        return 2

    draft_text = draft_path.read_text(encoding="utf-8")
    words = re.findall(r"\b[\w'-]+\b", draft_text)
    word_count = len(words)
    target_words = brief.get("target_word_count")
    tolerance_pct = int(brief.get("tolerance_pct", 10))

    # 1. Word count contract
    if isinstance(target_words, int) and target_words > 0:
        lo = int(target_words * (1 - tolerance_pct / 100.0))
        hi = int(target_words * (1 + tolerance_pct / 100.0))
        if word_count < int(target_words * 0.5):
            findings.append(
                Finding(
                    rule_id="LEN_CRITICALLY_SHORT",
                    severity="SEVERE",
                    category="length",
                    span=f"{word_count} words",
                    line=1,
                    message=f"Draft is {word_count} words (<50% of target {target_words}).",
                )
            )
        elif word_count < lo or word_count > hi:
            findings.append(
                Finding(
                    rule_id="LEN_OUT_OF_BAND",
                    severity="MEDIUM",
                    category="length",
                    span=f"{word_count} words",
                    line=1,
                    message=f"Word count {word_count} is outside ±{tolerance_pct}% band ({lo}–{hi} words).",
                )
            )

    # 2. Check strip_report.md exists when running on a run_dir
    if run_path:
        strip_rep = run_path / "strip_report.md"
        legacy_rep = run_path / "voice_strip_report.md"
        active_rep = strip_rep if strip_rep.exists() else (legacy_rep if legacy_rep.exists() else None)
        if not active_rep:
            findings.append(
                Finding(
                    rule_id="MISSING_STRIP_REPORT",
                    severity="SEVERE",
                    category="contract",
                    span="strip_report.md",
                    line=1,
                    message="Stage 4 strip_report.md is missing. Every run must log its de-slop edits.",
                )
            )
        elif "|" not in active_rep.read_text(encoding="utf-8"):
            findings.append(
                Finding(
                    rule_id="EMPTY_STRIP_REPORT",
                    severity="MEDIUM",
                    category="contract",
                    span=active_rep.name,
                    line=1,
                    message="strip_report.md does not contain a markdown diff table of changes.",
                )
            )

    # 3. Fact & Quote Grounding against receipts.md
    if receipts_text.strip():
        f_ground, fact_stats = verify_fact_grounding(draft_text, receipts_text)
        findings.extend(f_ground)

    # 4. M1 & M3 Scanners (Invented Agency & Receipt Theater)
    findings.extend(
        scan_regex_list(
            draft_text,
            INVENTED_AGENCY_PATTERNS,
            rule_id="M1_INVENTED_AGENCY",
            severity="SEVERE",
            category="metaphor",
            message="Rule M1: Invented agency or banned figurative cliché. Literalize who did what.",
        )
    )
    citation_mode = str(brief.get("citation_mode", "none")).strip().lower()
    # Legacy boolean from earlier skill versions
    if brief.get("inline_citations") is True and citation_mode in {"", "none", "false"}:
        citation_mode = "external_links"
    if citation_mode not in {"none", "end_references", "external_links"}:
        findings.append(
            Finding(
                rule_id="BAD_CITATION_MODE",
                severity="SEVERE",
                category="contract",
                span=citation_mode,
                line=1,
                message="citation_mode must be one of: none | end_references | external_links",
            )
        )
        citation_mode = "none"

    # Receipt-theater phrases are always banned; only marker/URL style depends on citation_mode.
    findings.extend(
        scan_regex_list(
            draft_text,
            RECEIPT_THEATER_PATTERNS,
            rule_id="M3_RECEIPT_THEATER",
            severity="SEVERE",
            category="epistemic",
            message="Rule M3: Receipt theater in prose. Keep verification language inside receipts.md.",
        )
    )
    if citation_mode == "none":
        for m in re.finditer(r"https?://\S+", draft_text):
            findings.append(
                Finding(
                    rule_id="URL_IN_PROSE_SIDECAR_MODE",
                    severity="MEDIUM",
                    category="citation",
                    span=m.group(0)[:80],
                    line=line_number_for_offset(draft_text, m.start()),
                    message="citation_mode=none: URLs belong in receipts.md (or switch to external_links / end_references).",
                )
            )
    elif citation_mode == "end_references":
        if not re.search(r"^##\s+References\s*$", draft_text, flags=re.MULTILINE | re.IGNORECASE):
            findings.append(
                Finding(
                    rule_id="MISSING_REFERENCES_SECTION",
                    severity="SEVERE",
                    category="citation",
                    span="## References",
                    line=1,
                    message="citation_mode=end_references requires a final '## References' section.",
                )
            )
        if not re.search(r"\[\d+\]|\[R\d+\]", draft_text):
            findings.append(
                Finding(
                    rule_id="MISSING_END_REFERENCE_MARKERS",
                    severity="MEDIUM",
                    category="citation",
                    span="[1] / [R01]",
                    line=1,
                    message="citation_mode=end_references expected in-prose markers like [1] or [R01].",
                )
            )

    # 5. blader/humanizer Targeted Scanners (H1, H5, H11, H15-H18, H23, H25)
    findings.extend(
        scan_regex_list(
            draft_text,
            H1_SIGNIFICANCE_PATTERNS,
            rule_id="H1_SIGNIFICANCE_INFLATION",
            severity="SEVERE",
            category="content",
            message="Rule H1 (blader/humanizer #1): Significance/legacy inflation or superficial -ing analysis.",
        )
    )
    findings.extend(
        scan_regex_list(
            draft_text,
            H5_WEASEL_PATTERNS,
            rule_id="H5_WEASEL_ATTRIBUTION",
            severity="SEVERE",
            category="attribution",
            message="Rule H5 (blader/humanizer #5): Vague weasel attribution ('experts argue', 'observers note'). Name the source or state the fact.",
        )
    )
    findings.extend(scan_h11_synonym_cycling(draft_text))
    findings.extend(scan_formatting_and_style(draft_text, brief, receipts_text))

    for pat, msg in H23_FILLER_PATTERNS:
        findings.extend(
            scan_regex_list(
                draft_text,
                [pat],
                rule_id="H23_FILLER_PHRASE",
                severity="SEVERE",
                category="filler",
                message=f"Rule H23 (blader/humanizer #23): {msg}",
            )
        )

    findings.extend(scan_h25_conclusions(draft_text))

    # 6. Vendor residue
    findings.extend(
        scan_regex_list(
            draft_text,
            RESIDUE_PATTERNS,
            rule_id="VENDOR_RESIDUE",
            severity="SEVERE",
            category="residue",
            message="Vendor citation residue or tracking parameter left in prose.",
        )
    )

    passed = not any(f.severity == "SEVERE" for f in findings)
    report_md = build_markdown_report(
        stage="final",
        passed=passed,
        word_count=word_count,
        target_words=target_words if isinstance(target_words, int) else None,
        tolerance_pct=tolerance_pct,
        fact_stats=fact_stats,
        receipt_stats=receipt_stats,
        findings=findings,
    )

    if run_path:
        (run_path / "verification_report.md").write_text(report_md, encoding="utf-8")

    if args.json:
        print(
            json.dumps(
                {
                    "passed": passed,
                    "word_count": word_count,
                    "target_word_count": target_words,
                    "fact_stats": fact_stats,
                    "receipt_stats": receipt_stats,
                    "findings": [asdict(f) for f in findings],
                },
                indent=2,
            )
        )
    else:
        print(report_md)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
