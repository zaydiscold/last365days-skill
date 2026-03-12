<h1 align="center">last365days-skill</h1>

<p align="center">claude code skill for persistent research tracking. wraps <a href="https://github.com/mvanhorn/last30days-skill">last30days</a> with per-person/topic running logs.</p>

<p align="center">
  <img src="https://img.shields.io/badge/skill-v1.0.0-B4A7D6?style=flat-square&labelColor=1a1a2e" alt="skill version" />
  <img src="https://img.shields.io/badge/zayd.wtf-D4AF37?style=flat-square&labelColor=1a1a2e" alt="site" />
</p>

<p align="center">
  <a href="#what-it-does">what it does</a> · <a href="#install">install</a> · <a href="#usage">usage</a> · <a href="#how-it-works">how it works</a>
</p>

<br>

## what it does

[last30days](https://github.com/mvanhorn/last30days-skill) researches any topic across reddit, x, youtube, tiktok, instagram, hacker news, polymarket, and the web. it's powerful — but ephemeral. once you close the session, the research is gone.

**last365days** wraps it with persistence. every research run is saved to a dated section in a per-person/topic markdown file. run it on the same person a month later and it appends a new entry, compares what changed, and builds a timeline.

one file per person. growing log. long-term memory.

works in claude code, codex, cursor, openclaw. one install, all agents.

<br>

## install

**prerequisite:** [last30days](https://github.com/mvanhorn/last30days-skill) must be installed and working (it provides the research engine).

```bash
npx skills add zaydiscold/last365days-skill@last365days -g -y
```

or install to a single agent:

```bash
npx skills add zaydiscold/last365days-skill@last365days -y
```

research output saves to `~/Desktop/last365days/` by default. override with `LAST365DAYS_DIR` env var.

<br>

## usage

```bash
/last365days saba nafees         # research + save to saba-nafees.md
/last365days kanye west          # research + save to kanye-west.md
/last365days AI video tools      # works for topics too
```

run it again later on the same person:

```bash
/last365days saba nafees         # appends new entry, shows what changed
```

the skill matches against existing profiles automatically. if it's not sure, it creates a new file rather than risk mixing people up.

browse your profiles:

```bash
/last365days                     # lists all profiles
```

<br>

## how it works

```
/last365days <person>
        │
        ▼
┌─ SKILL.md workflow ──────────────────────────────────┐
│  1. Check existing profiles (auto-injected on load)  │
│  2. Match against existing or create new             │
│  3. Run last30days.py research engine (unchanged)    │
│  4. Synthesize (same as /last30days)                 │
│  5. If history exists: compare what changed          │
│  6. Append dated section to person's MD file         │
└──────────────────────────────────────────────────────┘
        │
        ▼
~/Desktop/last365days/
├── saba-nafees.md          ← one file per person
├── kanye-west.md
├── ai-video-tools.md       ← topics work too
└── ...

each file:
  # Saba Nafees
  ## 2026-03-05
  ### Synthesis
  [what was learned, key patterns]
  ### Sources
  [auto-generated stats from all 8 sources]
  ---
  ## 2026-04-05
  ### Synthesis
  [new findings + what changed since last time]
  ---
```

<br>

## changelog

### v1.0.0
- initial release: persistent per-person/topic research logs
- wraps last30days research engine (all 8 sources)
- same-person matching with exact/high/medium confidence
- same-day duplicate handling (sub-entries)
- report.json topic validation before pulling stats
- qmd collection auto-indexed via after-hook
- `${CLAUDE_SKILL_DIR}` for portable paths
- `LAST365DAYS_DIR` env var for custom output location

<br>

<p align="left"><strong>zayd / cold</strong></p>

<p align="center">
  <a href="https://zayd.wtf">zayd.wtf</a> · <a href="https://x.com/coldcooks">twitter</a> · <a href="https://github.com/zaydiscold">github</a>
</p>

<p align="center">mit. <a href="./LICENSE">license</a></p>
