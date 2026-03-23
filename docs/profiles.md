# Profiles

<!-- TODO: Fill in as profile system is implemented -->

## What is a profile?

A profile is a TOML file that defines an analysis lens — which blocks to activate and how to frame the analysis.

## Built-in profiles

| Profile | Use case | Blocks |
|---------|----------|--------|
| `business` | Corporate meetings | 9 base blocks |
| `therapy` | Therapy sessions | 9 base + 4 domain blocks |

## Using a profile

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
```

## Adding extra blocks

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business --add-block emotional_patterns
```

## Creating a custom profile

Create a TOML file in `src/profiles/`:

```toml
# profiles/research.toml
name = "Research Discussion"
description = "Academic research meeting analysis"

context = """
Analyze as an academic research discussion. Focus on methodology,
findings, and literature references.
"""

blocks = [
    "session_summary",
    "key_concepts",
    "action_items",
    "open_questions",
]
```

## Listing available profiles

```bash
python src/diarize.py --list-profiles
```
