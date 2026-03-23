"""Diarize, transcribe, and analyze audio with composable analysis profiles.

Usage:
    python src/diarize.py input.wav -o output/ --profile business
    python src/diarize.py input.wav -o output/ --blocks session_summary decisions
    python src/diarize.py input.wav -o output/ --no-analyze
    python src/diarize.py --list-profiles
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from analyze import analyze_transcript
from audio import diarize, display_results, truncate_name
from profiles import list_blocks, list_profiles, load_block, load_profile, resolve_blocks
from render import render_briefing
from transcribe import get_whisper_model, transcribe_segments

# Load .env from workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Diarize, transcribe, and analyze audio with composable analysis profiles"
    )
    parser.add_argument("audio", type=Path, nargs="?", help="Path to audio file")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--speakers", "-n", type=int, help="Known number of speakers")
    parser.add_argument(
        "--model",
        "-m",
        default="large",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper model size (default: large)",
    )
    parser.add_argument(
        "--no-transcribe",
        action="store_true",
        help="Skip transcription, only do diarization",
    )
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Skip AI analysis",
    )
    parser.add_argument(
        "--context",
        "-c",
        type=str,
        default=None,
        help="Domain context to improve analysis (e.g., 'RSI pharma regulatory meeting')",
    )
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate foreign language audio to English (instead of transcribing in original language)",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=None,
        help="Source language code (e.g., 'ja' for Japanese, 'es' for Spanish). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Analysis profile (e.g., business, therapy). Use --list-profiles to see available.",
    )
    parser.add_argument(
        "--add-block",
        type=str,
        action="append",
        default=None,
        help="Add extra block(s) to the profile (repeatable). Requires --profile.",
    )
    parser.add_argument(
        "--blocks",
        type=str,
        nargs="+",
        default=None,
        help="Use specific blocks directly (no profile). Mutually exclusive with --profile.",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "ollama"],
        default="anthropic",
        help="LLM provider for analysis (default: anthropic)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Override LLM model name (default depends on provider)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )
    parser.add_argument(
        "--list-blocks",
        action="store_true",
        help="List available blocks and exit",
    )
    args = parser.parse_args()

    # Early exits for listing
    if args.list_profiles:
        console.print("[bold]Available profiles:[/bold]")
        for name in list_profiles():
            profile = load_profile(name)
            console.print(f"  {name:<10}— {profile['description']}")
        sys.exit(0)

    if args.list_blocks:
        console.print("[bold]Available blocks:[/bold]")
        for name in list_blocks():
            block = load_block(name)
            console.print(f"  {name:<30}— {block['description']}")
        sys.exit(0)

    # audio is required when not listing
    if args.audio is None:
        parser.error("the following arguments are required: audio")

    # Validate analysis args (before file check so errors are immediate)
    if args.blocks and args.profile:
        parser.error("--blocks and --profile are mutually exclusive")

    if args.add_block and not args.profile:
        parser.error("--add-block requires --profile")

    if not args.no_analyze and not args.blocks and not args.profile:
        available = ", ".join(list_profiles())
        parser.error(
            f"specify --profile or --blocks for analysis, or use --no-analyze to skip.\n"
            f"  Available profiles: {available}\n"
            f"  Use --list-profiles or --list-blocks for details."
        )

    if not args.audio.exists():
        console.print(f"[red]Error: File not found: {args.audio}[/red]")
        raise SystemExit(1)

    # Run diarization
    segments, wav_path = diarize(args.audio, num_speakers=args.speakers)

    # Transcribe if requested
    if not args.no_transcribe:
        whisper_model = get_whisper_model(args.model)
        segments = transcribe_segments(
            wav_path,
            segments,
            whisper_model,
            language=args.language,
            translate=args.translate,
        )

    # Display results
    display_results(segments, show_text=not args.no_transcribe)

    # Save output
    if args.output:
        short_name = truncate_name(args.audio.stem)
        output_dir = args.output / short_name
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[dim]Output folder: {output_dir}[/dim]")

        # Save JSON
        output_file = output_dir / f"diarization_{short_name}.json"
        with open(output_file, "w") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]Saved JSON: {output_file}[/green]")

        # Save readable transcript
        transcript_file = output_dir / f"transcript_{short_name}.txt"
        with open(transcript_file, "w", encoding="utf-8") as f:
            for seg in segments:
                text = seg.get("text", "")
                f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['speaker']}:\n")
                f.write(f"{text}\n\n")
        console.print(f"[green]Saved transcript: {transcript_file}[/green]")

        # Analysis
        if not args.no_analyze and not args.no_transcribe:
            if args.profile:
                profile = load_profile(args.profile)
                blocks = resolve_blocks(profile, add_blocks=args.add_block)
                context = profile.get("context", "")
                if args.context:
                    context = f"{context}\n\n{args.context}" if context else args.context
                profile_name = profile["name"]
            else:
                blocks = resolve_blocks(block_names=args.blocks)
                context = args.context
                profile_name = None

            analysis = analyze_transcript(
                segments=segments,
                blocks=blocks,
                provider=args.provider,
                model=args.llm_model,
                context=context,
            )
            if analysis:
                render_briefing(
                    output_dir=output_dir,
                    short_name=short_name,
                    segments=segments,
                    analysis=analysis,
                    blocks=blocks,
                    profile_name=profile_name,
                )


if __name__ == "__main__":
    main()
