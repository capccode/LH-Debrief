# Blocks

## What is a block?

A block is one **analysis dimension** — a TOML file that defines a prompt snippet and expected JSON output. [Profiles](profiles.md) assemble blocks into a complete analysis. You can also select blocks directly with `--blocks` for ad-hoc analysis.

Blocks live in `src/blocks/` and require no Python code to create or modify.

## Base blocks

These ship with the tool and are used by the built-in profiles:

| Block | Description |
|-------|-------------|
| `session_summary` | 2-3 sentence overview of the conversation |
| `decisions` | Concrete decisions that were made |
| `action_items` | Tasks with owners and deadlines |
| `follow_ups` | Topics to revisit in future conversations |
| `todos` | AI-generated suggestions inferred from context (not explicitly discussed) |
| `key_concepts` | Terms, acronyms, and frameworks mentioned |
| `open_questions` | Questions raised but not resolved |
| `participant_dynamics` | Communication styles, who drove what, tension points |
| `key_quotes` | Exact noteworthy statements worth preserving |

## Domain blocks

Domain-specific blocks for specialized use cases. These are included with the tool but only activated when referenced by a profile or selected directly.

| Block | Domain | Description |
|-------|--------|-------------|
| `emotional_patterns` | therapy | Recurring emotional themes and shifts |
| `relational_dynamics` | therapy | How participants relate, connect, and disconnect |
| `therapeutic_frameworks` | therapy | Relevant frameworks (attachment theory, IFS, CBT, etc.) |
| `suggested_explorations` | therapy | Suggested lines of inquiry for future sessions |

## Using blocks directly

Skip profiles and pick blocks manually — useful for quick, focused analysis:

```bash
python src/diarize.py meeting.mp4 -o output/ --blocks session_summary action_items todos
```

When using `--blocks`, there is no profile context. Use `-c` to provide framing:

```bash
python src/diarize.py meeting.mp4 -o output/ --blocks session_summary key_concepts -c "ML research standup"
```

## Block file format

Each block is a TOML file with five required fields:

```toml
# src/blocks/methodology_notes.toml
name = "methodology_notes"
display_name = "Methodology Notes"
description = "Research methodology discussed or proposed"

prompt = """
Identify any research methodology discussed, proposed, or critiqued.
Note the approach, its strengths, and any concerns raised.
"""

json_example = """
"methodology_notes": [
    {"approach": "Method name", "details": "How it was discussed", "concerns": "Any issues raised"}
]"""
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Block identifier — must match the filename (without `.toml`) |
| `display_name` | Yes | Human-readable heading in the briefing (e.g., "Key Concepts & Terms") |
| `description` | Yes | One-line description (shown by `--list-blocks`) |
| `prompt` | Yes | Prompt snippet sent to the LLM for this dimension |
| `json_example` | Yes | Literal JSON snippet showing the expected output structure |

### json_example patterns

The `json_example` field supports three value types. The renderer detects the type automatically:

**String** — renders as a paragraph:
```toml
json_example = '"session_summary": "2-3 sentence summary of the main points and outcomes"'
```

**List of strings** — renders as bullet points:
```toml
json_example = '"decisions": ["Decision 1 that was made", "Decision 2 that was made"]'
```

**List of dicts** — renders as a table:
```toml
json_example = """
"action_items": [
    {"owner": "Person name", "action": "What they need to do", "due": "Due date or TBD"}
]"""
```

## Creating a custom block

1. Create `src/blocks/<name>.toml` with the five required fields
2. Reference `<name>` in any profile, or use `--add-block <name>` / `--blocks <name>` at the CLI
3. No Python changes needed

## Listing available blocks

```bash
python src/diarize.py --list-blocks
```

Output:

```
Available blocks:
  action_items                  — Extract action items with owners and due dates
  decisions                     — Concrete decisions that were made
  emotional_patterns            — Recurring emotional themes and shifts
  follow_ups                    — Topics to revisit in future conversations
  key_concepts                  — Terms, acronyms, and frameworks mentioned
  key_quotes                    — Exact noteworthy statements worth preserving
  open_questions                — Questions raised but not resolved
  participant_dynamics          — Communication styles, who drove what, tension points
  relational_dynamics           — How participants relate, connect, and disconnect
  session_summary               — 2-3 sentence overview of the conversation
  suggested_explorations        — Suggested lines of inquiry for future sessions
  therapeutic_frameworks        — Relevant frameworks (attachment theory, IFS, etc.)
  todos                         — AI-generated suggestions inferred from context (not explicitly discussed)
```
