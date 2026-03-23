"""Audio conversion and speaker diarization using Pyannote 3.1."""

# Suppress torchcodec warnings (we bypass it with torchaudio)
import warnings
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*torchaudio.*load_with_torchcodec.*")

# NumPy 2.0 compatibility fix for pyannote.audio
import numpy as np
if not hasattr(np, 'NaN'):
    np.NaN = np.nan
if not hasattr(np, 'NAN'):
    np.NAN = np.nan

# PyTorch 2.6+ compatibility fix - allow pyannote model loading
import os
import torch
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False  # Force override
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import torchaudio
from pyannote.audio import Pipeline
from rich.console import Console
from rich.table import Table

console = Console()


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
    name = re.sub(r"[\s_]+", "-", name)   # spaces/underscores to hyphens
    name = name.lower().strip("-")

    if len(name) <= max_length:
        return name

    # Truncate at word boundary
    truncated = name[:max_length]
    if "-" in truncated:
        truncated = truncated.rsplit("-", 1)[0]

    return truncated.strip("-")


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
                "ffmpeg", "-y",  # Overwrite output
                "-i", str(audio_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono
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
        console.print("2. Accept license at: https://huggingface.co/pyannote/speaker-diarization-3.1")
        console.print("3. Create .env file with: HF_TOKEN=hf_your_token")
        raise SystemExit(1)

    # Set HF_TOKEN for huggingface_hub auto-detection
    os.environ["HF_TOKEN"] = hf_token

    console.print("[cyan]Loading Pyannote 3.1 pipeline...[/cyan]")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
    )

    if pipeline is None:
        console.print("[red]Error: Failed to load pipeline. Check your token and model access.[/red]")
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
        segments.append({
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
            "speaker": speaker,
        })

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
        console.print(f"  {speaker}: {total_time:.1f}s ({total_time/60:.1f}min)")
