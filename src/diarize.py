"""
Speaker diarization, transcription, and AI analysis using Pyannote 3.1 + Whisper + Claude

Usage:
    python tools/meeting-intel/src/diarize.py input.wav --output output/
    python tools/meeting-intel/src/diarize.py input.wav -o output/ --model medium
    python tools/meeting-intel/src/diarize.py input.wav -o output/ --no-analyze
"""

# Suppress torchcodec warnings (we bypass it with torchaudio)
import warnings

warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*torchaudio.*load_with_torchcodec.*")

# NumPy 2.0 compatibility fix for pyannote.audio
import numpy as np

if not hasattr(np, "NaN"):
    np.NaN = np.nan
if not hasattr(np, "NAN"):
    np.NAN = np.nan

# PyTorch 2.6+ compatibility fix - allow pyannote model loading
import os
import torch

_original_torch_load = torch.load


def _patched_torch_load(*args, **kwargs):
    kwargs["weights_only"] = False  # Force override
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_torch_load

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict, cast


def truncate_name(name: str, max_length: int = 15) -> str:
    """
    Truncate filename to max_length chars, keeping it readable.

    - Removes common suffixes like 'Meeting Recording', timestamps
    - Converts to lowercase kebab-case
    - Truncates at word boundary if possible
    """
    # Remove common suffixes
    name = re.sub(r"[-_]?\d{8}[-_]?\d{6}", "", name)  # timestamps like 20251219_115727
    name = re.sub(r"[-_]?Meeting Recording", "", name, flags=re.IGNORECASE)
    name = name.strip(" -_")

    # Convert to kebab-case
    name = re.sub(r"[^\w\s-]", "", name)  # remove special chars
    name = re.sub(r"[\s_]+", "-", name)  # spaces/underscores to hyphens
    name = name.lower().strip("-")

    if len(name) <= max_length:
        return name

    # Truncate at word boundary
    truncated = name[:max_length]
    if "-" in truncated:
        truncated = truncated.rsplit("-", 1)[0]

    return truncated.strip("-")


import torchaudio
import whisper
from dotenv import load_dotenv
from pyannote.audio import Pipeline
from rich.console import Console
from rich.table import Table

from analyze import analyze_transcript, save_briefing


class WhisperSegment(TypedDict):
    start: float
    end: float
    text: str


# Load .env from workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

console = Console()


def convert_to_wav(audio_path: Path) -> Path:
    """
    Convert audio/video file to wav format using ffmpeg.
    Returns path to wav file (original if already wav, temp file otherwise).
    """
    if audio_path.suffix.lower() == ".wav":
        return audio_path

    # Check if ffmpeg is available
    if not shutil.which("ffmpeg"):
        console.print("[red]Error: ffmpeg not found. Install with 'brew install ffmpeg'[/red]")
        raise SystemExit(1)

    console.print(f"[cyan]Converting {audio_path.suffix} to wav...[/cyan]")

    # Create temp wav file
    wav_path = Path(tempfile.gettempdir()) / f"{audio_path.stem}_converted.wav"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",  # Overwrite output
                "-i",
                str(audio_path),
                "-vn",  # No video
                "-acodec",
                "pcm_s16le",  # PCM 16-bit
                "-ar",
                "16000",  # 16kHz sample rate
                "-ac",
                "1",  # Mono
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        console.print(f"[green]Converted to: {wav_path}[/green]")
        return wav_path
    except subprocess.CalledProcessError as e:
        console.print(f"[red]ffmpeg error: {e.stderr.decode()}[/red]")
        raise SystemExit(1)


def get_pipeline() -> Pipeline:
    """Load the Pyannote 3.1 pipeline."""
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        console.print("[red]Error: HF_TOKEN not found in .env file[/red]")
        console.print("1. Get token from: https://huggingface.co/settings/tokens")
        console.print(
            "2. Accept license at: https://huggingface.co/pyannote/speaker-diarization-3.1"
        )
        console.print("3. Create .env file with: HF_TOKEN=hf_your_token")
        raise SystemExit(1)

    # Set HF_TOKEN for huggingface_hub auto-detection
    os.environ["HF_TOKEN"] = hf_token

    console.print("[cyan]Loading Pyannote 3.1 pipeline...[/cyan]")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
    )

    if pipeline is None:
        console.print(
            "[red]Error: Failed to load pipeline. Check your token and model access.[/red]"
        )
        raise SystemExit(1)

    # Use best available device: CUDA → MPS → CPU
    if torch.cuda.is_available():
        device = torch.device("cuda")
        console.print(f"[green]Using CUDA GPU: {torch.cuda.get_device_name(0)}[/green]")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        console.print("[green]Using Apple Silicon GPU (MPS)[/green]")
    else:
        device = torch.device("cpu")
        console.print("[yellow]No GPU found, using CPU (this will be slower)[/yellow]")
    pipeline.to(device)

    return pipeline


def get_whisper_model(model_name: str = "base") -> whisper.Whisper:
    """Load Whisper model for transcription."""
    console.print(f"[cyan]Loading Whisper model ({model_name})...[/cyan]")

    # Use CUDA if available, otherwise CPU
    # Note: MPS has sparse tensor issues with Whisper large model, so we skip it
    if torch.cuda.is_available():
        device = "cuda"
        console.print("[green]Whisper using CUDA GPU[/green]")
    else:
        device = "cpu"
        console.print("[yellow]Whisper using CPU (MPS not supported for large models)[/yellow]")
    model = whisper.load_model(model_name, device=device)

    return model


def transcribe_segments(
    audio_path: Path,
    segments: list[dict],
    model: whisper.Whisper,
    language: str | None = None,
    translate: bool = False,
) -> list[dict]:
    """Transcribe each speaker segment using Whisper."""
    task = "translate" if translate else "transcribe"
    console.print(f"[cyan]{'Translating' if translate else 'Transcribing'} segments...[/cyan]")

    # Transcribe full audio first (more accurate than segment-by-segment)
    # task="translate" converts any language to English
    result = model.transcribe(
        str(audio_path),
        language=language,  # None = auto-detect source language
        task=task,
        word_timestamps=True,
    )

    whisper_segments = cast(list[WhisperSegment], result.get("segments", []))

    # Assign transcripts to speaker segments
    for seg in segments:
        seg["text"] = ""
        seg_start: float = seg["start"]
        seg_end: float = seg["end"]

        # Find overlapping whisper segments
        for ws in whisper_segments:
            ws_start: float = ws["start"]
            ws_end: float = ws["end"]

            # Check for overlap
            if ws_start < seg_end and ws_end > seg_start:
                seg["text"] += ws["text"].strip() + " "

        seg["text"] = seg["text"].strip()

    return segments


def diarize(audio_path: Path, num_speakers: int | None = None) -> tuple[list[dict], Path]:
    """
    Run speaker diarization on an audio file.

    Args:
        audio_path: Path to audio file (wav, mp3, etc.)
        num_speakers: Optional known number of speakers

    Returns:
        Tuple of (segments with speaker labels and timestamps, wav_path used for processing)
    """
    # Convert to wav if needed (pyannote's torchcodec has issues with other formats)
    wav_path = convert_to_wav(audio_path)

    pipeline = get_pipeline()

    console.print(f"[cyan]Processing: {wav_path}[/cyan]")

    # Load audio with torchaudio (bypasses broken torchcodec in pyannote)
    waveform, sample_rate = torchaudio.load(wav_path)
    audio_input = {"waveform": waveform, "sample_rate": sample_rate}

    # Run diarization
    if num_speakers:
        diarization = pipeline(audio_input, num_speakers=num_speakers)
    else:
        diarization = pipeline(audio_input)

    # Handle new DiarizeOutput wrapper (pyannote 3.1+)
    if hasattr(diarization, "speaker_diarization"):
        diarization = diarization.speaker_diarization

    # Convert to list of segments
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "speaker": speaker,
            }
        )

    return segments, wav_path


def display_results(segments: list[dict], show_text: bool = True) -> None:
    """Display diarization results in a table."""
    table = Table(title="Speaker Diarization Results", show_lines=True)
    table.add_column("Time", style="cyan", width=12)
    table.add_column("Speaker", style="magenta", width=12)
    if show_text:
        table.add_column("Text", style="white", max_width=80)

    for seg in segments:
        time_range = f"{seg['start']:.1f}s - {seg['end']:.1f}s"
        if show_text:
            text = seg.get("text", "")
            # Truncate for display
            display_text = text[:200] + "..." if len(text) > 200 else text
            table.add_row(time_range, seg["speaker"], display_text)
        else:
            table.add_row(time_range, seg["speaker"])

    console.print(table)

    # Speaker summary
    speakers: dict[str, float] = {}
    for seg in segments:
        speaker = seg["speaker"]
        duration = seg["end"] - seg["start"]
        speakers[speaker] = speakers.get(speaker, 0) + duration

    console.print("\n[bold]Speaker Summary:[/bold]")
    for speaker, total_time in sorted(speakers.items()):
        console.print(f"  {speaker}: {total_time:.1f}s ({total_time / 60:.1f}min)")


def main():
    parser = argparse.ArgumentParser(
        description="Speaker diarization, transcription, and AI analysis using Pyannote 3.1 + Whisper + Claude"
    )
    parser.add_argument("audio", type=Path, help="Path to audio file")
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
        help="Skip Claude AI analysis (default: analyze is ON)",
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
    args = parser.parse_args()

    if not args.audio.exists():
        console.print(f"[red]Error: File not found: {args.audio}[/red]")
        raise SystemExit(1)

    # Run diarization
    segments, wav_path = diarize(args.audio, num_speakers=args.speakers)

    # Transcribe if requested (use wav_path for compatibility)
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
        # Generate truncated name and create subfolder per meeting
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

        # Run Claude analysis if enabled and we have transcripts
        if not args.no_analyze and not args.no_transcribe:
            analysis = analyze_transcript(
                segments=segments,
                audio_name=args.audio.stem,
                domain_context=args.context,
            )
            if analysis:
                save_briefing(
                    output_dir=output_dir,
                    short_name=short_name,
                    segments=segments,
                    analysis=analysis,
                )


if __name__ == "__main__":
    main()
