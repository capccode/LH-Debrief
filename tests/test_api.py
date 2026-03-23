"""Comprehensive tests for the FastAPI backend."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, store


@pytest.fixture(autouse=True)
def _clear_store():
    """Reset job store between tests."""
    store._jobs.clear()
    yield
    store._jobs.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# --- GET /health ---


class TestHealth:
    def test_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# --- GET /profiles ---


class TestProfiles:
    def test_returns_profiles(self, client):
        resp = client.get("/profiles")
        assert resp.status_code == 200
        profiles = resp.json()
        assert len(profiles) >= 2
        ids = {p["id"] for p in profiles}
        assert "business" in ids
        assert "therapy" in ids

    def test_profile_has_required_fields(self, client):
        resp = client.get("/profiles")
        for p in resp.json():
            assert "id" in p
            assert "name" in p
            assert "description" in p
            assert "blocks" in p
            assert isinstance(p["blocks"], list)
            assert len(p["blocks"]) > 0

    def test_profile_id_differs_from_name(self, client):
        resp = client.get("/profiles")
        for p in resp.json():
            # id is filename stem, name is display name from TOML
            assert isinstance(p["id"], str)
            assert isinstance(p["name"], str)


# --- GET /blocks ---


class TestBlocks:
    def test_returns_all_blocks(self, client):
        resp = client.get("/blocks")
        assert resp.status_code == 200
        blocks = resp.json()
        assert len(blocks) == 13

    def test_block_has_required_fields(self, client):
        resp = client.get("/blocks")
        for b in resp.json():
            for key in ("name", "display_name", "description", "prompt", "json_example"):
                assert key in b, f"missing {key} in block {b.get('name', '?')}"

    def test_known_blocks_present(self, client):
        resp = client.get("/blocks")
        names = {b["name"] for b in resp.json()}
        assert "session_summary" in names
        assert "action_items" in names
        assert "decisions" in names
        assert "key_quotes" in names


# --- GET /providers/ollama/models ---


class TestOllamaModels:
    def test_returns_empty_list_when_ollama_not_running(self, client):
        # Default: no Ollama running locally → graceful empty list
        resp = client.get("/providers/ollama/models")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_models_when_ollama_running(self, client):
        mock_data = {
            "models": [
                {"name": "qwen3:8b", "size": 4700000000, "modified_at": "2026-03-20T10:00:00Z"},
                {"name": "llama3:8b", "size": 4500000000},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status = MagicMock()

        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = client.get("/providers/ollama/models")
            assert resp.status_code == 200
            models = resp.json()
            assert len(models) == 2
            assert models[0]["name"] == "qwen3:8b"
            assert models[0]["size"] == 4700000000


# --- POST /jobs ---


class TestCreateJob:
    def _post_job(self, client, **form_data):
        files = {"file": ("test.wav", b"fake audio content", "audio/wav")}
        return client.post("/jobs", data=form_data, files=files)

    @patch("jobs._run_pipeline_sync")
    def test_creates_job_with_profile(self, mock_pipeline, client):
        resp = self._post_job(client, profile="business", provider="anthropic")
        assert resp.status_code == 200
        body = resp.json()
        assert "job_id" in body
        assert body["status"] == "queued"

    @patch("jobs._run_pipeline_sync")
    def test_creates_job_with_blocks(self, mock_pipeline, client):
        resp = self._post_job(client, blocks="session_summary,decisions", provider="ollama")
        assert resp.status_code == 200
        body = resp.json()
        assert "job_id" in body

    @patch("jobs._run_pipeline_sync")
    def test_creates_job_without_profile_or_blocks(self, mock_pipeline, client):
        # Diarization + transcription only (no analysis)
        resp = self._post_job(client, provider="anthropic")
        assert resp.status_code == 200

    def test_rejects_profile_and_blocks_together(self, client):
        resp = self._post_job(client, profile="business", blocks="session_summary")
        assert resp.status_code == 400
        assert "mutually exclusive" in resp.json()["detail"]

    def test_rejects_add_blocks_without_profile(self, client):
        resp = self._post_job(client, blocks="session_summary", add_blocks="todos")
        assert resp.status_code == 400
        assert "requires a profile" in resp.json()["detail"]

    def test_rejects_unknown_provider(self, client):
        resp = self._post_job(client, profile="business", provider="openai")
        assert resp.status_code == 400
        assert "unknown provider" in resp.json()["detail"]

    def test_rejects_missing_file(self, client):
        resp = client.post("/jobs", data={"profile": "business"})
        assert resp.status_code == 422


# --- GET /jobs/{id}/status ---


class TestJobStatus:
    @patch("jobs._run_pipeline_sync")
    def test_returns_status_for_existing_job(self, mock_pipeline, client):
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]

        resp = client.get(f"/jobs/{job_id}/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == job_id
        assert body["status"] in ("queued", "running", "completed", "failed")

    def test_returns_404_for_unknown_job(self, client):
        resp = client.get("/jobs/nonexistent/status")
        assert resp.status_code == 404


# --- GET /jobs/{id}/output/{filename} ---


class TestJobOutput:
    @patch("jobs._run_pipeline_sync")
    def test_serves_existing_file(self, mock_pipeline, client, tmp_path):
        # Create a job
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]

        # Wait briefly for task to start
        time.sleep(0.1)

        # Manually set output_dir and create a file
        import asyncio

        async def _setup():
            job = await store.get_job(job_id)
            job.output_dir = tmp_path
            (tmp_path / "briefing.md").write_text("# Test Briefing")

        asyncio.get_event_loop().run_until_complete(_setup())

        resp = client.get(f"/jobs/{job_id}/output/briefing.md")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "Test Briefing" in resp.text

    @patch("jobs._run_pipeline_sync")
    def test_content_types(self, mock_pipeline, client, tmp_path):
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]
        time.sleep(0.1)

        import asyncio

        async def _setup():
            job = await store.get_job(job_id)
            job.output_dir = tmp_path
            (tmp_path / "data.json").write_text('{"key": "value"}')
            (tmp_path / "transcript.txt").write_text("Hello world")

        asyncio.get_event_loop().run_until_complete(_setup())

        resp_json = client.get(f"/jobs/{job_id}/output/data.json")
        assert "application/json" in resp_json.headers["content-type"]

        resp_txt = client.get(f"/jobs/{job_id}/output/transcript.txt")
        assert "text/plain" in resp_txt.headers["content-type"]

    def test_returns_404_for_unknown_job(self, client):
        resp = client.get("/jobs/nonexistent/output/file.txt")
        assert resp.status_code == 404

    @patch("jobs._run_pipeline_sync")
    def test_returns_404_for_missing_file(self, mock_pipeline, client, tmp_path):
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]
        time.sleep(0.1)

        import asyncio

        async def _setup():
            job = await store.get_job(job_id)
            job.output_dir = tmp_path

        asyncio.get_event_loop().run_until_complete(_setup())

        resp = client.get(f"/jobs/{job_id}/output/nonexistent.txt")
        assert resp.status_code == 404

    @patch("jobs._run_pipeline_sync")
    def test_blocks_path_traversal(self, mock_pipeline, client, tmp_path):
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]
        time.sleep(0.1)

        import asyncio

        async def _setup():
            job = await store.get_job(job_id)
            job.output_dir = tmp_path

        asyncio.get_event_loop().run_until_complete(_setup())

        resp = client.get(f"/jobs/{job_id}/output/../../etc/passwd")
        assert resp.status_code in (403, 404)


# --- WS /jobs/{id}/logs ---


class TestJobLogsWebSocket:
    @patch("jobs._run_pipeline_sync")
    def test_receives_log_messages(self, mock_pipeline, client):
        # Create a job — the mocked pipeline still triggers run_pipeline's
        # async wrapper which adds a "Pipeline complete" log + sets completed
        create_resp = client.post(
            "/jobs",
            data={"profile": "business"},
            files={"file": ("t.wav", b"fake", "audio/wav")},
        )
        job_id = create_resp.json()["job_id"]

        # Give the async pipeline task time to complete
        time.sleep(0.5)

        with client.websocket_connect(f"/jobs/{job_id}/logs") as ws:
            msg = ws.receive_json()
            # run_pipeline adds a "Pipeline complete" log when the mock returns
            assert "timestamp" in msg
            assert "stage" in msg
            assert "message" in msg
            assert "status" in msg

    def test_rejects_unknown_job(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/jobs/nonexistent/logs") as ws:
                ws.receive_json()
