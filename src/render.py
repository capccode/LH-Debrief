"""Generic JSON → markdown briefing renderer.

Renders analysis results using block display_names as section headings.
No hardcoded field names — the block list drives section order and content.
"""

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


def render_briefing(
    output_dir: Path,
    short_name: str,
    segments: list[dict],
    analysis: dict,
    blocks: list[dict],
    profile_name: str | None = None,
) -> None:
    """Save a formatted briefing document and raw analysis JSON.

    Args:
        output_dir: Directory to save files
        short_name: Truncated name for output files
        segments: Original segments (for stats)
        analysis: The parsed analysis dict from the LLM
        blocks: Ordered list of block dicts (drives section order)
        profile_name: Optional profile name for the header
    """
    total_duration = max(seg["end"] for seg in segments) if segments else 0
    speakers = set(seg["speaker"] for seg in segments)

    briefing_file = output_dir / "briefing.md"

    with open(briefing_file, "w", encoding="utf-8") as f:
        f.write(f"# Session Briefing: {short_name}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | ")
        f.write(f"**Duration:** {total_duration / 60:.0f} min | ")
        f.write(f"**Speakers:** {len(speakers)}")
        if profile_name:
            f.write(f" | **Profile:** {profile_name}")
        f.write("\n\n---\n\n")

        for block in blocks:
            name = block["name"]
            display = block["display_name"]

            if name not in analysis:
                console.print(
                    f"[yellow]Warning: block '{name}' missing from analysis, skipping[/yellow]"
                )
                continue

            value = analysis[name]
            f.write(f"## {display}\n\n")

            if isinstance(value, str):
                f.write(f"{value}\n\n")
            elif isinstance(value, list) and value:
                if isinstance(value[0], str):
                    for item in value:
                        f.write(f"- {item}\n")
                    f.write("\n")
                elif isinstance(value[0], dict):
                    headers = list(value[0].keys())
                    f.write(
                        "| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |\n"
                    )
                    f.write("|" + "|".join("---" for _ in headers) + "|\n")
                    for row in value:
                        f.write("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n")
                    f.write("\n")
            elif isinstance(value, list):
                # Empty list
                f.write("*(none)*\n\n")

    console.print(f"[green]Saved briefing: {briefing_file}[/green]")

    # Save raw analysis JSON
    analysis_file = output_dir / "analysis.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    console.print(f"[green]Saved analysis: {analysis_file}[/green]")
