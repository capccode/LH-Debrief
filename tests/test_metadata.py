"""Tests for per-session metadata generation and index management."""

import json
from unittest.mock import patch

from metadata import generate_metadata, rebuild_index

MOCK_SEGMENTS = [
    {"start": 0.0, "end": 30.0, "speaker": "Speaker 0", "text": "Hello"},
    {"start": 30.0, "end": 60.0, "speaker": "Speaker 1", "text": "Hi there"},
    {"start": 60.0, "end": 120.0, "speaker": "Speaker 0", "text": "Let's discuss"},
]

MOCK_PIPELINE_CONFIG = {
    "profile": "business",
    "blocks_used": ["session_summary", "decisions"],
    "provider": "anthropic",
    "model": "claude-opus-4-5-20251101",
    "whisper_model": "large",
    "context": "Q3 planning",
    "language": None,
    "translated": False,
}


class TestGenerateMetadata:
    def test_creates_metadata_file(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        generate_metadata(tmp_path, "test-meeting", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert (tmp_path / "metadata.json").exists()

    def test_returns_dict_with_correct_structure(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(
            tmp_path, "test-meeting", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG
        )
        for key in (
            "id",
            "date",
            "timestamp",
            "title",
            "source",
            "speakers",
            "pipeline",
            "output_files",
            "classification",
        ):
            assert key in meta

    def test_id_format(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        with patch("metadata.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-03-23"
            meta = generate_metadata(
                tmp_path, "test-meeting", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG
            )
        assert meta["id"] == "2026-03-23-test-meeting"

    def test_title_from_short_name(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(
            tmp_path, "q3-planning-call", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG
        )
        assert meta["title"] == "Q3 Planning Call"

    def test_source_file_matches_audio(self, tmp_path):
        audio = tmp_path / "my-recording.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert meta["source"]["file"] == "my-recording.mp4"

    def test_source_duration_from_segments(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert meta["source"]["duration_seconds"] == 120.0

    def test_speakers_count(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert meta["speakers"]["count"] == 2

    def test_speakers_labels(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert meta["speakers"]["labels"] == ["Speaker 0", "Speaker 1"]

    def test_speaking_times(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        times = meta["speakers"]["speaking_times"]
        assert times["Speaker 0"] == 90.0  # 30 + 60
        assert times["Speaker 1"] == 30.0

    def test_output_files_lists_directory(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        (tmp_path / "briefing.md").write_text("# Briefing")
        (tmp_path / "analysis.json").write_text("{}")
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert "metadata.json" in meta["output_files"]
        assert "briefing.md" in meta["output_files"]
        assert "analysis.json" in meta["output_files"]

    def test_classification_empty(self, tmp_path):
        audio = tmp_path / "meeting.mp4"
        audio.touch()
        meta = generate_metadata(tmp_path, "test", MOCK_SEGMENTS, audio, MOCK_PIPELINE_CONFIG)
        assert meta["classification"] == {"domains": [], "projects": [], "tags": []}


class TestRebuildIndex:
    def test_creates_index_file(self, tmp_path):
        # Create a session with metadata
        session_dir = tmp_path / "2026-03-23" / "test-meeting"
        session_dir.mkdir(parents=True)
        meta = {
            "id": "2026-03-23-test",
            "date": "2026-03-23",
            "title": "Test",
            "pipeline": {"profile": "business"},
            "speakers": {"count": 2},
            "source": {"duration_seconds": 120.0},
        }
        (session_dir / "metadata.json").write_text(json.dumps(meta))
        rebuild_index(tmp_path)
        assert (tmp_path / "index.json").exists()

    def test_index_structure(self, tmp_path):
        session_dir = tmp_path / "2026-03-23" / "test"
        session_dir.mkdir(parents=True)
        meta = {
            "id": "2026-03-23-test",
            "date": "2026-03-23",
            "title": "Test",
            "pipeline": {"profile": "business"},
            "speakers": {"count": 2},
            "source": {"duration_seconds": 120.0},
        }
        (session_dir / "metadata.json").write_text(json.dumps(meta))
        rebuild_index(tmp_path)
        with open(tmp_path / "index.json") as f:
            index = json.load(f)
        assert "version" in index
        assert "updated" in index
        assert "sessions" in index
        assert index["version"] == "1.0"

    def test_sessions_from_metadata(self, tmp_path):
        session_dir = tmp_path / "2026-03-23" / "meeting"
        session_dir.mkdir(parents=True)
        meta = {
            "id": "2026-03-23-meeting",
            "date": "2026-03-23",
            "title": "Meeting",
            "pipeline": {"profile": "business"},
            "speakers": {"count": 3},
            "source": {"duration_seconds": 300.0},
        }
        (session_dir / "metadata.json").write_text(json.dumps(meta))
        rebuild_index(tmp_path)
        with open(tmp_path / "index.json") as f:
            index = json.load(f)
        assert len(index["sessions"]) == 1
        s = index["sessions"][0]
        assert s["id"] == "2026-03-23-meeting"
        assert s["title"] == "Meeting"
        assert s["speakers"] == 3
        assert s["duration_seconds"] == 300.0

    def test_empty_directory(self, tmp_path):
        rebuild_index(tmp_path)
        with open(tmp_path / "index.json") as f:
            index = json.load(f)
        assert index["sessions"] == []

    def test_multiple_sessions(self, tmp_path):
        for name in ("alpha", "beta"):
            d = tmp_path / "2026-03-23" / name
            d.mkdir(parents=True)
            meta = {
                "id": f"2026-03-23-{name}",
                "date": "2026-03-23",
                "title": name.title(),
                "pipeline": {"profile": "business"},
                "speakers": {"count": 2},
                "source": {"duration_seconds": 60.0},
            }
            (d / "metadata.json").write_text(json.dumps(meta))
        rebuild_index(tmp_path)
        with open(tmp_path / "index.json") as f:
            index = json.load(f)
        assert len(index["sessions"]) == 2

    def test_sessions_sorted_by_date_desc(self, tmp_path):
        for dt, name in [("2026-03-21", "old"), ("2026-03-23", "new"), ("2026-03-22", "mid")]:
            d = tmp_path / dt / name
            d.mkdir(parents=True)
            meta = {
                "id": f"{dt}-{name}",
                "date": dt,
                "title": name.title(),
                "pipeline": {"profile": "business"},
                "speakers": {"count": 1},
                "source": {"duration_seconds": 60.0},
            }
            (d / "metadata.json").write_text(json.dumps(meta))
        rebuild_index(tmp_path)
        with open(tmp_path / "index.json") as f:
            index = json.load(f)
        dates = [s["date"] for s in index["sessions"]]
        assert dates == ["2026-03-23", "2026-03-22", "2026-03-21"]
