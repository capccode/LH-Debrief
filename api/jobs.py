"""Job store and background pipeline execution."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from schemas import LogMessage


@dataclass
class JobRecord:
    """Mutable internal state for a pipeline job."""

    job_id: str
    status: str = "queued"
    stage: str | None = None
    progress: str | None = None
    files: list[str] = field(default_factory=list)
    error: str | None = None
    logs: list[LogMessage] = field(default_factory=list)
    output_dir: Path | None = None
    upload_dir: Path | None = None
    upload_filename: str = ""
    # Pipeline params
    profile: str | None = None
    blocks: list[str] | None = None
    add_blocks: list[str] | None = None
    provider: str = "anthropic"
    model: str | None = None
    context: str | None = None
    user_output_dir: str | None = None


class JobStore:
    """In-memory job store."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        upload_filename: str,
        upload_dir: str,
        *,
        profile: str | None = None,
        blocks: list[str] | None = None,
        add_blocks: list[str] | None = None,
        provider: str = "anthropic",
        model: str | None = None,
        context: str | None = None,
        output_dir: str | None = None,
    ) -> str:
        job_id = uuid.uuid4().hex
        job = JobRecord(
            job_id=job_id,
            upload_dir=Path(upload_dir),
            upload_filename=upload_filename,
            profile=profile,
            blocks=blocks,
            add_blocks=add_blocks,
            provider=provider,
            model=model,
            context=context,
            user_output_dir=output_dir,
        )
        async with self._lock:
            self._jobs[job_id] = job
        return job_id

    async def get_job(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_job(self, job_id: str, **kwargs: object) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in kwargs.items():
                    setattr(job, key, value)

    async def add_log(self, job_id: str, stage: str, message: str, status: str) -> None:
        log = LogMessage(
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            message=message,
            status=status,
        )
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.logs.append(log)

    async def get_logs(self, job_id: str, offset: int = 0) -> list[LogMessage]:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return []
            return list(job.logs[offset:])

    async def scan_output_files(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job and job.output_dir and job.output_dir.exists():
                job.files = sorted(f.name for f in job.output_dir.iterdir() if f.is_file())


async def run_pipeline(job_id: str, store: JobStore) -> None:
    """Async entry point: dispatches sync pipeline to thread pool."""
    await store.update_job(job_id, status="running")
    loop = asyncio.get_running_loop()

    def log(stage: str, message: str, status: str = "running") -> None:
        asyncio.run_coroutine_threadsafe(store.add_log(job_id, stage, message, status), loop)

    def update(**kwargs: object) -> None:
        asyncio.run_coroutine_threadsafe(store.update_job(job_id, **kwargs), loop)

    try:
        job = await store.get_job(job_id)
        assert job is not None
        await asyncio.to_thread(_run_pipeline_sync, job, log, update)
        await store.scan_output_files(job_id)
        await store.update_job(job_id, status="completed", stage="done")
        await store.add_log(job_id, "done", "Pipeline complete", "done")
    except Exception as e:
        await store.update_job(job_id, status="failed", error=str(e))
        await store.add_log(job_id, "pipeline", str(e), "error")


def _run_pipeline_sync(
    job: JobRecord,
    log: object,
    update: object,
) -> None:
    """Run the full pipeline in a worker thread. Lazy-imports src/ modules."""
    from audio import diarize, truncate_name
    from transcribe import get_whisper_model, transcribe_segments

    assert job.upload_dir is not None
    audio_path = job.upload_dir / job.upload_filename

    # Stage 1: Diarization
    log("diarize", "Starting diarization...", "running")  # type: ignore[operator]
    update(stage="diarizing", progress="Diarizing audio...")  # type: ignore[operator]
    segments, wav_path = diarize(audio_path)
    speaker_count = len({s["speaker"] for s in segments})
    log("diarize", f"Found {speaker_count} speakers, {len(segments)} segments", "done")  # type: ignore[operator]

    # Stage 2: Transcription
    log("transcribe", "Loading Whisper large model...", "running")  # type: ignore[operator]
    update(stage="transcribing", progress="Transcribing with Whisper large...")  # type: ignore[operator]
    whisper_model = get_whisper_model("large")
    segments = transcribe_segments(wav_path, segments, whisper_model)
    log("transcribe", f"Transcribed {len(segments)} segments", "done")  # type: ignore[operator]

    # Resolve output directory
    short_name = truncate_name(audio_path.stem)
    if job.user_output_dir:
        from datetime import date

        date_prefix = date.today().isoformat()
        output_dir = Path(job.user_output_dir) / date_prefix / short_name
    else:
        output_dir = job.upload_dir / "output" / short_name
    output_dir.mkdir(parents=True, exist_ok=True)
    job.output_dir = output_dir

    # Save base outputs (diarization JSON + transcript)
    diar_file = output_dir / "diarization.json"
    with open(diar_file, "w") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    transcript_file = output_dir / "transcript.txt"
    with open(transcript_file, "w", encoding="utf-8") as f:
        for seg in segments:
            text = seg.get("text", "")
            f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['speaker']}:\n")
            f.write(f"{text}\n\n")

    log("transcribe", "Saved diarization and transcript files", "done")  # type: ignore[operator]

    # Stage 3: Analysis (only if profile or blocks specified)
    if job.profile or job.blocks:
        from analyze import analyze_transcript
        from profiles import load_profile, resolve_blocks
        from render import render_briefing

        if job.profile:
            profile = load_profile(job.profile)
            blocks = resolve_blocks(profile, add_blocks=job.add_blocks)
            context = profile.get("context", "")
            if job.context:
                context = f"{context}\n\n{job.context}" if context else job.context
            profile_name = profile["name"]
        else:
            blocks = resolve_blocks(block_names=job.blocks)
            context = job.context
            profile_name = None

        log("analyze", f"Analyzing with {job.provider}...", "running")  # type: ignore[operator]
        update(stage="analyzing", progress=f"Analyzing with {job.provider}...")  # type: ignore[operator]
        analysis = analyze_transcript(
            segments=segments,
            blocks=blocks,
            provider=job.provider,
            model=job.model,
            context=context,
        )
        log("analyze", "Analysis complete", "done")  # type: ignore[operator]

        # Stage 4: Rendering
        if analysis:
            log("render", "Generating briefing...", "running")  # type: ignore[operator]
            update(stage="rendering", progress="Rendering briefing...")  # type: ignore[operator]
            render_briefing(
                output_dir=output_dir,
                short_name=short_name,
                segments=segments,
                analysis=analysis,
                blocks=blocks,
                profile_name=profile_name,
            )
            log("render", "Briefing saved", "done")  # type: ignore[operator]


async def save_upload(file: object) -> tuple[str, str]:
    """Save an uploaded file to a temp directory. Returns (filename, temp_dir)."""
    upload_dir = tempfile.mkdtemp(prefix="lh-debrief-")
    filename = getattr(file, "filename", "upload") or "upload"
    dest = Path(upload_dir) / filename
    content = await file.read()  # type: ignore[union-attr]
    with open(dest, "wb") as f:
        f.write(content)
    return filename, upload_dir
