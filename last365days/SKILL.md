---
name: last365days
description: >-
  Use when the user wants long-term tracking for a person, brand, or topic,
  asks for a research timeline or persistent profile, or invokes "last365 ..."
  to save repeated research into dated history files.
---

# last365days v1.2.0: Persistent Research Tracker

Same deep research as the bundled `scripts/last30days.py` engine — Reddit, X, YouTube, TikTok, Instagram, HN, Polymarket, web — but every run is saved to a per-person/topic MD file. Over time you build a running timeline: what changed, what's new, how far they've come.

Research folder: `~/Desktop/last365days/`

## Requirements

This skill is standalone. The research engine is bundled in
`${CLAUDE_SKILL_DIR}/scripts/last30days.py`, and source stats are read from
`~/.local/share/last365days/out/report.json` by default.

X/Twitter behavior is handled by the bundled engine. Bird auth remains
Safari-first when available, with fallback handled inside the bundled stack.

Optional: if `qmd` is installed in the host environment, you can refresh your
knowledge index after a run with:

```bash
command -v qmd >/dev/null 2>&1 && qmd update >> /dev/null 2>&1 || true
```

If you need browse, export, or troubleshooting workflows, load
`references/operations.md`. Do not load it for the normal research path unless
the user asks for those tasks.

## Existing Profiles

To inspect the existing profile list at the start of the workflow, run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py list
```

---

## File Format Convention

Each profile is a Markdown file with dated `## YYYY-MM-DD` sections containing `### Synthesis`, `### Sources`, and `### Notable Items`. See `references/file-format.md` for the full specification and same-day entry handling.

---

## STEP 0: Parse Intent + Check History

The user's raw topic is the exact text they provided after invoking
`last365days`.

If the user did not provide a topic, they are asking to browse profiles rather
than run new research. In that case, stop here and list profiles:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py list
```

Show the result to the user and do not continue into matching, research, or
persistence.

Parse that raw topic into:

- **TOPIC**: the main person, brand, product, or idea being researched
- **QUERY_TYPE**:
  - `recommendations` for "best", "top", "alternatives", or shortlist requests
  - `news` for "latest", "what changed", "update", or recent-event requests
  - `prompting` for prompt examples, prompt templates, or AI workflow requests
  - `general` for everything else

The profile list above shows what already exists. Now run a targeted match:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py match "<RAW_TOPIC>"
```

Substitute the concrete raw topic string from the user in place of
`<RAW_TOPIC>`. Do not pass the literal placeholder.

This returns:
- `matches`: existing profiles with confidence levels (exact/high/medium)
- `suggested_slug`: what the filename would be if creating new
- `total_profiles`: how many profiles exist

### Matching rules

Always tell the user which file you're writing to. Never match or create
silently.

- `"confidence": "exact"` or `"high"` — Use the existing profile. Tell the
  user: "Found existing profile: `{slug}.md` ({N} entries, last updated
  {date}). Appending to it."
- `"confidence": "medium"` — Never append automatically. First read the file:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py read "<slug>"
```

After reading the file, follow this confirmation flow:

1. If the content is clearly a different person or topic, create a new profile
   and tell the user why.
2. If the content still looks plausible but you are not fully certain, ask the
   user to choose before continuing.
3. Only append to the existing profile if the user explicitly confirms it.

Use direct language when asking. Name both options so the user can make a clean
decision. For example:

```
I found a possible existing profile: {slug}.md ({N} entries, last updated {date}).
It looks related, but I am not confident enough to append automatically.

Do you want me to:
1. Use {slug}.md
2. Create a new profile: {suggested_slug}.md
```

If the user declines, is unsure, or gives an ambiguous answer, create a new
profile. Do not risk corrupting an existing timeline.

- **No matches** — Tell the user: "No existing profile found. Creating
  `{slug}.md`."

When in doubt, create a new profile. It is better to have two separate files
than to corrupt one with unrelated research. The user can merge them later.

**If there IS a match with history**, load context for comparison:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py history "<slug>"
```

Display to the user:

```
I'll research {TOPIC} across Reddit, X, YouTube, TikTok, and the web.

Parsed intent:
- TOPIC = {TOPIC}
- QUERY_TYPE = {QUERY_TYPE}
- Existing profile: {slug}.md ({N} entries, last updated {date})

Research typically takes 2-8 minutes. Starting now.
```

If creating new:

```
I'll research {TOPIC} across Reddit, X, YouTube, TikTok, and the web.

Parsed intent:
- TOPIC = {TOPIC}
- QUERY_TYPE = {QUERY_TYPE}
- Profile: new — will create {slug}.md

Research typically takes 2-8 minutes. Starting now.
```

---

## STEP 1: Resolve X Handle (if applicable)

If the topic could have an X account (person, brand, company), do a quick
WebSearch to find their handle:

```
WebSearch("{TOPIC} X twitter handle site:x.com")
```

If you find a verified handle, pass it as `--x-handle={handle}` in the research script. Skip for generic concepts.

---

## STEP 2: Run Research

Run the bundled research engine. Research quality and depth stay the same.

**Flag forwarding**: If the user includes any of these flags, pass them through to the research script:
- `--days=N` — override the default 30-day window (e.g., `--days=7` for a quick weekly check)
- `--quick` — faster research with fewer sources (triggered by "quick check", "quick look")
- `--deep` — thorough research with more sources (triggered by "deep dive", "deep research")
- `--x-handle=HANDLE` — from STEP 1 if an X handle was resolved

```bash
LAST30DAYS_OUTPUT_DIR="${LAST365DAYS_OUTPUT_DIR:-$HOME/.local/share/last365days/out}" \
LAST30DAYS_CACHE_DIR="${LAST365DAYS_CACHE_DIR:-$HOME/.cache/last365days}" \
LAST30DAYS_CONFIG_DIR="${LAST365DAYS_CONFIG_DIR:-$HOME/.config/last365days}" \
python3 "${CLAUDE_SKILL_DIR}/scripts/last30days.py" "<TOPIC>" --emit=compact --no-native-web
```

Run the same command with the real parsed topic text in place of the final
argument. Append any resolved flags (`--x-handle`, `--days`, `--quick`,
`--deep`) to that command.

Use a **timeout of 300000** (5 minutes). Read the ENTIRE output — it contains all 8 data sections.

---

## STEP 3: WebSearch Supplement

After the script finishes, do WebSearch to supplement the script output:

- **RECOMMENDATIONS**: search for "best {TOPIC} recommendations", "{TOPIC} list examples"
- **NEWS**: search for "{TOPIC} news", "{TOPIC} announcement update"
- **PROMPTING**: search for "{TOPIC} prompts examples"
- **GENERAL**: search for "{TOPIC}", "{TOPIC} discussion"

Exclude reddit.com, x.com, twitter.com (covered by script).

---

## STEP 4: Synthesize + Present

Synthesize across the script output and the WebSearch supplement using these
rules:

1. Weight Reddit/X higher (engagement signals), YouTube/TikTok high (views + transcripts), web lower
2. Cross-platform signals are strongest
3. Polymarket odds are high-signal — real money on outcomes
4. Cite sources: prefer @handles > r/subs > YouTube channels > TikTok > Instagram > HN > Polymarket > web
5. Present the result in this order:
   - optional `What changed since {last_date}` section when history exists
   - `What I learned`
   - `Key patterns`
   - source stats block
   - short invitation for the next step

**CRITICAL ADDITION — What Changed (if history exists):**

If this person/topic has previous entries, read the most recent entry's synthesis and add a "What Changed" section BEFORE "What I learned":

```
**What changed since {last_date}:**
- [New development not in previous entries]
- [Shift in public sentiment or narrative]
- [New milestones, numbers, or events]
- [Things that stayed the same / are still true]
```

Ground this comparison in the ACTUAL content of the previous entries vs the new research. Don't make things up. If you can't meaningfully compare (e.g., previous entry was too sparse), say so and skip the section.

Then present the final response using this structure:

```markdown
**What I learned**
- 3-6 specific findings grounded in the evidence

**Key patterns**
- 2-4 cross-platform patterns, themes, or repeated signals

**Source stats**
- Brief platform summary using the report and notable items
```

For `recommendations`, bias the findings toward concrete picks and trade-offs.
For `news`, bias toward what is new or changed. For `prompting`, bias toward
useful prompt structures and workflow takeaways.

---

## STEP 5: Persist Results

After presenting to the user, save the research. Write your synthesis text (the "What I learned" section including key patterns) and pipe it into persist.py:

```bash
cat << 'SYNTHESIS_EOF' | python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py append "<SLUG>" --title "<Display Name>"
YOUR FULL SYNTHESIS TEXT HERE
Include the "What I learned" section.
Include KEY PATTERNS.
If there was a "What Changed" section, include that too.
Do NOT include the stats block (persist.py adds stats from report.json automatically).
SYNTHESIS_EOF
```

persist.py will:
- Create `~/Desktop/last365days/<slug>.md` if new, or append to existing
- Add a dated section header (`## YYYY-MM-DD`)
- Handle same-day runs (sub-entries under the same date)
- Include your synthesis under `### Synthesis`
- Pull source statistics from `~/.local/share/last365days/out/report.json` automatically
- Validate that report.json matches the topic before pulling stats
- Add top sources by engagement

**After persisting**, tell the user:

```
Saved to ~/Desktop/last365days/<slug>.md (<N> entries total)
```

---

## STEP 6: Invitation

End with 2-3 specific next-step suggestions based on `QUERY_TYPE`:

- `recommendations`: offer a shortlist, comparison table, or opinionated picks
- `news`: offer a timeline, change summary, or watchlist
- `prompting`: offer copy-paste prompts, tool-specific variants, or a prompt
  pack
- `general`: offer a deeper dive, a comparison with another topic, or a saved
  follow-up later

**Additional suggestions for profiles with history:**
- "Compare how things have changed since [earliest date]"
- "Show me the full timeline for [person]"

---

## Additional operations

If the user asks to browse profiles, export data, diff two saved dates, or
debug an installation problem, read `references/operations.md` and follow the
matching workflow there.

---

## Context Memory

After research, answer follow-ups from memory. Do not re-run research unless the
user asks about a different topic or explicitly wants a fresh update.

**Additional context**: You also have access to the person's full research history via the profile file. Reference it when answering follow-ups about trends or changes over time.

---

## Security & Permissions

This skill additionally:
- Writes MD files to `~/Desktop/last365days/` (user-visible, human-readable)
- Reads `~/.local/share/last365days/out/report.json` for source statistics
- Does not transmit profile data to any external service
