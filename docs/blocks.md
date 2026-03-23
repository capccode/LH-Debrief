# Blocks

<!-- TODO: Fill in as block system is implemented -->

## What is a block?

A block is one analysis dimension — a TOML file that defines a prompt snippet and expected JSON output. Profiles assemble blocks into a complete analysis.

## Base blocks

| Block | Description |
|-------|-------------|
| `session_summary` | 2-3 sentence overview |
| `decisions` | Concrete decisions made |
| `action_items` | Tasks with owners and deadlines |
| `follow_ups` | Topics to revisit later |
| `todos` | AI-generated suggestions (not explicitly discussed) |
| `key_concepts` | Terms, acronyms, frameworks |
| `open_questions` | Raised but unresolved |
| `participant_dynamics` | Communication styles and tension points |
| `key_quotes` | Noteworthy statements worth preserving |

## Using blocks directly

Skip profiles and pick blocks manually:

```bash
python src/diarize.py meeting.mp4 -o output/ --blocks session_summary action_items todos
```

## Creating a custom block

Create a TOML file in `src/blocks/`:

```toml
# blocks/methodology_notes.toml
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

## Listing available blocks

```bash
python src/diarize.py --list-blocks
```
