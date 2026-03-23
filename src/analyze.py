"""Prompt assembly and LLM orchestration for transcript analysis.

Dynamically builds prompts from block definitions and routes
through the provider abstraction — no hardcoded fields or clients.
"""

import json

from rich.console import Console

from providers import call_llm

console = Console()


def assemble_prompt(
    segments: list[dict],
    blocks: list[dict],
    context: str | None = None,
) -> str:
    """Build the full analysis prompt from segments and block definitions.

    Args:
        segments: List of diarized segments with 'start', 'end', 'speaker', 'text'
        blocks: Ordered list of block dicts (from resolve_blocks)
        context: Optional context string (from profile + per-run)

    Returns:
        Assembled prompt string ready for LLM
    """
    # Format transcript lines
    transcript_lines = []
    for seg in segments:
        text = seg.get("text", "")
        if text:
            transcript_lines.append(f"[{seg['start']:.1f}s] {seg['speaker']}: {text}")
    transcript_text = "\n".join(transcript_lines)

    # Build numbered dimensions
    dimensions = []
    for i, block in enumerate(blocks, 1):
        dimensions.append(
            f"{i}. {block['display_name']}: {block['description']}\n{block['prompt'].strip()}"
        )
    dimensions_text = "\n\n".join(dimensions)

    # Merge json_examples
    examples = [block["json_example"].strip() for block in blocks]
    json_example_text = "{\n    " + ",\n    ".join(examples) + "\n}"

    # Assemble prompt
    parts = ["You are analyzing a recorded conversation."]

    if context is not None:
        parts.append(f"\n<context>\n{context.strip()}\n</context>")

    parts.append(f"\n<transcript>\n{transcript_text}\n</transcript>")
    parts.append(f"\nAnalyze the transcript across the following dimensions:\n\n{dimensions_text}")
    parts.append(f"\nProvide your analysis as JSON with this exact structure:\n{json_example_text}")
    parts.append("\nReturn ONLY the JSON, no other text.")

    return "\n".join(parts)


def analyze_transcript(
    segments: list[dict],
    blocks: list[dict],
    provider: str = "anthropic",
    model: str | None = None,
    context: str | None = None,
) -> dict | None:
    """Orchestrate transcript analysis via LLM.

    Args:
        segments: List of diarized segments with 'start', 'end', 'speaker', 'text'
        blocks: Ordered list of block dicts (from resolve_blocks)
        provider: LLM provider name ("anthropic" or "ollama")
        model: Model name override (uses provider default if None)
        context: Optional context string

    Returns:
        Parsed analysis dict or None on failure
    """
    # Build transcript text to check for content
    has_text = any(seg.get("text") for seg in segments)
    if not has_text:
        console.print("[yellow]Warning: No transcript text to analyze[/yellow]")
        return None

    console.print(f"[cyan]Analyzing transcript with {provider}...[/cyan]")

    prompt = assemble_prompt(segments, blocks, context=context)

    try:
        response_text = call_llm(prompt, provider=provider, model=model)
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]LLM error: {e}[/red]")
        return None

    # Strip markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    try:
        analysis = json.loads(response_text.strip())
        console.print("[green]Analysis complete[/green]")
        return analysis
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse LLM response: {e}[/red]")
        return None
