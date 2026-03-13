<h1 align="center">last365days-skill</h1>

<p align="center">
  Persistent research tracking for people, brands, and topics. This skill wraps
  <a href="https://github.com/mvanhorn/last30days-skill">last30days</a> and
  saves each run into a dated Markdown timeline.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/skill-v1.1.0-B4A7D6?style=flat-square&labelColor=1a1a2e" alt="skill version" />
  <img src="https://img.shields.io/badge/license-MIT-D4AF37?style=flat-square&labelColor=1a1a2e" alt="license" />
</p>

## What it does

`last30days` can research a topic deeply, but the output is ephemeral. Once the
session ends, you lose the accumulated context. `last365days` adds persistence
on top of that workflow.

Each run appends a dated section to a single Markdown file for that person or
topic. Over time, that file becomes a timeline you can revisit, diff, export,
and extend.

## Compatibility matrix

This repo is runtime-agnostic at the file level, but it relies on
`last30days` for the research engine.

| Runtime | Supported | Notes |
| --- | --- | --- |
| Claude Code | Yes | Native skill workflow and `CLAUDE_SKILL_DIR` path support |
| Codex | Yes | Reads the same skill files and Python helper |
| Cursor | Yes | Works as a repo-backed skill with the same persistence layer |
| OpenClaw | Yes | Uses the same Markdown storage model |
| Python CLI only | Partial | `persist.py` commands work directly without the skill wrapper |

## Install

Install `last30days` first. `last365days` depends on its research output and
its `last30days.py` engine.

To install globally:

```bash
npx skills add zaydiscold/last365days-skill@last365days -g -y
```

To install for one agent only:

```bash
npx skills add zaydiscold/last365days-skill@last365days -y
```

By default, saved research goes to `~/Desktop/last365days/`. Override that
directory with `LAST365DAYS_DIR`.

`persist.py` reads stats from `~/.local/share/last30days/out/report.json` by
default. Override that location with `LAST30DAYS_OUT` or the `--report-path`
flag.

## Usage

The main skill entry point is `/last365days`.

```bash
/last365days saba nafees
/last365days kanye west
/last365days AI video tools
```

Run it again later on the same topic and the skill appends a new dated entry:

```bash
/last365days saba nafees
```

If the match is exact or high confidence, the skill appends automatically. If
the match is only medium confidence, the skill now asks the user to confirm
whether it should reuse the existing file or create a new one.

To browse existing profiles:

```bash
/last365days
```

## Persist CLI reference

`last365days/scripts/persist.py` is the persistence layer behind the skill. You
can run it directly when you want diagnostics or structured exports.

### Core commands

These commands are the ones the skill depends on during normal use.

```bash
python3 last365days/scripts/persist.py list
python3 last365days/scripts/persist.py match "Saba Nafees"
python3 last365days/scripts/persist.py history "saba-nafees"
python3 last365days/scripts/persist.py read "saba-nafees"
python3 last365days/scripts/persist.py search "founder mode"
python3 last365days/scripts/persist.py slugify "Saba Nafees"
```

### New v1.1 commands

These commands improve trust, debugging, and operability.

```bash
python3 last365days/scripts/persist.py doctor
python3 last365days/scripts/persist.py diff "saba-nafees" 2026-03-05 2026-04-05
python3 last365days/scripts/persist.py export "saba-nafees" --format json
python3 last365days/scripts/persist.py export --all --format csv
```

`doctor` checks:

- whether the research directory exists or can be created
- whether the last30days output directory is available
- whether `report.json` is readable and shaped like a valid report
- whether `last30days.py` is installed
- whether optional `qmd` indexing is available

`diff` compares two saved date blocks from the same profile using a deterministic
unified diff.

`export` lets you move data out of the Markdown files without hand parsing:

- `export <slug> --format md|json|csv`
- `export --all --format json|csv`

## How it works

The runtime behavior is split cleanly between the skill instructions and the
Python helper.

```text
/last365days <topic>
        │
        ▼
SKILL.md
  1. List existing profiles
  2. Match against existing files
  3. Ask for confirmation on medium-confidence matches
  4. Run last30days research
  5. Synthesize and compare against history
  6. Persist the new entry
        │
        ▼
persist.py
  - appends Markdown entries
  - reads report.json for stats
  - exposes history/search/diff/export/doctor commands
```

Saved files live in `~/Desktop/last365days/` by default:

```text
~/Desktop/last365days/
├── saba-nafees.md
├── kanye-west.md
├── ai-video-tools.md
└── ...
```

The Markdown format is documented in
`last365days/references/file-format.md`.

## Repository map

If you need to understand where to look before changing something, start here.

- `last365days/SKILL.md`: runtime workflow, matching rules, and user-facing
  research behavior
- `last365days/scripts/persist.py`: persistence CLI, storage parsing, exports,
  diffs, and diagnostics
- `last365days/references/file-format.md`: profile file structure and same-day
  update format
- `last365days/references/operations.md`: browse, export, diff, and
  troubleshooting flows that are intentionally kept out of the main skill path
- `tests/test_persist.py`: CLI regression coverage for slugify, matching,
  history, search, doctor, diff, and export
- `.github/workflows/ci.yml`: syntax check plus test execution on push and pull
  request

## Testing and CI

This repo now includes a minimal built-in Python test suite and a GitHub Actions
workflow.

Run everything locally with:

```bash
python3 -m compileall last365days tests
python3 -m unittest discover -s tests -v
```

CI runs the same two checks on every push to `main` and on pull requests.

## Known limitations

The current design stays intentionally lean. A few limits are deliberate.

- Medium-confidence matches still rely on user confirmation rather than richer
  identity metadata.
- `diff` compares whole dated Markdown blocks. It does not produce semantic
  summaries.
- `export --all --format md` is not supported.
- Source stats depend on a compatible `report.json` produced by `last30days`.
- There are no destructive workflows yet for merge, delete-entry, or
  delete-profile.
- File writes are simple append operations. There is no broad locking or atomic
  rewrite strategy yet.

## v1.2 backlog

These items are intentionally deferred because they add more risk than the v1.1
changes.

- `merge`, `delete-entry`, and `delete-profile` with backup and confirmation
- profile metadata blocks such as aliases, canonical handles, and timestamps
- broader locking and atomic rewrite strategy for concurrent edits

## Changelog

### v1.1.0

- added `doctor` diagnostics for path, dependency, and `report.json` validation
- added `diff <slug> <date1> <date2>` for deterministic profile comparisons
- added `export` support for Markdown, JSON, and CSV outputs
- added a test suite for core CLI behavior
- added GitHub Actions CI for syntax and tests
- changed medium-confidence matches to require explicit user confirmation
- expanded documentation with a repo map, command reference, and known limits

### v1.0.1

- added Anthropic skill guide metadata and compatibility frontmatter
- moved file format details into `references/file-format.md`
- added troubleshooting and better trigger phrases
- added `search` plus CLI path overrides for `persist.py`
- improved Unicode slug handling and deterministic fallback slugs
- guarded the `qmd` after-hook so it only runs when available

### v1.0.0

- shipped persistent per-person and per-topic Markdown timelines
- wrapped `last30days` research output in a reusable profile model
- added same-day duplicate handling and automatic source stats

<p align="center">
  <a href="./LICENSE">MIT</a>
</p>
