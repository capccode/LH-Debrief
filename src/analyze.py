"""
Claude-powered meeting analysis module.

Extracts structured insights from meeting transcripts:
- Executive summary
- Decisions made
- Action items with owners
- Key concepts and terms
- Open questions
- Follow-up items
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TypedDict, cast

import anthropic
from rich.console import Console

console = Console()


class MeetingAnalysis(TypedDict):
    executive_summary: str
    decisions: list[str]
    action_items: list[dict[str, str]]
    key_concepts: list[dict[str, str]]
    open_questions: list[str]
    follow_ups: list[str]


def analyze_transcript(
    segments: list[dict],
    audio_name: str,
    domain_context: str | None = None,
) -> MeetingAnalysis | None:
    """
    Analyze transcript with Claude to extract structured insights.

    Args:
        segments: List of diarized segments with 'start', 'end', 'speaker', 'text'
        audio_name: Name of the audio file (for logging)
        domain_context: Optional domain-specific context to improve analysis

    Returns:
        MeetingAnalysis dict or None if analysis fails
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[yellow]Warning: ANTHROPIC_API_KEY not set, skipping analysis[/yellow]")
        return None

    console.print("[cyan]Analyzing transcript with Claude...[/cyan]")

    # Build transcript text
    transcript_text = ""
    for seg in segments:
        text = seg.get("text", "")
        if text:
            transcript_text += f"[{seg['start']:.1f}s] {seg['speaker']}: {text}\n"

    if not transcript_text.strip():
        console.print("[yellow]Warning: No transcript text to analyze[/yellow]")
        return None

    # Domain context for better understanding
    domain_prompt = ""
    if domain_context:
        domain_prompt = f"""
<domain_context>
{domain_context}
</domain_context>
"""

    prompt = f"""Analyze this meeting transcript and extract structured information.

{domain_prompt}
<transcript>
{transcript_text}
</transcript>

Provide your analysis as JSON with this exact structure:
{{
    "executive_summary": "2-3 sentence summary of the meeting's main points and outcomes",
    "decisions": ["Decision 1 that was made", "Decision 2 that was made"],
    "action_items": [
        {{"owner": "Person name or role", "action": "What they need to do", "due": "Due date if mentioned, otherwise 'TBD'"}}
    ],
    "key_concepts": [
        {{"term": "Technical term or acronym", "explanation": "What it means in context"}}
    ],
    "open_questions": ["Question that was raised but not answered"],
    "follow_ups": ["Topic that needs follow-up discussion"]
}}

Focus on:
- Being precise and accurate - only include what was actually discussed
- Capturing technical terms and acronyms specific to this domain
- Identifying action items with clear owners when possible
- Noting decisions vs. things still being discussed

Return ONLY the JSON, no other text."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text  # type: ignore

        # Clean up response if needed (remove markdown code blocks)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        analysis = json.loads(response_text.strip())
        console.print("[green]Analysis complete[/green]")
        return cast(MeetingAnalysis, analysis)

    except anthropic.APIError as e:
        console.print(f"[red]Claude API error: {e}[/red]")
        return None
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse Claude response: {e}[/red]")
        return None


def save_briefing(
    output_dir: Path,
    short_name: str,
    segments: list[dict],
    analysis: MeetingAnalysis,
) -> None:
    """
    Save a formatted briefing document and raw analysis JSON.

    Args:
        output_dir: Directory to save files
        short_name: Truncated name for output files (e.g., 'rsi-next-steps')
        segments: Original segments (for stats)
        analysis: The MeetingAnalysis from Claude
    """
    # Calculate meeting stats
    total_duration = max(seg["end"] for seg in segments) if segments else 0
    speakers = set(seg["speaker"] for seg in segments)

    briefing_file = output_dir / f"briefing_{short_name}.md"

    with open(briefing_file, "w", encoding="utf-8") as f:
        f.write(f"# Meeting Briefing: {short_name}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | ")
        f.write(f"**Duration:** {total_duration/60:.0f} min | ")
        f.write(f"**Speakers:** {len(speakers)}\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"{analysis['executive_summary']}\n\n")

        # Decisions
        if analysis.get("decisions"):
            f.write("## Decisions Made\n\n")
            for i, decision in enumerate(analysis["decisions"], 1):
                f.write(f"{i}. {decision}\n")
            f.write("\n")

        # Action Items
        if analysis.get("action_items"):
            f.write("## Action Items\n\n")
            f.write("| Owner | Action | Due |\n")
            f.write("|-------|--------|-----|\n")
            for item in analysis["action_items"]:
                owner = item.get("owner", "TBD")
                action = item.get("action", "")
                due = item.get("due", "TBD")
                f.write(f"| {owner} | {action} | {due} |\n")
            f.write("\n")

        # Key Concepts
        if analysis.get("key_concepts"):
            f.write("## Key Concepts & Terms\n\n")
            for concept in analysis["key_concepts"]:
                term = concept.get("term", "")
                explanation = concept.get("explanation", "")
                f.write(f"- **{term}**: {explanation}\n")
            f.write("\n")

        # Open Questions
        if analysis.get("open_questions"):
            f.write("## Open Questions\n\n")
            for q in analysis["open_questions"]:
                f.write(f"- {q}\n")
            f.write("\n")

        # Follow-ups
        if analysis.get("follow_ups"):
            f.write("## Follow-up Items\n\n")
            for item in analysis["follow_ups"]:
                f.write(f"- {item}\n")
            f.write("\n")

    console.print(f"[green]Saved briefing: {briefing_file}[/green]")

    # Also save raw analysis as JSON
    analysis_file = output_dir / f"analysis_{short_name}.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    console.print(f"[green]Saved analysis: {analysis_file}[/green]")
