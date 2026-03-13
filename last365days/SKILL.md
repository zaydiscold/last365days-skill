---
name: last365days
description: >-
  Persistent research tracker. Runs the same deep research as /last30days
  but saves a running per-person/topic log to ~/Desktop/last365days/.
  Each run appends a dated section — over time you build a timeline of how
  a person or topic evolves. Use when user says "last365", "last365days",
  "track over time", "research timeline", "persistent research", "build a
  profile", or wants long-term monitoring of a person, brand, or topic.
  Also triggered by "last365 <name>".
license: MIT
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
compatibility: >-
  Requires the last30days skill (provides the research engine).
  Optional: qmd for knowledge-base indexing.
  Supported runtimes: Claude Code, Codex, Cursor, OpenClaw.
  Uses CLAUDE_SKILL_DIR or CLAUDE_PLUGIN_ROOT for script paths.
metadata:
  author: zayd
  version: 1.1.0
  repository: https://github.com/zaydiscold/last365days-skill
user-invocable: true
argument-hint: 'last365 Saba Nafees, last365 kanye west, last365 AI video tools'
hooks:
  after:
    - type: command
      command: "command -v qmd >/dev/null 2>&1 && qmd update >> /dev/null 2>&1 || true"
---

# last365days v1.1: Persistent Research Tracker

Same deep research as `/last30days` — Reddit, X, YouTube, TikTok, Instagram, HN, Polymarket, web — but every run is saved to a per-person/topic MD file. Over time you build a running timeline: what changed, what's new, how far they've come.

Research folder: `~/Desktop/last365days/`

## Existing Profiles

!`python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py list`

---

## File Format Convention

Each profile is a Markdown file with dated `## YYYY-MM-DD` sections containing `### Synthesis`, `### Sources`, and `### Notable Items`. See `references/file-format.md` for the full specification and same-day entry handling.

---

## STEP 0: Parse Intent + Check History

The user's topic is: $ARGUMENTS

If `$ARGUMENTS` is empty, the user is asking to browse profiles rather than run
new research. In that case, stop here and list profiles:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py list
```

Show the result to the user and do not continue into matching, research, or
persistence.

Parse this for **TOPIC** (and optionally TARGET_TOOL, QUERY_TYPE) exactly as `/last30days` does.

The profile list above shows what already exists. Now run a targeted match:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py match "$ARGUMENTS"
```

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

Same as `/last30days`: if the topic could have an X account (person, brand, company), do a quick WebSearch to find their handle:

```
WebSearch("{TOPIC} X twitter handle site:x.com")
```

If you find a verified handle, pass it as `--x-handle={handle}` in the research script. Skip for generic concepts.

---

## STEP 2: Run Research

Run the Last 30 Days research engine. This is the same script — nothing changes about the research quality or depth.

**Flag forwarding**: If the user includes any of these flags, pass them through to the research script:
- `--days=N` — override the default 30-day window (e.g., `--days=7` for a quick weekly check)
- `--quick` — faster research with fewer sources (triggered by "quick check", "quick look")
- `--deep` — thorough research with more sources (triggered by "deep dive", "deep research")
- `--x-handle=HANDLE` — from STEP 1 if an X handle was resolved

```bash
for dir in \
  "." \
  "${CLAUDE_PLUGIN_ROOT:-}" \
  "$HOME/.claude/skills/last30days" \
  "$HOME/.agents/skills/last30days" \
  "$HOME/.codex/skills/last30days"; do
  [ -n "$dir" ] && [ -f "$dir/scripts/last30days.py" ] && SKILL_ROOT="$dir" && break
done

if [ -z "${SKILL_ROOT:-}" ]; then
  echo "ERROR: Could not find last30days research engine" >&2
  exit 1
fi

python3 "${SKILL_ROOT}/scripts/last30days.py" "$ARGUMENTS" --emit=compact --no-native-web
```

Append any resolved flags (`--x-handle`, `--days`, `--quick`, `--deep`) to the command above.

Use a **timeout of 300000** (5 minutes). Read the ENTIRE output — it contains all 8 data sections.

---

## STEP 3: WebSearch Supplement

After the script finishes, do WebSearch to supplement — same rules as `/last30days`:

- **RECOMMENDATIONS**: search for "best {TOPIC} recommendations", "{TOPIC} list examples"
- **NEWS**: search for "{TOPIC} news 2026", "{TOPIC} announcement update"
- **PROMPTING**: search for "{TOPIC} prompts examples 2026"
- **GENERAL**: search for "{TOPIC} 2026", "{TOPIC} discussion"

Exclude reddit.com, x.com, twitter.com (covered by script).

---

## STEP 4: Synthesize + Present

Follow the same synthesis rules as `/last30days`:

1. Weight Reddit/X higher (engagement signals), YouTube/TikTok high (views + transcripts), web lower
2. Cross-platform signals are strongest
3. Polymarket odds are high-signal — real money on outcomes
4. Cite sources: prefer @handles > r/subs > YouTube channels > TikTok > Instagram > HN > Polymarket > web
5. Use the same "What I learned" format, KEY PATTERNS, and stats block

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

Then show the standard "What I learned" section, stats block, and invitation — same format as `/last30days`.

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
- Pull source statistics from `~/.local/share/last30days/out/report.json` automatically
- Validate that report.json matches the topic before pulling stats
- Add top sources by engagement

**After persisting**, tell the user:

```
Saved to ~/Desktop/last365days/<slug>.md (<N> entries total)
```

---

## STEP 6: Invitation

Same as `/last30days` — adapt to QUERY_TYPE. Include 2-3 specific suggestions based on the research.

**Additional suggestions for profiles with history:**
- "Compare how things have changed since [earliest date]"
- "Show me the full timeline for [person]"

---

## UTILITY: Browse Profiles

If the user asks to see their profiles, list existing research, or check history:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py list
```

For a specific profile's timeline:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py history "<slug>"
```

To read a full profile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py read "<slug>"
```

To search across all profiles:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py search "query terms"
```

To search within a specific profile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py search "query terms" --slug "<slug>"
```

To validate paths and dependencies:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py doctor
```

To diff two saved dates from one profile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py diff "<slug>" "<date1>" "<date2>"
```

To export one profile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py export "<slug>" --format json
```

To export every profile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/persist.py export --all --format csv
```

---

## Context Memory

Same as `/last30days`: after research, you're an expert. Answer follow-ups from memory. Don't re-search unless the user asks about a different topic.

**Additional context**: You also have access to the person's full research history via the profile file. Reference it when answering follow-ups about trends or changes over time.

---

## Examples

### Example 1: First research on a new person

User says: "last365 Saba Nafees"

Actions:
1. `persist.py match` finds no existing profile
2. Tells user: "No existing profile found. Creating saba-nafees.md"
3. Runs last30days research engine across all 8 sources
4. Synthesizes findings in "What I learned" format
5. `persist.py append "saba-nafees" --title "Saba Nafees"` creates the file

Result: `~/Desktop/last365days/saba-nafees.md` created with first dated entry.

### Example 2: Follow-up research (existing profile)

User says: "last365 Saba Nafees" (one month later)

Actions:
1. `persist.py match` returns exact match for saba-nafees.md (3 entries, last updated 2026-02-05)
2. `persist.py history "saba-nafees"` loads previous synthesis for comparison
3. Runs fresh research across all sources
4. Synthesizes with "What Changed since 2026-02-05" section
5. Appends new dated entry to existing file

Result: `saba-nafees.md` now has 4 entries. User sees what changed since last check.

### Example 3: Browsing profiles

User says: "show me my last365 profiles"

Actions:
1. `persist.py list` returns all profiles with metadata
2. Displays: slug, title, entry count, last updated date, file size

Result: User sees a summary of all tracked people/topics.

---

## Troubleshooting

### Error: "Could not find last30days research engine"

Cause: The last30days skill is not installed or not in any expected path.

Solution:
1. Install last30days: `npx skills add mvanhorn/last30days-skill -g -y`
2. Verify it exists: `ls ~/.claude/skills/last30days/scripts/last30days.py`

### Error: persist.py not found

Cause: `CLAUDE_SKILL_DIR` environment variable is not set or points to the wrong location.

Solution:
1. Check your agent runtime sets `CLAUDE_SKILL_DIR` to this skill's directory
2. Try running directly: `python3 /path/to/last365days/scripts/persist.py list`

### Stats missing from saved entry

Cause: `report.json` not found at `~/.local/share/last30days/out/report.json`, or the topic in report.json doesn't match the profile being saved.

Solution:
- This is normal if last30days output location differs from default
- Override with `LAST30DAYS_OUT` environment variable pointing to the correct directory
- Synthesis is still saved; only the auto-generated stats block is skipped

### Profile matching is wrong

Cause: A medium-confidence match was accepted for the wrong person (e.g., two people share a name token).

Solution:
- The skill always tells you which file it's writing to before persisting
- When in doubt, it creates a new profile rather than risk corruption
- You can manually merge profiles later by editing the MD files

---

## Security & Permissions

Same as `/last30days`. This skill additionally:
- Writes MD files to `~/Desktop/last365days/` (user-visible, human-readable)
- Reads `~/.local/share/last30days/out/report.json` for source statistics
- Does not transmit profile data to any external service
