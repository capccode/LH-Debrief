"""Per-session metadata generation and output index management."""

import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


def generate_metadata(
    output_dir: Path,
    short_name: str,
    segments: list[dict],
    audio_path: Path,
    pipeline_config: dict,
) -> dict:
    """Generate metadata.json for a single session.

    Must be called AFTER all other output files are written so the
    output_files list is complete.
    """
    today = date.today().isoformat()
    session_id = f"{today}-{short_name}"

    # Speaker stats
    speaker_times: dict[str, float] = defaultdict(float)
    for seg in segments:
        speaker_times[seg["speaker"]] += seg["end"] - seg["start"]
    labels = sorted(speaker_times.keys())

    duration = max(seg["end"] for seg in segments) if segments else 0.0

    # Scan output directory for all files (including this metadata.json)
    output_files = sorted(f.name for f in output_dir.iterdir() if f.is_file())
    if "metadata.json" not in output_files:
        output_files.append("metadata.json")
        output_files.sort()

    metadata = {
        "id": session_id,
        "date": today,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "title": short_name.replace("-", " ").title(),
        "source": {
            "type": "audio",
            "file": audio_path.name,
            "duration_seconds": round(duration, 1),
            "language": pipeline_config.get("language"),
        },
        "speakers": {
            "count": len(labels),
            "labels": labels,
            "speaking_times": {s: round(t, 1) for s, t in sorted(speaker_times.items())},
        },
        "pipeline": {
            "profile": pipeline_config.get("profile"),
            "blocks_used": pipeline_config.get("blocks_used", []),
            "provider": pipeline_config.get("provider"),
            "model": pipeline_config.get("model"),
            "whisper_model": pipeline_config.get("whisper_model"),
            "context": pipeline_config.get("context"),
            "language": pipeline_config.get("language"),
            "translated": pipeline_config.get("translated", False),
        },
        "output_files": output_files,
        "classification": {
            "domains": [],
            "projects": [],
            "tags": [],
        },
    }

    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata


def rebuild_index(output_root: Path) -> None:
    """Scan all metadata.json files under output_root and build index.json."""
    sessions = []
    for meta_path in output_root.rglob("metadata.json"):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        session_dir = meta_path.parent
        sessions.append(
            {
                "id": meta["id"],
                "date": meta["date"],
                "title": meta["title"],
                "profile": meta.get("pipeline", {}).get("profile"),
                "speakers": meta.get("speakers", {}).get("count", 0),
                "duration_seconds": meta.get("source", {}).get("duration_seconds", 0),
                "path": str(session_dir.relative_to(output_root)) + "/",
            }
        )

    # Sort by date descending, then title ascending
    sessions.sort(key=lambda s: s["title"])
    sessions.sort(key=lambda s: s["date"], reverse=True)

    index = {
        "version": "1.0",
        "updated": datetime.now(timezone.utc).isoformat(),
        "sessions": sessions,
    }

    with open(output_root / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
