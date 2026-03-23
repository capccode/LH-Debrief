"""Tests for briefing rendering."""

import json
from unittest.mock import patch

from render import render_briefing

MOCK_SEGMENTS = [
    {"start": 0.0, "end": 300.0, "speaker": "SPEAKER_00"},
    {"start": 300.0, "end": 600.0, "speaker": "SPEAKER_01"},
]


def _make_block(name, display_name):
    return {
        "name": name,
        "display_name": display_name,
        "description": f"Description for {name}",
        "prompt": f"Prompt for {name}",
        "json_example": f'"{name}": "example"',
    }


class TestRenderBriefing:
    def test_creates_both_files(self, tmp_path):
        blocks = [_make_block("summary", "Summary")]
        analysis = {"summary": "A test summary."}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        assert (tmp_path / "briefing_test.md").exists()
        assert (tmp_path / "analysis_test.json").exists()

    def test_string_value_renders_as_paragraph(self, tmp_path):
        blocks = [_make_block("summary", "Summary")]
        analysis = {"summary": "This is a paragraph."}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        content = (tmp_path / "briefing_test.md").read_text()
        assert "This is a paragraph." in content

    def test_list_of_strings_renders_as_bullets(self, tmp_path):
        blocks = [_make_block("items", "Items")]
        analysis = {"items": ["First", "Second", "Third"]}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        content = (tmp_path / "briefing_test.md").read_text()
        assert "- First" in content
        assert "- Second" in content
        assert "- Third" in content

    def test_list_of_dicts_renders_as_table(self, tmp_path):
        blocks = [_make_block("tasks", "Tasks")]
        analysis = {"tasks": [{"owner": "Alice", "task": "Review PR"}]}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        content = (tmp_path / "briefing_test.md").read_text()
        assert "| Owner | Task |" in content
        assert "| Alice | Review PR |" in content

    def test_missing_block_key_skipped_with_warning(self, tmp_path):
        blocks = [_make_block("missing_key", "Missing")]
        analysis = {}
        with patch("render.console") as mock_console:
            render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
            mock_console.print.assert_any_call(
                "[yellow]Warning: block 'missing_key' missing from analysis, skipping[/yellow]"
            )

    def test_profile_name_in_header(self, tmp_path):
        blocks = [_make_block("summary", "Summary")]
        analysis = {"summary": "text"}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks, profile_name="Business")
        content = (tmp_path / "briefing_test.md").read_text()
        assert "**Profile:** Business" in content

    def test_no_profile_name_in_header(self, tmp_path):
        blocks = [_make_block("summary", "Summary")]
        analysis = {"summary": "text"}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        content = (tmp_path / "briefing_test.md").read_text()
        assert "Profile:" not in content

    def test_analysis_json_is_valid(self, tmp_path):
        blocks = [_make_block("summary", "Summary")]
        analysis = {"summary": "text", "extra": [1, 2, 3]}
        render_briefing(tmp_path, "test", MOCK_SEGMENTS, analysis, blocks)
        with open(tmp_path / "analysis_test.json") as f:
            loaded = json.load(f)
        assert loaded == analysis
