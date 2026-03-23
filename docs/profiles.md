# Profiles

## What is a profile?

A profile is a TOML file that defines an **analysis lens** — which [blocks](blocks.md) to activate and how to frame the analysis. Profiles live in `src/profiles/` and require no Python code to create or modify.

Each profile provides:

- A **context** that tells the LLM how to interpret the conversation (e.g., "analyze as a therapy session")
- An ordered **block list** that determines which analysis dimensions to extract and in what order

## Built-in profiles

| Profile | Use case | Blocks |
|---------|----------|--------|
| `business` | Corporate meetings — decisions, accountability, stakeholder dynamics | 9 base blocks |
| `therapy` | Therapy sessions — emotional patterns, relational dynamics, frameworks | 9 base + 4 domain blocks |

## Using a profile

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business
```

## Adding extra blocks to a profile

Append blocks that aren't in the profile's default list:

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business --add-block emotional_patterns
```

`--add-block` is repeatable — use it multiple times to add several blocks:

```bash
python src/diarize.py session.mp4 -o output/ --profile business \
    --add-block emotional_patterns \
    --add-block therapeutic_frameworks
```

## Adding per-run context

Append additional context to refine the analysis for a specific recording:

```bash
python src/diarize.py meeting.mp4 -o output/ --profile business -c "RSI pharma regulatory meeting"
```

The `-c` text is appended to the profile's built-in context, giving the LLM more specific framing without changing the profile file.

## Creating a custom profile

Create a TOML file in `src/profiles/`:

```toml
# src/profiles/research.toml
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

### Profile fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Human-readable profile name (shown in briefing header) |
| `description` | Yes | One-line description (shown by `--list-profiles`) |
| `context` | Yes | Framing sent to the LLM — shapes how every block is interpreted |
| `blocks` | Yes | Ordered list of block names to activate |

All referenced blocks must exist as TOML files in `src/blocks/`. The tool will error clearly if a block is missing.

## Listing available profiles

```bash
python src/diarize.py --list-profiles
```

Output:

```
Available profiles:
  business  — Corporate meeting analysis — decisions, accountability, stakeholder dynamics
  therapy   — Therapy session analysis — emotional patterns, relational dynamics, therapeutic frameworks
```
