# Modular Analysis Architecture — Design Spec

## Problem

The current analysis system has a single hardcoded prompt, a single hardcoded JSON schema, and a single hardcoded markdown renderer — all coupled to the business meeting use case. Adding a new analysis "lens" (therapy, research, coaching) requires rewriting Python code.

## Goal

A composable, extensible analysis system where:
- **Blocks** are reusable analysis dimensions (TOML files — no Python)
- **Profiles** assemble blocks into use-case-specific configurations (TOML files — no Python)
- **Providers** (Anthropic, Ollama) are selected independently of profiles
- Users extend the system by adding TOML files, not writing code
- Output is structured JSON suitable for future RAG/KG ingestion

## Architecture Overview

```
CLI (diarize.py)
  │
  ├── audio.py          → ffmpeg conversion, device selection
  ├── transcribe.py     → Whisper model loading, segment alignment
  │
  └── analyze.py        → prompt assembly + LLM orchestration
        │
        ├── profiles.py  → loads profile TOML, resolves block list
        ├── providers.py → _call_anthropic, _call_ollama
        └── render.py    → generic JSON → markdown briefing
```

Two consumers of this core engine:
1. **CLI** — power-user, scriptable, automatable (this spec)
2. **Frontend** — future standalone project, upload + click + view (not in scope)

Both hit the same core. The frontend will call into the same profile/block/provider system.

---

## Blocks

A block is one analysis dimension — a single TOML file in `src/blocks/`.

### Block file format

Each block includes a `json_example` field — the literal JSON snippet that gets merged into the prompt to show the LLM what output to produce. This avoids inventing a schema DSL; you write the example you want the LLM to follow.

**String value block:**

```toml
# blocks/session_summary.toml
name = "session_summary"
display_name = "Session Summary"
description = "2-3 sentence overview of the conversation"

prompt = """
Provide a concise 2-3 sentence summary of the main points and outcomes
of this conversation.
"""

json_example = '"session_summary": "2-3 sentence summary of the main points and outcomes"'
```

**List of strings block:**

```toml
# blocks/decisions.toml
name = "decisions"
display_name = "Decisions Made"
description = "Concrete decisions that were made"

prompt = """
Identify all concrete decisions that were made during this conversation.
Only include things that were actually decided, not things still being discussed.
"""

json_example = '"decisions": ["Decision 1 that was made", "Decision 2 that was made"]'
```

**List of dicts block:**

```toml
# blocks/action_items.toml
name = "action_items"
display_name = "Action Items"
description = "Extract action items with owners and due dates"

prompt = """
Identify all action items discussed. For each, note who owns it
and any mentioned deadline.
"""

json_example = """
"action_items": [
    {"owner": "Person name or role", "action": "What they need to do", "due": "Due date if mentioned, otherwise TBD"}
]"""
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Block identifier, matches filename |
| `display_name` | Yes | Human-readable heading for the briefing (e.g., "Key Concepts & Terms") |
| `description` | Yes | Human-readable explanation |
| `prompt` | Yes | Prompt snippet sent to LLM for this dimension |
| `json_example` | Yes | Literal JSON snippet merged into the prompt example — what the LLM should output for this block |

### Base blocks (ship with the tool)

| Block | What it captures |
|-------|-----------------|
| `session_summary` | 2-3 sentence overview of the conversation |
| `decisions` | Concrete decisions that were made |
| `action_items` | Explicitly discussed tasks with owners and deadlines |
| `follow_ups` | Topics to revisit in future conversations |
| `todos` | AI-generated suggestions inferred from context (not explicitly discussed) |
| `key_concepts` | Terms, acronyms, and frameworks mentioned |
| `open_questions` | Questions raised but not resolved |
| `participant_dynamics` | Communication styles, who drove what, tension points |
| `key_quotes` | Exact noteworthy statements worth preserving |

### Domain blocks (examples, user-created)

| Block | Profile | What it captures |
|-------|---------|-----------------|
| `emotional_patterns` | therapy | Recurring emotional themes and shifts |
| `relational_dynamics` | therapy | How participants relate, connect, and disconnect |
| `therapeutic_frameworks` | therapy | Relevant frameworks (attachment theory, IFS, etc.) |
| `suggested_explorations` | therapy | Suggested lines of inquiry for future sessions |

### Adding a new block

1. Create `src/blocks/<name>.toml` with `name`, `display_name`, `description`, `prompt`, `json_example`
2. Reference `<name>` in any profile, or use `--add-block <name>` / `--blocks <name>` at CLI
3. No Python changes needed

---

## Profiles

A profile is an assembled configuration — a TOML file in `src/profiles/` that lists which blocks to activate and provides lens context.

### Profile file format

```toml
# profiles/business.toml
name = "Business Meeting"
description = "Corporate meeting analysis — decisions, accountability, stakeholder dynamics"

context = """
Analyze as a corporate meeting. Focus on deliverables, ownership,
and stakeholder dynamics. Frame participant dynamics as actionable
management insights.
"""

blocks = [
    "session_summary",
    "decisions",
    "action_items",
    "follow_ups",
    "todos",
    "key_concepts",
    "open_questions",
    "participant_dynamics",
    "key_quotes",
]
```

```toml
# profiles/therapy.toml
name = "Therapy Session"
description = "Therapy session analysis — emotional patterns, relational dynamics, therapeutic frameworks"

context = """
Analyze as a therapy session. Focus on emotional undercurrents,
relational patterns, and therapeutic frameworks. Frame suggestions
gently as explorations, not prescriptions. Note moments of rupture
and repair. Attend to how participants relate and connect in the space.
"""

blocks = [
    "session_summary",
    "decisions",
    "action_items",
    "follow_ups",
    "todos",
    "key_concepts",
    "open_questions",
    "participant_dynamics",
    "key_quotes",
    "emotional_patterns",
    "relational_dynamics",
    "therapeutic_frameworks",
    "suggested_explorations",
]
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Human-readable profile name |
| `description` | Yes | What this profile is for |
| `context` | Yes | Lens/framing sent to the LLM — shapes how every block is interpreted |
| `blocks` | Yes | Ordered list of block names to activate |

### Adding a new profile

1. Create `src/profiles/<name>.toml`
2. List desired blocks (base + any domain blocks you've created)
3. Write a `context` that frames the analysis lens
4. Use with `--profile <name>`

---

## CLI Interface

```bash
# Profile-based (most common)
python src/diarize.py meeting.mp4 -o output/ --profile business

# Profile + extra blocks
python src/diarize.py session.mp4 -o output/ --profile therapy --add-block key_quotes

# Direct block selection (no profile)
python src/diarize.py recording.mp4 -o output/ --blocks session_summary action_items key_concepts

# Provider selection (independent of profile)
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama
python src/diarize.py session.mp4 -o output/ --profile therapy --provider ollama --llm-model phi4:14b

# Per-run context (appended to profile context)
python src/diarize.py meeting.mp4 -o output/ --profile business -c "RSI pharma regulatory meeting"

# Existing flags unchanged
python src/diarize.py audio.mp4 -o output/ -n 3 -m medium -l ja --translate

# List available profiles and blocks
python src/diarize.py --list-profiles
python src/diarize.py --list-blocks
```

### New flags

| Flag | Purpose |
|------|---------|
| `--profile <name>` | Select analysis profile |
| `--add-block <name>` | Add block(s) to the profile's list (repeatable) |
| `--blocks <name> [name...]` | Use these blocks directly (no profile) |
| `-c, --context <text>` | Per-run context appended to profile context (e.g., "RSI pharma regulatory meeting"). Kept from current CLI. |
| `--provider <anthropic\|ollama>` | LLM provider (default: anthropic) |
| `--llm-model <name>` | Override LLM model name |
| `--list-profiles` | List available profiles and exit |
| `--list-blocks` | List available blocks and exit |

### Precedence

- `--blocks` and `--profile` are mutually exclusive
- `--add-block` requires `--profile`
- `-c` / `--context` works with both `--profile` and `--blocks` — when used with a profile, it is appended to the profile's built-in context; when used with `--blocks`, it is the only context
- If neither `--profile` nor `--blocks` is specified and `--no-analyze` is not set, error with a helpful message listing available profiles
- `--provider` and `--llm-model` are independent of profile selection

---

## Module Responsibilities

### `diarize.py` — CLI entry point and pipeline orchestrator

Slimmed down from current 404 lines. Responsible for:
- CLI argument parsing (argparse)
- Pipeline orchestration: audio → diarize → transcribe → analyze → render → save
- Loading `.env`
- Calling into other modules

Does NOT contain: audio conversion, whisper logic, LLM calls, prompt assembly, or rendering.

### `audio.py` — Audio conversion and diarization

Extracted from current `diarize.py`:
- `convert_to_wav()` — ffmpeg conversion
- `get_pipeline()` — load Pyannote with CUDA/MPS/CPU device selection
- `diarize()` — run speaker diarization, return segments
- `truncate_name()` — filename utility

### `transcribe.py` — Whisper model and segment alignment

Extracted from current `diarize.py`:
- `get_whisper_model()` — load Whisper with its own device selection (skips MPS for large models due to sparse tensor issues)
- `transcribe_segments()` — full-audio transcription + segment alignment
- `WhisperSegment` TypedDict

Note: Pyannote and Whisper have different device compatibility (Whisper skips MPS). Each module handles its own device selection internally.

### `profiles.py` — Profile and block loading

New module:
- `load_block(name)` — reads `src/blocks/<name>.toml`, returns block dict
- `load_profile(name)` — reads `src/profiles/<name>.toml`, returns profile dict
- `resolve_blocks(profile, add_blocks)` — returns ordered list of block dicts
- `list_profiles()` — returns available profile names
- `list_blocks()` — returns available block names
- Validates that referenced blocks exist, errors clearly if not

### `analyze.py` — Prompt assembly and LLM orchestration

Refactored from current:
- `assemble_prompt(segments, blocks, context=None)` — builds the full prompt from transcript + block prompts + merged json_example. Context is optional — omitted from prompt when None.
- `analyze_transcript(segments, blocks, provider, model, context=None)` — assembles prompt, calls provider, parses JSON response
- JSON response parsing with code-block stripping

Does NOT contain: LLM client code (that's in `providers.py`) or rendering (that's in `render.py`).

### `providers.py` — LLM provider implementations

New module:
- `call_llm(prompt, provider, model)` — routes to correct provider
- `_call_anthropic(prompt, model)` — Anthropic SDK call
- `_call_ollama(prompt, model)` — Ollama client call with `format="json"`

### `render.py` — Generic JSON to markdown briefing

Extracted and generalized from current `save_briefing()`:
- `render_briefing(output_dir, short_name, segments, analysis, blocks, profile_name)` — generates markdown from any analysis JSON
- Iterates blocks in profile order (not LLM output order) and renders each block's JSON value using the block's `display_name` as the section heading:
  - String value → paragraph under `## Display Name`
  - List of strings → bullet list
  - List of dicts → table (dict keys become columns)
  - Missing key → skip section, warn
- Also saves raw `analysis_<name>.json`

No hardcoded field names. The block list drives section order and headings.

---

## Prompt Assembly

`analyze.py` assembles the full prompt from blocks. Given a therapy profile with 4 blocks, the assembled prompt looks like:

```
You are analyzing a recorded conversation.

<context>
Analyze as a therapy session. Focus on emotional undercurrents,
relational patterns, and therapeutic frameworks...
</context>

<transcript>
[0.0s] Speaker 0: ...
[5.2s] Speaker 1: ...
</transcript>

Analyze the transcript across the following dimensions:

1. SESSION SUMMARY: 2-3 sentence overview of the conversation

2. EMOTIONAL PATTERNS: Track emotional themes across the conversation...

3. RELATIONAL DYNAMICS: ...

4. TODOS: Generate actionable suggestions inferred from the conversation...

Provide your analysis as JSON with this exact structure:
{
    "session_summary": "...",
    "emotional_patterns": [...],
    "relational_dynamics": [...],
    "todos": [...]
}

Return ONLY the JSON, no other text.
```

The profile's `context` sets the lens (omitted entirely when using `--blocks` without `-c`). Each block's `prompt` becomes a numbered dimension. The merged `json_example` from all blocks becomes the JSON example. Sections render in block list order, using each block's `display_name` as the heading.

---

## Output

### Files generated (unchanged structure)

```
output/<meeting-name>/
├── diarization_<name>.json     # Raw speaker segments
├── transcript_<name>.txt       # Human-readable transcript
├── briefing_<name>.md          # Rendered analysis (from render.py)
└── analysis_<name>.json        # Raw LLM analysis JSON
```

### Briefing format (generic)

The briefing markdown is generated by `render.py` walking the JSON keys:

```markdown
# Session Briefing: <name>

**Date:** 2026-03-22 | **Duration:** 45 min | **Speakers:** 3 | **Profile:** therapy

---

## Session Summary

The session focused on...

## Emotional Patterns

| Pattern | Moments | Significance |
|---------|---------|-------------|
| ... | ... | ... |

## Todos

- Consider exploring...
- Schedule follow-up on...
```

---

## Error Handling

- Missing block file → clear error: `Block 'xyz' not found in src/blocks/. Available: ...`
- Missing profile file → clear error: `Profile 'xyz' not found in src/profiles/. Available: ...`
- No profile or blocks specified (without --no-analyze) → error listing available profiles
- Ollama not running → clear error with setup instructions
- Ollama model not pulled → clear error: `Model 'xyz' not found. Run: ollama pull xyz`
- LLM returns invalid JSON → log raw response, return None, skip briefing
- LLM omits a block's key → render skips that section, warns

---

## What's NOT in scope

- Frontend (future standalone project)
- RAG / knowledge graph ingestion
- Per-block context overrides in profiles
- Block dependencies or ordering constraints
- Profile inheritance (one profile extending another)
- Schema validation of LLM output (graceful degradation via missing-key warnings is sufficient)
