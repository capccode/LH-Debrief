"""Whisper transcription and speaker segment alignment."""

from pathlib import Path
from typing import TypedDict, cast

import torch
import whisper
from rich.console import Console

console = Console()


class WhisperSegment(TypedDict):
    start: float
    end: float
    text: str


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
