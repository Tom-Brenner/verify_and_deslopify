# Style, Metaphor & Anti-Slop Reference (`verify_and_deslopify`)

This reference defines the exact defect taxonomy for Stage 3 (Voice-First Draft), Stage 4 (Literalize & De-Slop), and Stage 5 (`scripts/verify_run.py`).

Rules **M1–M3** originate from the sidecar-sourced narrative workflow (`meltdown_vo` / `voice_first` / `voice_strip`).
Rules **H1, H5, H11, H15–H18, H23, and H25** are adapted and extended from [`blader/humanizer`](https://github.com/blader/humanizer) (MIT License, grounded in WikiProject AI Cleanup's *Wikipedia:Signs of AI writing*).

---

## 1. Metaphor, Agency & Epistemic Hygiene (`M1–M3`)

### M1. Invented Agency & Non-Idiomatic Imagery (`invented_agency`) — SEVERE
**The problem:** LLMs try to sound "literary" or punchy by making abstract nouns, corporate entities, financial instruments, or body parts perform physical actions that never happened.
**Ban list:**
- Words or quotes positioned physically (*"the word Reuters put near his mouth"*)
- Empires, catalogs, brands, or balance sheets walking, bleeding, breathing, keeping keys, or deciding someone is *"useful inventory"*
- Weather/atmosphere/oxygen metaphors for popularity or money (*"writes the weather"*, *"losing the chart feels like losing oxygen"*, *"sharing oxygen"*)
- Cold opens that rely on figurative scene-setting instead of a concrete date, place, person, and action.

| Bad (Invented Agency / Metaphor) | Good (Literalized Fact + Tone) |
| :--- | :--- |
| *"The bleach-blond empire walks into custody."* | *"Cameras follow him into custody."* |
| *"Kyodo and Reuters both put the word near his mouth."* | *"Kyodo and Reuters both quoted him saying it."* |
| *"A balance sheet deciding a human being was still useful inventory."* | *"The label still needed his catalog to pay off its debt."* |
| *"Until the song feels like weather."* | *"Until you could not walk through a mall in 1984 without hearing it."* |

### M2. Stacked Metaphors & Clever Replacements (`stacked_metaphor`) — MEDIUM / SEVERE
**The problem:** When asked to edit, LLMs often swap one strained metaphor for another ("thrift-store armor" → "neon battle gear").
**Rules:**
1. Prefer **zero** metaphors.
2. Never put two figurative images in the same paragraph.
3. During the de-slop pass, **never replace a bad metaphor with a cleverer one**—delete the image and keep the literal who/what/when/number.

### M3. Receipt Theater in Prose (`receipt_theater`) — SEVERE
**The problem:** When an agent researches facts before writing, it gets anxious to prove to the reader that it did the homework. It litters the prose with compliance language.
**Banned phrases in prose:**
- *"the record shows"*, *"as the record reflects"*, *"public records confirm"*
- *"as documented in"*, *"according to multiple sources"*, *"verified reports indicate"*
- *"as proof"*, *"the evidence is clear"*, *"fact-checkers note"*
- Naming 3–4 outlets in a sentence just to prove notability (*"covered by the NYT, BBC, and Reuters"*) when the outlet is not an actor in the story.

**The Sidecar Rule:** Put the URL, date, and verbatim quote in `receipts.md`. In the prose, state the verified fact directly. Name an outlet in prose **only** when the publication or broadcast itself triggered the next event (e.g., *"After Weekly Bunshun published the hotel photos on Wednesday, the sponsor pulled its ads by Friday"*).

---

## 2. Content & Attribution Defects (`H1, H5`)

### H1. Undue Emphasis on Significance, Legacy & Broader Trends (`significance_inflation`) — SEVERE
*(Adapted from `blader/humanizer` #1)*
**The problem:** LLMs puff up ordinary facts by tacking on claims about how they "mark a pivotal moment," "stand as a testament," or "reflect broader trends in an evolving landscape."
**Banned phrases / patterns:**
- `stands as a`, `serves as a`, `is a testament to`, `is a stark reminder`
- `plays a vital/significant/crucial/pivotal/key role`
- `underscores/highlights its importance/significance`
- `reflects broader trends`, `symbolizing its ongoing/enduring/lasting`
- `marks a pivotal moment`, `key turning point`, `evolving landscape`, `indelible mark`, `deeply rooted`, `setting the stage for`
- Tacked-on `-ing` participial tails that fake analysis (`...highlighting the intricate interplay between X and Y`, `...underscoring the need for...`).

| Bad | Good |
| :--- | :--- |
| *"The 1989 audit marked a pivotal moment in the evolution of regional accounting, underscoring the vital role of transparency."* | *"The 1989 audit exposed $14 million in off-book loans and forced the board to resign."* |

### H5. Vague Attributions & Weasel Authority (`weasel_attribution`) — SEVERE
*(Adapted from `blader/humanizer` #5)*
**The problem:** Attributing claims to nameless authorities instead of citing the specific source from `receipts.md` or cutting the claim.
**Banned phrases:**
- `industry reports suggest/indicate`, `observers have cited/noted`
- `experts argue/believe/agree`, `some critics argue/claim`
- `many analysts believe`, `studies show` (without naming the study/year)
- `several sources/publications` (when `receipts.md` has the exact source)

| Bad | Good |
| :--- | :--- |
| *"Industry observers noted that the chip ran too hot, and critics argued the launch was rushed."* | *"AnandTech's October benchmark measured the chip at 98°C under load, and two lead thermal engineers had quit three months before launch."* |

---

## 3. Language & Formatting Hygiene (`H11, H15–H18`)

### H11. Elegant Variation / Synonym Cycling (`synonym_cycling`) — MEDIUM
*(Adapted from `blader/humanizer` #11)*
**The problem:** Repetition-penalty habits cause models to invent a new epithet for the same subject in every sentence (*"the singer... the Queens-born vocalist... the neon-haired icon... the central figure"* or *"the database... the storage engine... the relational powerhouse"*).
**Rule:** Pick the plain name or noun and stick to it, or use `he / she / they / it`. Never cycle through 3+ descriptive noun phrases for the same entity in one paragraph.

### H15. Overuse of Boldface (`boldface_overuse`) — MEDIUM / SEVERE
*(Adapted from `blader/humanizer` #15)*
**The problem:** LLMs mechanically wrap keywords, acronyms, and mid-sentence phrases in `**bold**` as if writing a study guide.
**Rules:**
- In `video_narration` format: **0 boldface spans** allowed in the prose body.
- In `longform_article` / `case_study` / `memo`: Do not bold mid-sentence phrases or acronym expansions (`**OKRs (Objectives and Key Results)**`).

### H16. Inline-Header Vertical Lists (`inline_header_list`) — SEVERE
*(Adapted from `blader/humanizer` #16)*
**The problem:** LLMs love outputting bulleted lists where every bullet starts with a bolded noun phrase and a colon:
```markdown
- **Speed:** Speed was improved by rewriting the parser.
- **Cost:** Cost dropped by 40% after moving off AWS.
```
**Rule:** Ban `- **Header:**` bullet lists in narrative/article prose. Turn them into normal sentences with real transitions, or (if a list is genuinely needed in a technical memo) write plain bullets without bolded label prefixes.

### H17. Title Case in Headings (`title_case_heading`) — MEDIUM
*(Adapted from `blader/humanizer` #17)*
**The problem:** AI defaults to capitalizing every major word in Markdown headings (`## Strategic Negotiations And Global Partnerships`).
**Rule:** Always use **sentence case** for headings (`## Strategic negotiations and global partnerships`), capitalizing only the first word and proper nouns/acronyms recorded in `receipts.md`.

### H18. Decorative Emojis (`emoji_decoration`) — SEVERE
*(Adapted from `blader/humanizer` #18)*
**The problem:** Decorating headings, callouts, or bullet points with emojis (`🚀`, `💡`, `✅`, `⚠️`, `🎯`).
**Rule:** Strip all emojis from headings, lists, and prose unless quoting a literal social media post verbatim from `receipts.md`.

---

## 4. Filler & Ending Verification (`H23, H25`)

Both **H23** and **H25** are enforced in Stage 4 *and* deterministically scanned by `scripts/verify_run.py` in Stage 5.

### H23. Filler Phrases & Epistemic Throat-Clearing (`filler_phrase`) — SEVERE
*(Adapted from `blader/humanizer` #23 + spoken VO rules)*
**The problem:** Padding sentences with bureaucratic prepositional chains or conversational throat-clearing.
**Deterministic replacements:**
- `"in order to"` → `"to"`
- `"due to the fact that"` / `"owing to the fact that"` → `"because"`
- `"at this point in time"` / `"at the present time"` → `"now"`
- `"in the event that"` → `"if"`
- `"has the ability to"` / `"is able to"` → `"can"`
- `"it is important to note that"` / `"it is worth noting that"` / `"it bears mentioning that"` → *delete entirely; state the fact*
- `"here's the thing"` / `"let's unpack this"` / `"let's dive in"` / `"without further ado"` / `"at its core"` / `"the real question is"` → *delete entirely*

### H25. Generic Positive Conclusions (`generic_positive_conclusion`) — SEVERE
*(Adapted from `blader/humanizer` #25)*
**The problem:** When an LLM finishes a draft, RLHF training pulls it toward a warm, upbeat, horoscope-style wrap-up—even at the end of a disaster post-mortem or critical investigation.
**Banned closing patterns (scanned in final 20% of text):**
- `"the future looks bright"`, `"exciting times lie ahead"`
- `"journey toward excellence"`, `"a major step in the right direction"`
- `"continues to thrive"`, `"poised for continued success"`
- `"only time will tell"`, `"remains to be seen how this will shape the future"`
- `"ultimately, the story of X reminds us that..."`

**Rule:** Every piece must end on its planned payoff from `plan.md`: a specific dated fact, a concrete cost/outcome from `receipts.md`, or a dry situational callback to the opening hook.
