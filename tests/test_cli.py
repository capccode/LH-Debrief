"""Tests for CLI argument parsing and validation."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    """Run diarize.py with given CLI arguments."""
    return subprocess.run(
        [sys.executable, "src/diarize.py", *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )


class TestListCommands:
    def test_list_profiles(self):
        result = run_cli("--list-profiles")
        assert result.returncode == 0
        assert "business" in result.stdout
        assert "therapy" in result.stdout

    def test_list_blocks(self):
        result = run_cli("--list-blocks")
        assert result.returncode == 0
        assert "session_summary" in result.stdout
        assert "action_items" in result.stdout


class TestArgValidation:
    def test_blocks_and_profile_mutually_exclusive(self):
        result = run_cli("fake.wav", "--blocks", "summary", "--profile", "business")
        assert result.returncode == 2
        assert "mutually exclusive" in result.stderr

    def test_add_block_requires_profile(self):
        result = run_cli("fake.wav", "--add-block", "todos")
        assert result.returncode == 2
        assert "--add-block requires --profile" in result.stderr

    def test_no_profile_or_blocks_requires_no_analyze(self):
        result = run_cli("fake.wav")
        assert result.returncode == 2
        assert "specify --profile or --blocks" in result.stderr
